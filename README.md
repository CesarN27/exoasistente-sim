# Prototipo virtual del exoasistente de rodilla (MuJoCo)

Primer paso hacia el digital twin: un modelo que simula a la persona levantándose y sentándose con el exo puesto. Se usa para decidir la transmisión, el comportamiento ante fallas y los requisitos de seguridad antes de construir el hardware.

## Cómo correrlo

```bash
python3 -m pip install -r requirements.txt
python3 experimentos.py            # todos los experimentos (~2 min), figuras en figuras/
python3 experimentos.py fallas     # uno solo: nominal | latencia | fallas | sentarse | runaway | transparencia
```

Los parámetros están en `exo_sim.py`: antropometría (`MASA`, `ALTURA`), diseños de transmisión (`DISENOS`) y el escenario (`Config`).

## Qué modela

- **Persona**: modelo sagital de 3 segmentos (pierna, muslo, tronco) con las dos piernas sumadas y los pies fijos al suelo. Antropometría de Winter para 75 kg y 1,70 m. Sigue una trayectoria de levantarse de 2,6 s (despega del asiento a los 0,8 s) con par anticipado (dinámica inversa) más rigidez postural. Su par de extensión de rodilla está limitado a una fracción `capacidad` del mínimo necesario para levantarse sin ayuda (136 N·m en este modelo, calibrado con `calibrar_umbral()`). Tarda 150 ms en darse cuenta de que el exo dejó de ayudar.
- **Exo**: actuador en la rodilla con límite de 25 N·m, límite por tensión de batería, inercia reflejada Jm·N², fricción de la reductora y amortiguamiento con bobinado en corto kt²·N²/R. Da el 25% del par de rodilla desde que detecta la inclinación del tronco (0,4 s).
- **Modos de falla**: libre (sin energía), bobinado en corto, corto con diodo (solo frena la flexión), freno de 150 N·m y trinquete (bloquea la flexión y deja extender).

| Diseño (valores representativos, no de catálogo) | Inercia reflejada | Fricción | Corto kt²N²/R | Par de bloqueo sin límite |
|---|---|---|---|---|
| DC 12 V + 170:1 | 0,032 kg·m² | 5 N·m | 18 N·m·s/rad | 40 N·m |
| BLDC 24 V + 36:1 | 0,039 kg·m² | 1,2 N·m | 11 N·m·s/rad | 115 N·m |
| BLDC 24 V cuasi directo 9:1 | 0,012 kg·m² | 0,4 N·m | 6 N·m·s/rad | 111 N·m |

## Resultados (persona con 85% de la fuerza necesaria salvo que se indique)

1. **Nominal** (`figuras/1_nominal.png`): sin exo no se levanta; con 25 N·m del exo sí. El pico de par de rodilla del modelo es 0,83 N·m/kg por pierna, coherente con los 0,9 N·m/kg que cita el documento.
2. **Alcance de 25 N·m** (`figuras/2_latencia.png`): cubre un déficit de hasta ~15%. Con 80% de fuerza ya no alcanza; para ese usuario haría falta ~30 N·m más la fricción.
3. **Latencia** (`figuras/2_latencia.png`): la asistencia tiene que empezar como máximo 0,5 s después de que la persona empieza a inclinar el tronco, es decir, unos 0,3 s antes de despegar del asiento. Una asistencia tardía puede ser peor que ninguna: con 90% de fuerza y asistencia a los 0,7 s, la persona despega y cae a la silla a 1,4 m/s, mientras que sin exo se queda sentada.
4. **Fallas al levantarse** (`figuras/3_fallas.png`): el único tramo peligroso va del despegue hasta ~70° de rodilla. Antes, la persona vuelve suavemente a la silla y después termina de pie.
   - Con transmisión de baja fricción (BLDC 9:1 o 36:1) y modo libre, la ventana peligrosa dura ~0,2 s. Con la DC 170:1 dura ~0,5 s, porque sus 5 N·m de fricción frenan a la persona.
   - **Frenar o bloquear la rodilla es lo peor**: el freno extiende la ventana peligrosa hasta 2,0 s porque impide terminar de levantarse. El corto también frena la extensión. El trinquete no mejora el caso libre; con los BLDC incluso lo empeora un poco.
5. **Sentarse** (`figuras/4_sentarse.png`): con 70% de fuerza, sin exo cae a la silla a 0,88 m/s. Amortiguar con 8 N·m·s/rad baja a 0,34 m/s. Un corto a través de diodo, sin energía, baja a 0,44 m/s: frena la flexión (sentarse, colapso) sin frenar la extensión (levantarse).
6. **Firmware descontrolado** (`figuras/5_runaway.png`): con límite de corriente de 25 N·m en el driver, ningún caso termina en caída aunque el corte tarde 500 ms. Sin ese límite, un BLDC puede dar ~110 N·m y la persona cae si el corte tarda 200 ms o más.

## Qué implica para el diseño

- Preferir una transmisión retroimpulsable de baja fricción (BLDC con reducción ≤ 36:1) sobre la DC 170:1.
- Ante una falla: liberar la extensión y frenar solo la flexión. Un relé normalmente cerrado que ponga el motor en corto a través de un diodo lo hace sin energía ni software.
- Limitar la corriente del driver por hardware al par máximo y cortar la potencia con un watchdog externo en ≤ 50–100 ms. El watchdog de tareas del ESP32 viene configurado en 5 s por defecto, así que no sirve para esto.
- En los criterios de éxito del MVP, medir la latencia de la asistencia respecto al inicio de la inclinación del tronco, con una meta ≤ 0,5 s.

## Limitaciones

Modelo 2D con las dos piernas sumadas y los pies fijos, así que no simula pérdida de equilibrio ni caídas hacia adelante fuera de la silla. La persona es un seguidor de trayectoria con fuerza limitada, no un modelo muscular. Los motores son representativos y no de catálogo. Todavía no incluye la etapa elástica en serie ni el peso del exo, y no está validado con mediciones reales. Los números sirven para comparar diseños entre sí, no como valores absolutos.

## Siguientes pasos

1. Añadir la etapa elástica en serie y el peso del exo (1,8–2,2 kg).
2. Sustituir los motores representativos por los de catálogo que se consideren.
3. Convertirlo en digital twin: leer ángulo, IMU y corriente del ESP32 por serie/BLE, reproducir la sesión en el modelo y comparar el par estimado contra el medido.
