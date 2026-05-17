# Backups — Ayuda

## ¿Qué hace esta sección?

Permite crear, listar y restaurar copias de seguridad (backups) de los datos del mundo Minecraft. Los backups se guardan como archivos `.tar.gz` en la carpeta `backups/`.

---

## Cómo usar

### Crear un backup
1. Escribe un nombre descriptivo en el campo "Nombre del backup" (ej: `antes-del-update`).
2. Activa o desactiva la compresión (`.tar.gz` vs `.tar`). La compresión ocupa menos espacio.
3. Configura la **retención máxima** (opcional — ver sección más abajo).
4. Haz clic en **Crear Backup Ahora**.
5. El proceso enviará `save-off` al servidor (pausar guardado automático) antes de comprimir, y `save-on` al terminar. Esto garantiza que el backup sea consistente.

### Restaurar un backup
1. Selecciona el backup en la lista (haz clic en él).
2. Haz clic en **Restaurar**.
3. **Detén el servidor antes de restaurar** para evitar conflictos de archivos.
4. Después de restaurar, inicia el servidor normalmente.

### Eliminar un backup
1. Selecciona el backup en la lista.
2. Haz clic en **Eliminar**.

---

## Retención automática de backups

El campo **Retención máx.** controla cuántos backups se conservan automáticamente:

- **0** (por defecto): sin límite — nunca elimina backups automáticamente
- **N > 0**: después de cada backup creado, elimina los más antiguos hasta mantener solo N backups

**Ejemplo:** Si tienes 8 backups y configuras retención en 5, al crear uno nuevo quedaran 5 (el nuevo + los 4 más recientes).

> La retención solo se aplica al **crear** un backup nuevo. No afecta backups existentes hasta la próxima creación.

---

## Atajos de teclado

| Tecla | Acción |
|-------|--------|
| `5` | Ir a Backups |
| `?` | Abrir esta ayuda |

---

## Preguntas frecuentes

**¿Dónde se guardan los backups?**
En la carpeta `backups/` dentro del directorio del proyecto (al lado de `docker-compose.yml`).

**¿Cuánto espacio ocupa un backup?**
Depende del tamaño del mundo. Un mundo típico de 100MB comprimido puede quedar en 30-60 MB. Mundos explorados pueden pesar varios GB.

**¿Puedo hacer backups con el servidor encendido?**
Sí. MC Manager pausa el guardado automático (`save-off`) durante el backup para garantizar la consistencia, y lo reactiva al terminar.

**¿Se hacen backups automáticamente?**
No por defecto. Puedes configurar backups automáticos en la sección "Programador de Tareas".

---

## Solución de problemas

- **"Error: No se encontró el directorio de datos"**: El servidor no ha creado `datos_mc/` aún. Inícialo al menos una vez.
- **El backup tarda mucho**: Mundos grandes tardan más. Es normal para mundos de varios GB.
- **Error al restaurar**: Asegúrate de que el servidor esté **detenido** antes de restaurar.

---

## Consejos

- Haz un backup **antes** de cambiar la versión de Minecraft o instalar plugins nuevos.
- Configura backups automáticos cada 6 horas en el Programador para no perder progreso.
- Los backups más antiguos pueden eliminarse para liberar espacio en disco.
