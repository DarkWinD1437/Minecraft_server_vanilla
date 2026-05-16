# Dashboard — Ayuda

## ¿Qué hace esta sección?

El Dashboard es la pantalla principal de MC Manager. Te muestra de un vistazo el estado del servidor, los recursos que está usando y el link de conexión de Playit.gg.

---

## Cómo usar

1. **Estado del Servidor** (tarjeta superior izquierda): muestra si el servidor está en línea (🟢), detenido (🔴) o sin crear (⚪), junto con el tiempo que lleva corriendo (uptime).
2. **Acciones Rápidas** (tarjeta superior derecha): botones para iniciar, detener y reiniciar el servidor sin salir del dashboard.
3. **Recursos (mini)** (tarjeta inferior izquierda): mini-gráficas de CPU y RAM de los últimos 30 segundos.
4. **Túnel Playit.gg** (tarjeta inferior derecha): muestra el link para que tus amigos puedan conectarse sin abrir puertos.

---

## Atajos de teclado

| Tecla | Acción |
|-------|--------|
| `s` | Toggle start/stop del servidor (desde cualquier pantalla) |
| `1` | Ir al Dashboard |
| `?` | Abrir esta ayuda |

---

## Preguntas frecuentes

**¿Por qué el estado dice "SIN CONTENEDOR"?**
El contenedor de Docker no ha sido creado todavía. Haz clic en "Iniciar Servidor" o usa el wizard de la pantalla de inicio.

**¿Por qué no veo el link de Playit.gg?**
El link aparece cuando el servicio `mc_tunel_red` está corriendo y ha establecido la conexión. Puede tardar hasta 30 segundos la primera vez. Haz clic en "Recargar Link".

**¿El uptime se reinicia si cierro MC Manager?**
No, el uptime se lee directamente de Docker (cuándo se inició el contenedor), así que no depende de que la app esté abierta.

---

## Solución de problemas

- **Los botones no responden**: Comprueba que Docker esté corriendo (`docker info` en terminal).
- **El estado nunca cambia a ONLINE**: Revisa los logs del servidor en la sección "Consola" o "Log Viewer".
- **Uptime muestra `--:--:--`**: El servidor no ha arrancado aún o acaba de reiniciarse.

---

## Consejos

- Usa el atajo `s` para iniciar/detener el servidor rápidamente desde cualquier sección.
- Si el servidor lleva mucho tiempo online sin jugadores, considera detenerlo para ahorrar RAM (la laptop Asus tiene 8GB compartidos).
- Revisa el Dashboard antes de empezar a jugar para asegurarte de que el túnel está activo.
