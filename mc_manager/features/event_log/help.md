# Historial de Eventos — Ayuda

## ¿Qué hace esta sección?

Registra y muestra todos los eventos importantes del servidor en una base de datos SQLite persistente. Incluye conexiones de jugadores, errores del servidor, backups realizados y comandos ejecutados.

---

## Cómo usar

1. Los eventos se registran automáticamente mientras MC Manager está corriendo.
2. Usa el selector de categoría para filtrar por tipo de evento.
3. Haz clic en **Actualizar** para recargar la vista.
4. **Exportar CSV** guarda el historial filtrado para análisis externo.

---

## Categorías de eventos

| Categoría | Descripción |
|-----------|-------------|
| Servidor | Inicio, parada, reinicios del servidor |
| Jugadores | Conexiones, desconexiones, muertes |
| Backups | Backups creados, restaurados |
| Comandos | Comandos RCON ejecutados desde MC Manager |
| Sistema | Inicio de MC Manager, errores del sistema |
| Errores | Errores críticos del servidor detectados en logs |

---

## Atajos de teclado

| Tecla / Acción | Descripción |
|----------------|-------------|
| Sidebar → Avanzado → Historial Eventos | Navegar a esta sección |
| `?` | Abrir esta ayuda |

---

## Preguntas frecuentes

**¿Los eventos persisten entre sesiones?**
Sí, se guardan en `logs/events.db` (SQLite). Los datos se mantienen aunque cierres MC Manager.

**¿Por qué no aparecen eventos de jugadores?**
Los eventos de jugadores se detectan parseando los logs del servidor. Si el servidor no está corriendo o los logs no fluyen, no habrá eventos.

**¿Puedo borrar el historial?**
Sí, elimina el archivo `logs/events.db` manualmente. MC Manager creará uno nuevo la próxima vez.

---

## Consejos

- Exporta el historial a CSV antes de actualizar el servidor para tener un registro de la actividad.
- Los errores críticos aparecen automáticamente — revisa esta sección si el servidor crasheó.
- Útil para saber quién estuvo conectado y cuándo, sin necesitar logs raw.
