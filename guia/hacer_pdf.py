"""Arma guia/GUIA_SIMULACION.pdf a partir de casos.py (corre casos.py primero)."""
import os, json
import matplotlib
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image, Table,
                                TableStyle, PageBreak, KeepTogether)

AQUI = os.path.dirname(os.path.abspath(__file__)); IMG = os.path.join(AQUI, "img")
fd = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
pdfmetrics.registerFont(TTFont("DV", f"{fd}/DejaVuSans.ttf")); pdfmetrics.registerFont(TTFont("DVB", f"{fd}/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DVI", f"{fd}/DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DVB", italic="DVI", boldItalic="DVB")
C = json.load(open(f"{AQUI}/casos.json"))
for _k in C: C[_k]['impacto_m_s'] = f"{C[_k]['impacto_m_s']:.1f}".replace('.', ',')

INK, INK2 = colors.HexColor("#1b2328"), colors.HexColor("#52514e")
AZUL, VERDE, ROJO, AMAR = (colors.HexColor(x) for x in ("#1f5f8b", "#0a7d3b", "#b3261e", "#9a6400"))
BG_V, BG_R, BG_A, BG_N = (colors.HexColor(x) for x in ("#e5f3ea", "#fbe9e7", "#fdf3dc", "#eef2f4"))
st = dict(
  body=ParagraphStyle("body", fontName="DV", fontSize=9.6, leading=14.2, textColor=INK, spaceAfter=5),
  small=ParagraphStyle("small", fontName="DV", fontSize=8.3, leading=11.5, textColor=INK2),
  h1=ParagraphStyle("h1", fontName="DVB", fontSize=17, leading=21, textColor=INK, spaceBefore=2, spaceAfter=8),
  h2=ParagraphStyle("h2", fontName="DVB", fontSize=11.5, leading=15, textColor=AZUL, spaceBefore=8, spaceAfter=4),
  title=ParagraphStyle("title", fontName="DVB", fontSize=26, leading=31, textColor=INK, spaceAfter=8),
  sub=ParagraphStyle("sub", fontName="DV", fontSize=12.5, leading=17, textColor=INK2, spaceAfter=14),
  cap=ParagraphStyle("cap", fontName="DVI", fontSize=8.2, leading=11, textColor=INK2, spaceAfter=6),
  cell=ParagraphStyle("cell", fontName="DV", fontSize=8.8, leading=12, textColor=INK),
  cellb=ParagraphStyle("cellb", fontName="DVB", fontSize=8.8, leading=12, textColor=INK),
)
def P(t, s="body"): return Paragraph(t, st[s])
def caja(txt, fondo, borde, titulo=None):
    cont = [P(f"<b>{titulo}</b>", "body")] if titulo else []
    cont.append(P(txt, "body"))
    t = Table([[cont]], colWidths=[17 * cm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), fondo), ("LINEBEFORE", (0, 0), (0, -1), 3, borde),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t
def tabla(filas, anchos, cab=True):
    data = [[P(c, "cellb" if (cab and i == 0) else "cell") for c in f] for i, f in enumerate(filas)]
    t = Table(data, colWidths=[a * cm for a in anchos], repeatRows=1 if cab else 0)
    est = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#d5dce0")),
           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    if cab: est.append(("BACKGROUND", (0, 0), (-1, 0), BG_N))
    t.setStyle(TableStyle(est)); return t
def img(nombre, ancho=17):
    from reportlab.lib.utils import ImageReader
    w, h = ImageReader(f"{IMG}/{nombre}").getSize()
    return Image(f"{IMG}/{nombre}", width=ancho * cm, height=ancho * cm * h / w)

def pie(c, d):
    c.saveState(); c.setFont("DV", 7.5); c.setFillColor(INK2)
    c.drawString(2 * cm, 1.2 * cm, "Guía de la simulación · exoasistente de rodilla · prototipo virtual (MuJoCo)")
    c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"{d.page}"); c.restoreState()

doc = BaseDocTemplate(os.path.join(AQUI, "GUIA_SIMULACION.pdf"), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                      topMargin=1.8 * cm, bottomMargin=1.9 * cm, title="Guía para entender la simulación del exoasistente",
                      author="Proyecto exoasistente")
doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(2 * cm, 1.9 * cm, 17 * cm, A4[1] - 3.7 * cm, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=pie)])
S = []

