# Monitoreo — Ayuda

## ¿Qué hace esta sección?

El Monitoreo muestra en tiempo real cómo está usando los recursos el servidor Minecraft y el sistema operativo completo. Las gráficas se actualizan automáticamente cada 2 segundos.

---

## Cómo usar

Las gráficas (Sparklines) muestran el historial de los últimos 60 segundos. El valor actual aparece debajo de cada gráfica junto con los valores mínimo y máximo del período.

**Sección Servidor Minecraft:**
- **CPU del Servidor**: Porcentaje de CPU que usa el contenedor Docker del servidor.
- **RAM del Servidor**: Megabytes de RAM que usa el servidor Java.
- **Red Entrada/Salida**: Kilobytes por segundo de datos de red (jugadores conectándose, chunks).
- **Disco Lectura/Escritura**: MB/s de operaciones de disco (guardado del mundo, etc).

**Sección Sistema Host:**
- **CPU Sistema**: Uso total del procesador de la laptop.
- **RAM Sistema**: GB de RAM en uso del sistema operativo.

Las barras de progreso en la parte inferior muestran el uso instantáneo en porcentaje.

---

## Atajos de teclado

| Tecla | Acción |
|-------|--------|
| `2` | Ir a Monitoreo |
| `r` | Forzar actualización |
| `?` | Abrir esta ayuda |

---

## Preguntas frecuentes

**¿Por qué la CPU del servidor es 0%?**
El servidor puede no estar corriendo. Verifica el estado en el Dashboard.

**¿Qué es un nivel normal de CPU para Paper 1.20.4?**
En reposo (sin jugadores): 1-5%. Con 1-3 jugadores: 10-30%. Si supera el 80% constantemente, hay algún plugin o proceso pesado.

**¿Cuánta RAM debería usar el servidor?**
Con la configuración actual (5G heap), el uso normal es de 2-4 GB. Si se acerca a 5 GB constantemente, considera reducir `view-distance` en la configuración.

**¿Por qué la red no muestra nada?**
Si no hay jugadores conectados, el tráfico de red es mínimo (~0 KB/s). Es normal.

---

## Solución de problemas

- **Las gráficas no se actualizan**: El worker de estadísticas puede haber fallado. Reinicia MC Manager.
- **CPU sistema al 100%**: Minecraft está compitiendo con el SO. Reduce la distancia de visión o el número de entidades.
- **RAM sistema al 100%**: Considera reducir el heap de Java en la sección "Rendimiento JVM" y reiniciar el servidor.

---

## Consejos

- La laptop Asus K53Z tiene un A8-3520M (4 núcleos a ~1.6 GHz), así que un 40% de CPU del servidor es suficiente para 2-3 jugadores.
- Si la escritura de disco es muy alta, el servidor está guardando el mundo constantemente. Puedes ajustar `autosave-interval` en el Paper config.
- Mantén la RAM del servidor por debajo del 80% de los 8GB totales para evitar lag del sistema.
