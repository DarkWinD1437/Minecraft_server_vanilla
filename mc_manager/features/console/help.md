# Consola — Ayuda

## ¿Qué hace esta sección?

La Consola muestra en tiempo real los mensajes del servidor Minecraft (logs) y te permite enviar comandos directamente al servidor como si estuvieras en su consola.

---

## Cómo usar

1. Los logs aparecen automáticamente en la pantalla principal de la consola.
2. Escribe un comando en el campo de texto de abajo y presiona **Enter** o el botón **Enviar**.
3. Los comandos se envían al servidor via `rcon-cli` (incluido en la imagen Docker).

**Códigos de color:**
- Blanco: INFO — mensajes normales
- Amarillo: WARN — advertencias
- Rojo: ERROR — errores del servidor
- Cyan: Mensajes del propio servidor `[Server]`

---

## Comandos útiles de Minecraft

| Comando | Descripción |
|---------|-------------|
| `list` | Ver jugadores conectados |
| `say Hola!` | Enviar mensaje a todos |
| `time set day` | Poner de día |
| `weather clear` | Limpiar el clima |
| `tp Jugador 0 64 0` | Teletransportar jugador |
| `give Jugador diamond 64` | Dar objetos |
| `difficulty hard` | Cambiar dificultad |
| `gamemode creative Jugador` | Cambiar modo de juego |
| `whitelist add Jugador` | Agregar a whitelist |
| `ban Jugador Razón` | Banear jugador |
| `stop` | Detener el servidor |

---

## Atajos de teclado

| Tecla | Acción |
|-------|--------|
| `3` | Ir a Consola |
| `Ctrl+L` | Limpiar la consola |
| `Enter` | Enviar comando |
| `?` | Abrir esta ayuda |

---

## Preguntas frecuentes

**¿Por qué mis comandos dan error?**
Verifica que RCON esté habilitado en server.properties (`enable-rcon=true`) y que la contraseña RCON en `config.py` coincida con la del servidor.

**¿Los logs aparecen con delay?**
Pueden tardar 1-2 segundos en aparecer. Es normal dado que se leen del stream de Docker.

**¿Puedo ejecutar comandos si el servidor está detenido?**
No, los comandos RCON requieren que el servidor esté corriendo.

---

## Solución de problemas

- **"RCON no disponible"**: Agrega `enable-rcon=true` y `rcon.password=mcpassword` a `server.properties` y reinicia.
- **Sin logs en la consola**: El servidor puede no estar corriendo. Inícialo desde el Dashboard.
- **La consola se llena muy rápido**: Usa el botón "Limpiar" o activa el filtro de nivel para ver solo errores.
