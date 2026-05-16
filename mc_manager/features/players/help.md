# Gestión de Jugadores — Ayuda

## ¿Qué hace esta sección?

Permite gestionar todos los aspectos de los jugadores: ver quién está conectado, administrar la whitelist (lista blanca), gestionar baneos y controlar quién tiene permisos de operador (OP).

---

## Cómo usar

La sección tiene 4 pestañas:

### Pestaña Online
- Lista de jugadores actualmente conectados.
- Selecciona un jugador y usa **Kick** para expulsarlo temporalmente.
- Usa **Ban Temporal** para banear desde la lista de online.

### Pestaña Whitelist
- Lista de jugadores autorizados a entrar.
- Escribe el nombre en el campo inferior y usa **Agregar**.
- Selecciona un jugador y usa **Quitar** para removerlo.
- Recuerda activar la whitelist en Configuración (`white-list=true`).

### Pestaña Baneos
- Lista de jugadores baneados permanentemente.
- Agrega baneos por nombre de jugador.
- Usa **Desbanear** para perdonar a un jugador.

### Pestaña Operators
- Lista de jugadores con permisos de administrador.
- Los operadores pueden usar todos los comandos de consola.
- **Dar OP** agrega permisos, **Quitar OP** los revoca.

---

## Atajos de teclado

| Tecla | Acción |
|-------|--------|
| `4` | Ir a Jugadores |
| `?` | Abrir esta ayuda |

---

## Preguntas frecuentes

**¿Necesito reiniciar el servidor para que los cambios surtan efecto?**
No, los cambios se aplican via RCON y toman efecto inmediatamente. Si RCON no está disponible, se editan los archivos JSON directamente y pueden requerir `/whitelist reload` desde la consola.

**¿Por qué la lista Online está vacía?**
RCON puede no estar configurado. Actívalo en Configuración o directamente en `server.properties`. Sin RCON, la lista no puede obtenerse en tiempo real.

**¿Qué nivel de OP debo dar?**
- Nivel 1: Bypass spawn protection
- Nivel 2: Comandos de juego básicos
- Nivel 3: Gestión de jugadores (kick, ban)
- Nivel 4: Acceso total (incluyendo detener el servidor)

---

## Solución de problemas

- **"RCON no disponible"**: Activa RCON en server.properties (`enable-rcon=true`, `rcon.password=...`).
- **Los cambios no se guardan**: Verifica que `datos_mc/` tenga permisos de escritura.
- **Error al agregar jugador**: Comprueba que el nombre sea válido (solo letras, números y guión bajo, máximo 16 caracteres).
