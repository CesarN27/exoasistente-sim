# Cómo leer los resultados de la simulación

## 1. Los números que hay que tener en la cabeza

| Valor | Qué es | De dónde sale |
|---|---|---|
| **124 N·m** | Par de extensión de rodilla que necesita la persona en el punto más duro del levantarse (las dos piernas sumadas, ≈62 N·m por pierna, 0,83 N·m/kg) | Dinámica inversa: el modelo calcula qué par articular hace falta para seguir la trayectoria de referencia |
| **136 N·m** | Fuerza mínima de rodilla con la que la persona se levanta sola en este modelo (`UMBRAL_SOLA` = 1,094 × 124) | Bisección: se baja la fuerza hasta que deja de lograrlo. Es más que 124 porque la persona tiene retardo y el control no es perfecto |
| **85%** | La persona simulada tiene 0,85 × 136 = **116 N·m** de fuerza de rodilla. Le faltan 20 N·m | Parámetro `capacidad` |
| **25 N·m** | Par máximo del exo, en **una** rodilla. Como el modelo suma las dos piernas en una sola cadena, es equivalente a un exo en una pierna con la otra sin ayuda | `tau_max` de cada diseño |
| **0,5 m/s** | Velocidad a la que la pelvis toca la silla. Por debajo se considera un asiento suave, por encima un golpe | Umbral que elegí; no viene de una norma |

**Idea clave:** "85% de fuerza" no significa 85% de un adulto sano. Significa 85% de lo mínimo que necesita para levantarse sola. Por eso 25 N·m alcanzan: le faltan 20.

## 2. Figura por figura

### 1_nominal.png: ¿ayuda el exo?
- Izquierda: la línea gris (sin exo) se queda en ~75° de flexión, es decir, la persona no logra estirar la rodilla. La verde (con exo) sigue casi exacto la referencia punteada y llega a 0° (de pie).
- Derecha: la línea gris punteada en ~116 N·m es el techo de fuerza de la persona. Mientras el exo aporta sus 25 N·m (azul), la curva verde de la persona baja de ese techo y logra levantarse. Es el "20% que falta".

### 2_latencia.png: ¿cuándo tiene que empezar a ayudar?
- Cada fila es una fuerza de la persona; cada columna, cuándo empieza el exo desde que la persona empieza a inclinar el tronco. La persona despega del asiento a los 0,8 s.
- Verde = termina de pie. Amarillo = vuelve a la silla suavemente (el número es la velocidad de impacto). Rojo = cae con fuerza (≥ 0,5 m/s).
- Lectura: a 85% funciona si el exo empieza a los 0,5 s o antes. A 80% no lo arregla ningún momento de inicio, porque le faltan más de los 25 N·m que da el exo. A 90%, si el exo llega tarde (0,7 s o más) la persona despega sin apoyo y cae fuerte: **llegar tarde es peor que no ayudar**.

### 3_fallas.png: ¿qué pasa si el exo falla?
- Eje horizontal: en qué momento falla (arriba, el tiempo; abajo, la flexión de rodilla en ese instante).
- Cada fila es un diseño con un modo de falla. Los cuadros amarillos de la izquierda son fallas antes de despegar: la persona simplemente se queda sentada.
- La zona roja es la peligrosa: entre el despegue y ~70°. Ahí la persona ya no está apoyada en la silla y todavía no tiene la rodilla estirada.
- Comparar filas: en la DC 170:1 la zona roja es más ancha porque sus 5 N·m de fricción frenan a la persona incluso apagada. En "freno 150 N·m" la zona roja llega hasta el final porque impide estirar la rodilla. Los mejores modos son "libre" y "corto con diodo".

### 4_sentarse.png: ¿qué tan fuerte cae a la silla?
- Eje horizontal: fuerza de la persona (de 100% a 50%). Eje vertical: velocidad de impacto. Más bajo es mejor.
- El exo apagado (línea verde discontinua) casi no cambia nada frente a no tener exo. Amortiguar activamente o usar el corto con diodo reduce el impacto claramente a partir de 70%.
- El punto más bajo de la DC 170:1 a 80% (0,32 m/s) no es una ventaja real: es la fricción de la reductora frenando, y a la vez es lo que la hace mala al levantarse.

### 5_runaway.png: firmware descontrolado
- El motor empuja al máximo en flexión (contra la persona) desde 1,7 s hasta que un watchdog corta la potencia. Columnas: cuánto tarda ese corte.
- Con límite de corriente en el driver (25 N·m), nunca pasa nada. Sin límite, los BLDC pueden dar ~110 N·m y la persona cae si el corte tarda 200 ms o más. La DC sin límite solo llega a 40 N·m porque su motor es pequeño.

## 3. Tabla de transparencia (`resultados.json`, clave `transparencia`)

| Diseño | Inercia reflejada | Fricción | Par parásito pico | Par de bloqueo |
|---|---|---|---|---|
| DC 12 V + 170:1 | 0,032 kg·m² | 5,0 N·m | **5,4 N·m** | 40 N·m |
| BLDC + 36:1 | 0,039 kg·m² | 1,2 N·m | 1,6 N·m | 115 N·m |
| BLDC cuasi directo 9:1 | 0,012 kg·m² | 0,4 N·m | **0,7 N·m** | 111 N·m |

- **Par parásito**: lo que la persona tiene que vencer para mover el exo cuando está apagado (inercia × aceleración + fricción + viscosidad). Con la DC son 5,4 N·m, un 22% de lo que aporta el exo; con el BLDC 9:1, 0,7 N·m.
- **Par de bloqueo**: lo que empujaría el motor con la tensión completa y sin límite de corriente. Es el número que hay que limitar por hardware.
- La inercia reflejada es Jm·N². Sube con el cuadrado de la reducción, por eso la DC 170:1 se siente "pesada" aunque su motor sea diminuto.

## 4. Qué NO significan estos números

- No son predicciones de un exo real. Los motores son valores representativos y el modelo no incluye la etapa elástica ni el peso del exo.
- Los umbrales (0,5 m/s, 85%, 150 N·m del freno, retardo de 150 ms) son supuestos míos. Los que más mueven las conclusiones son el retardo de reacción de la persona y la fuerza que se le asigna. Conviene repetir los experimentos cambiándolos.
- Sirven para comparar diseños entre sí y ver tendencias, no para dar cifras absolutas de seguridad.
