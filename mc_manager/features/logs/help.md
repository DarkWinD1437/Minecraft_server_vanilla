# Log Viewer — Ayuda

## ¿Qué hace esta sección?

Visualizador avanzado de los logs del servidor Minecraft con filtros, búsqueda y exportación. A diferencia de la Consola, aquí puedes pausar los logs, filtrar por nivel de severidad y buscar texto específico.

---

## Cómo usar

1. Los logs aparecen automáticamente en tiempo real (modo LIVE).
2. Usa el campo de búsqueda para filtrar líneas que contengan un texto específico.
3. Usa el selector de nivel para ver solo INFO, WARN o ERROR.
4. El botón **Pausar** congela la vista sin detener la captura de logs.
5. **Exportar** guarda los logs filtrados actuales en `logs/export_YYYYMMDD_HHMMSS.txt`.

**Colores:**
- Blanco: INFO — mensajes normales
- Amarillo: WARN — advertencias
- Rojo: ERROR — errores críticos

---

## Atajos de teclado

| Tecla | Acción |
|-------|--------|
| `7` | Ir a Log Viewer |
| `?` | Abrir esta ayuda |

---

## Preguntas frecuentes

**¿Qué diferencia hay entre la Consola y el Log Viewer?**
La Consola está pensada para interactuar en tiempo real (enviar comandos). El Log Viewer es para análisis: buscar errores, filtrar por nivel, exportar para diagnóstico.

**¿Se guardan los logs entre sesiones?**
El buffer en memoria (últimas 5000 líneas) se pierde al cerrar MC Manager. Los logs de Docker se mantienen hasta que se recrea el contenedor.

**¿Puedo buscar un error específico?**
Sí, escribe el texto en el campo de búsqueda. El filtro se aplica en tiempo real al buffer de logs.

---

## Solución de problemas

- **Sin logs**: El servidor no está corriendo o Docker no está disponible.
- **Demasiados logs**: Usa el filtro de nivel "ERROR" para ver solo los problemas.
- **Error al exportar**: Verifica que la carpeta `logs/` tenga permisos de escritura.