# ---------------------------------------------------------------- portada
S += [Spacer(1, 1.2 * cm), P("Guía para entender la simulación del exoasistente de rodilla", "title"),
      P("Un caso donde todo sale bien y tres donde todo sale mal, con la misma persona y las mismas gráficas.", "sub"),
      caja("Un muñeco de computadora se levanta de una silla. Sus piernas están un poco débiles y le falta algo de fuerza. "
           "Un exoesqueleto en la rodilla le da el empujón que le falta. La simulación repite esa escena muchas veces, "
           "cambiando una cosa a la vez (cuándo ayuda el exo, cómo falla, qué motor lleva), para ver cuándo la persona "
           "termina de pie y cuándo se cae de nuevo a la silla.", BG_N, AZUL, "En una frase"),
      Spacer(1, 0.4 * cm), P("Cómo usar esta guía", "h2"),
      P("Primero lee el caso A, que es el modelo de cómo se ve todo cuando funciona. Después los casos B1, B2 y B3, que son "
        "tres formas distintas de que salga mal. Cada caso tiene fotos, una gráfica, qué pasó, y en qué parte de las gráficas "
        "grandes del análisis (las 5 imágenes que ya viste) se ve reflejado. Al final hay un cuadro para reconocer "
        "un caso bueno de uno malo de un vistazo."),
      P("El personaje", "h2"),
      tabla([["Dato", "Valor", "Qué significa"],
             ["Persona", "75 kg, 1,70 m", "Maniquí de 3 segmentos (pierna, muslo, tronco); las dos piernas se cuentan como una sola"],
             ["Movimiento", "Sentada a de pie en 2,6 s", "Despega del asiento a los 0,8 s, después estira la rodilla hasta 0°"],
             ["Fuerza que necesita", "136 N·m", "Es la fuerza mínima de rodilla con la que se levantaría sola en este modelo"],
             ["Fuerza que tiene", "116 N·m (85%)", "Le faltan unos 20 N·m. En los casos B3 tiene 90% (122 N·m)"],
             ["Exo", "25 N·m máximo, en una rodilla", "Es lo que puede empujar el motor. Con eso cubre lo que falta"]],
            [3.6, 4.3, 9.1])]
S += [PageBreak()]

# ---------------------------------------------------------------- vocabulario
S += [P("Antes de empezar: el vocabulario", "h1"),
      tabla([["Palabra", "Qué es", "Para qué sirve saberlo"],
             ["N·m (newton metro)", "Cuánta fuerza de giro hace la rodilla. Como cuando aprietas una tuerca con una llave", "Más N·m es más fuerza. 116 N·m es lo que aguanta la persona, 25 N·m es lo que da el exo"],
             ["Grados de rodilla (°)", "95° es la rodilla doblada como sentada. 0° es la pierna recta, de pie", "La gráfica de la izquierda de cada caso: la línea tiene que bajar hasta cero"],
             ["m/s", "Velocidad con la que la pelvis toca la silla al caer", "0,3 es sentarse normal. Más de 0,5 ya es un golpe. 1,5 es un desplome"],
             ["Asistencia", "El empujón que da el exo", "Tiene que llegar a tiempo, ni antes ni tarde"],
             ["Límite de corriente", "Un tope en la electrónica: el motor no puede empujar más de cierto valor aunque el programa se lo pida", "Es lo que evita el caso B2"],
             ["Watchdog", "Un perro guardián: si el programa se cuelga, corta la energía al motor", "Cuanto más rápido corte, menos daño"],
             ["Reductora (N:1)", "Engranes que multiplican la fuerza del motor. 170:1 da mucha fuerza pero es dura de mover a mano", "Por eso el diseño DC 170:1 falla peor que los BLDC"]],
            [3.4, 7.1, 6.5]),
      Spacer(1, 0.3 * cm), P("Los colores de las gráficas grandes", "h2"),
      tabla([["Color", "Significa"],
             ["Verde con palomita ✓", "La persona terminó de pie"],
             ["Amarillo con número", "Se volvió a sentar, pero suave (menos de 0,5 m/s)"],
             ["Rojo con número", "Se dejó caer fuerte a la silla (0,5 m/s o más). Es el número de la velocidad"],
             ["Naranja \"a medio\"", "Se quedó a medio camino, ni de pie ni sentada"]], [4.5, 12.5]),
      Spacer(1, 0.3 * cm),
      caja("Las gráficas de esta guía tienen dos partes. <b>Izquierda:</b> la rodilla, que debe bajar de 95° a 0° siguiendo la línea punteada. "
           "<b>Derecha:</b> quién pone la fuerza. La línea gris es la persona (con su tope de fuerza), la azul es el exo.", BG_N, AZUL, "Cómo leer las gráficas de cada caso")]
S += [PageBreak()]

