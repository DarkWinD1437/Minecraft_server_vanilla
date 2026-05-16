# Programador de Tareas — Ayuda

## ¿Qué hace esta sección?

Permite configurar tareas automáticas para el servidor: reinicios programados, backups automáticos, anuncios en el chat, y ejecución de comandos en horarios definidos.

---

## Cómo usar

### Plantillas rápidas
Los botones en la parte inferior izquierda añaden tareas preconfiguradas comunes:
- **+ Restart diario**: Reinicia el servidor todos los días a las 4am.
- **+ Backup cada 6h**: Crea un backup automático cada 6 horas.
- **+ Aviso cada 24h**: Envía un mensaje al chat cada 24 horas.

### Crear tarea personalizada
1. Escribe un nombre descriptivo.
2. Selecciona el tipo de tarea.
3. Elige el horario (intervalo o hora diaria fija).
4. Para tareas de anuncio o comando, escribe el parámetro extra.
5. Haz clic en **Agregar Tarea**.

### Tipos de tareas
| Tipo | Descripción |
|------|-------------|
| Reiniciar servidor | Reinicia el contenedor de Minecraft |
| Crear backup | Genera un backup `.tar.gz` del mundo |
| Ejecutar comando RCON | Envía un comando al servidor via RCON |
| Anunciar en chat | Envía un `say` al chat del servidor |

---

## Atajos de teclado

| Tecla | Acción |
|-------|--------|
| `9` | Ir a Programador |
| `?` | Abrir esta ayuda |

---

## Preguntas frecuentes

**¿Las tareas se ejecutan si cierro MC Manager?**
No. Las tareas solo corren mientras MC Manager está abierto. Para tareas sin depender de la app, usa `cron` del sistema operativo en Linux.

**¿Qué pasa si el servidor está detenido cuando se ejecuta una tarea?**
Las tareas de comando y anuncio fallarán silenciosamente (RCON no disponible). Las tareas de backup seguirán, pero el mundo puede estar en estado inconsistente.

**¿Puedo desactivar una tarea sin eliminarla?**
Sí, selecciónala en la tabla y usa el botón **Desactivar**.

---

## Consejos

- Programa el restart diario a las 4am cuando nadie juegue para evitar interrupciones.
- Combina un anuncio "El servidor se reiniciará en 5 minutos" con el restart para avisar a los jugadores.
- Los backups automáticos cada 6 horas son suficientes para la mayoría de servidores pequeños.
