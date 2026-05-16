# Stats del Mundo — Ayuda

## ¿Qué hace esta sección?

Muestra estadísticas del mundo Minecraft desde el sistema de archivos: tamaño en disco de cada dimensión, número de archivos de región (chunks guardados) y la semilla del mundo.

---

## Cómo usar

1. Haz clic en **🔄 Actualizar stats** para escanear el directorio `datos_mc/`.
2. La tabla muestra las 3 dimensiones: Overworld, Nether y End.
3. **Abrir carpeta** abre el explorador de archivos en la carpeta de datos del servidor.

---

## Información mostrada

| Campo | Descripción |
|-------|-------------|
| Dimensión | Nombre de la carpeta de la dimensión |
| Tamaño en disco | Espacio que ocupa esa dimensión |
| Archivos .mca | Número de archivos de región guardados |
| Chunks aprox. | Estimación de chunks generados (1 archivo .mca = hasta 1024 chunks) |
| Semilla | Semilla del mundo (de level.dat) |
| Tamaño total | Suma del tamaño de todas las dimensiones |

---

## Preguntas frecuentes

**¿Por qué la semilla muestra "—"?**
El archivo `level.dat` no existe (el servidor no se ha iniciado aún) o no se pudo leer.

**¿Cómo afecta el tamaño del mundo al rendimiento?**
Un mundo muy grande (>5GB) puede causar tiempos de carga más largos al iniciar el servidor. El rendimiento durante el juego depende más de los chunks activamente cargados.

**¿Puedo borrar dimensiones que no uso?**
Sí, pero el servidor debe estar detenido. Borra la carpeta de la dimensión y se regenerará la próxima vez que un jugador entre en ella.

**¿Cómo reduzco el tamaño del mundo?**
Usa herramientas como `minecraft-chunk-trimmer` o `mca-selector` para eliminar chunks no visitados. Haz un backup antes.

---

## Consejos

- Si el mundo pesa más de 5GB, considera borrar las regiones del Nether y del End que no hayas explorado.
- La carpeta de datos más grande suele ser el Overworld. El Nether y el End son opcionales.
- Verifica periódicamente el tamaño para asegurarte de que no se llene el disco de 250GB de la laptop.