# ---------------------------------------------------------------- caso A
a = C["A"]
S += [P("Caso A: todo sale bien", "h1"),
      caja("La persona tiene 85% de la fuerza necesaria. El exo lleva un motor BLDC cuasi directo 9:1 y empieza a ayudar a los 0,4 s, cuando "
           "la persona empieza a inclinar el tronco. No hay ninguna falla.", BG_V, VERDE, "El escenario"),
      Spacer(1, 0.25 * cm), img("A_fotos.png"), P("Fotogramas del caso A: sentada, inclinándose, despegando, estirando la rodilla y de pie.", "cap"),
      img("A_graf.png"),
      P("Segundo a segundo", "h2"),
      tabla([["Tiempo", "Qué pasa"],
             ["0,0 s", "Sentada, rodilla a 95°."],
             ["0,4 s", "Empieza a inclinar el tronco. El exo detecta el movimiento y entra con 25 N·m."],
             ["0,8 s", "Despega del asiento. Este es el momento más difícil: toda la fuerza de la persona (116 N·m) más la del exo."],
             ["1,3 s", "La rodilla ya baja rápido. La persona empieza a necesitar menos fuerza, la línea gris baja."],
             ["2,2 s", "La rodilla está casi recta (menos de 5°). Está de pie."],
             ["2,1 s", "El exo ya casi no empuja: se apaga solo porque ya no hace falta."]], [2.2, 14.8]),
      P("Cómo se ve un caso bueno", "h2"),
      P("<b>1.</b> La línea gruesa de la izquierda va pegada a la punteada y llega a cero. "
        "<b>2.</b> La línea gris de la derecha toca su tope solo en el despegue y luego baja. "
        "<b>3.</b> El exo entra antes del despegue y sale solo. "
        "<b>4.</b> Nadie toca la silla: no hay línea roja."),
      caja("Gráfica 1: la línea verde llega a 0°. Gráfica 2: fila 85%, columna 0,4 s, verde con palomita. Gráfica 3, 4 y 5: no aplican, "
           "porque en este caso no hay fallas.", BG_N, AZUL, "Dónde se ve en las gráficas grandes")]
S += [PageBreak()]

def caso(k, quien, que_paso, por_que, donde, evita, color=BG_R):
    c = C[k]
    return [P(f"Caso {k}: {c['titulo'].lower()}", "h1"),
            caja(que_paso, color, ROJO, "Qué pasó"), Spacer(1, 0.25 * cm),
            img(f"{k}_fotos.png"), P(f"Fotogramas del caso {k}. El último es el momento en que la persona toca la silla.", "cap"),
            img(f"{k}_graf.png"),
            P("Por qué salió mal", "h2"), P(por_que),
            caja(donde, BG_N, AZUL, "Dónde se ve en las gráficas grandes"), Spacer(1, 0.2 * cm),
            caja(evita, BG_V, VERDE, "Cómo se evita"), PageBreak()]

S += caso("B1", "", "Igual que el caso A, pero a los 1,3 s el exo se apaga (por ejemplo, se acaba la batería o se desconecta un cable). "
          "Esta vez el diseño es el DC con reductora 170:1. La persona sigue con su 85% de fuerza.",
          "Sin los 25 N·m del exo, a la persona le faltan unos 20 N·m y no le alcanza para terminar de estirar la rodilla. "
          "Además, la reductora 170:1 es dura de mover: aun apagada, le pone resistencia (unos 5 N·m de fricción). Como el exo no se "
          "puede \"soltar\", la persona pelea contra el propio dispositivo. La rodilla se atora entre 40° y 70°, y a los 2,5 s se desploma en la silla "
          f"a {C['B1']['impacto_m_s']} m/s. En la gráfica de la derecha la línea gris está pegada a su tope: no tiene más fuerza que dar.",
          "Gráfica 3, fila \"DC 12 V + 170:1 · libre (sin energía)\", columna 1,3 s: rojo con 1,6. "
          "Mira la fila \"BLDC cuasi directo 9:1 · libre\" en la misma columna: verde. El mismo apagón termina bien, "
          "porque ese motor casi no ofrece resistencia cuando está apagado.",
          "Usar un motor y una reductora que se muevan fácil cuando están apagados (BLDC de reducción baja), para que una falla de energía deje libre la pierna. "
          "Si además se pone un diodo que frene solo la flexión, la persona se sienta suave sin que el exo se oponga a levantarse.")

S += caso("B2", "", "Igual que el caso A, pero a los 1,7 s falla el programa del exo: el motor empuja con toda su fuerza en el sentido equivocado, "
          "doblando la rodilla, y nada limita su fuerza. Pasan 0,2 s hasta que un watchdog corta la energía. El diseño es un BLDC con reductora 36:1.",
          "Sin un límite de corriente, ese motor puede dar unos 115 N·m, casi la fuerza total de la persona, pero en su contra. Durante 0,2 s la rodilla "
          "se dobla a la fuerza. La persona alcanza a levantarse (la rodilla vuelve a menos de 8° hacia los 2,3 s), pero queda desequilibrada y a los 3,6 s se "
          f"desploma hacia atrás a {C['B2']['impacto_m_s']} m/s. <b>Ojo:</b> el muñeco no tiene reflejo de equilibrio; una persona real "
          "quizá daría un paso o se agarraría. Lo importante es que 0,2 s de un empujón de 115 N·m es una fuerza enorme para lo que la persona puede resistir.",
          "Gráfica 5, fila \"BLDC + 36:1 · sin límite (115 N·m)\", columna 200 ms: rojo con 1,5. "
          "La fila de abajo, \"límite 25 N·m por hardware\", es verde en todas las columnas: con el tope puesto, el mismo fallo no hace nada.",
          "Poner un límite de corriente en el driver del motor, por hardware (no en el programa), para que el motor nunca pueda dar más de 25 N·m. "
          "Y un watchdog externo que corte la energía en 50 a 100 ms.")

S += caso("B3", "", "Aquí no hay ninguna falla. La persona tiene 90% de fuerza (un poco más que antes) y el exo funciona perfecto, pero empieza a ayudar "
          "a los 0,7 s en lugar de a los 0,4 s. El despegue es a los 0,8 s.",
          "Con 90% de fuerza la persona está justo en el límite. En la gráfica de la derecha, la línea gris está pegada a su tope desde el principio: "
          "ya da todo lo que tiene. Mientras el exo no ayuda, la rodilla se va quedando atrás de la trayectoria (a 1,0 s está más doblada de lo que debería). "
          "Cuando el exo entra ya va retrasada, y 25 N·m no alcanzan para recuperar ese atraso: la rodilla se atora a los 60° y la persona se cae de nuevo a la silla "
          f"a {C['B3']['impacto_m_s']} m/s. Sin exo esta misma persona se habría vuelto a sentar suavemente, así que llegar tarde con la ayuda es peor que no tener ayuda.",
          "Gráfica 2, fila 90%, columna 0,7 s: rojo con 1,4. Las columnas de 0,1 a 0,6 s de esa misma fila son verdes. "
          "Una diferencia de 0,1 s decide entre pararse y caerse.",
          "Que el exo detecte la intención de levantarse lo más pronto posible, a más tardar 0,5 s después de que la persona empieza a inclinar el tronco. "
          "Por eso el sensor del torso (IMU) tiene que estar en el MVP.")

# ---------------------------------------------------------------- resumen
S += [P("Resumen: cómo reconocer un caso bueno de uno malo", "h1"),
      tabla([["", "Caso bueno", "Caso malo"],
             ["Rodilla (izquierda)", "La línea sigue la punteada y llega a 0°", "Se separa de la punteada y se queda arriba de 40°, o vuelve a subir"],
             ["Persona (derecha, gris)", "Toca su tope un momento y luego baja", "Se queda pegada al tope: ya no tiene más fuerza"],
             ["Exo (derecha, azul)", "Entra antes del despegue y se apaga solo", "Llega tarde, se corta a media subida, o empuja para el lado contrario"],
             ["Silla", "Nadie la toca después del despegue", "Línea roja: la persona cae con un número. Más de 0,5 m/s ya es golpe"],
             ["Mapa de color", "Verde con palomita", "Rojo, con número de velocidad"]],
            [3.7, 6.3, 7.0]),
      Spacer(1, 0.35 * cm), P("Lo que enseñan los cuatro casos juntos", "h2"),
      tabla([["Caso", "Lección"],
             ["A", "25 N·m bastan para cubrir un 15% de déficit de fuerza si llegan a tiempo"],
             ["B1", "El diseño importa: un motor duro de mover convierte un apagón en un accidente. Uno suave lo deja pasar"],
             ["B2", "Un límite de fuerza por hardware es la protección más barata y más efectiva contra un fallo de programa"],
             ["B3", "La rapidez de detección es un requisito de seguridad: llegar tarde es peor que no ayudar"]], [1.8, 15.2]),
      Spacer(1, 0.35 * cm), P("Qué no significan estos casos", "h2"),
      P("Son una simulación en 2D con un muñeco, no una persona ni un dispositivo real. Los motores son valores representativos, no de catálogo, "
        "y el exo todavía no incluye el resorte en serie ni su peso. Cosas como el retardo de reacción de la persona (150 ms) o el umbral de 0,5 m/s son "
        "supuestos míos. Sirven para comparar diseños entre sí y entender qué importa, no para dar cifras de seguridad."),
      Spacer(1, 0.2 * cm),
      P("Todo el código y las 5 gráficas grandes están en github.com/CesarN27/exoasistente-sim. Para ver los casos en movimiento: <font name='DVB'>python ver.py</font>.", "small")]
doc.build(S)
print("PDF listo")
