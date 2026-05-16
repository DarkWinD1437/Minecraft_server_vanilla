# Configuración del Servidor — Ayuda

## ¿Qué hace esta sección?

Editor visual del archivo `server.properties` de Minecraft. Te permite cambiar todas las opciones del servidor sin editar el archivo manualmente.

---

## Cómo usar

1. Las opciones están agrupadas por categorías (haz clic en cada sección para expandirla).
2. Modifica los valores que necesites:
   - **Switches**: activan/desactivan opciones boolean (ej: whitelist, PvP).
   - **Selectores**: para opciones con valores fijos (ej: dificultad, modo de juego).
   - **Campos de texto**: para valores numéricos o de texto libre.
3. Haz clic en **Guardar** para escribir los cambios al archivo.
4. Algunos cambios requieren **reiniciar el servidor** (el banner amarillo te avisa).

---

## Opciones más importantes

| Opción | Descripción |
|--------|-------------|
| `level-name` | Nombre de la carpeta del mundo |
| `gamemode` | Modo de juego por defecto (survival/creative) |
| `difficulty` | Dificultad (peaceful/easy/normal/hard) |
| `max-players` | Máximo de jugadores simultáneos |
| `view-distance` | Chunks visibles (más = más CPU/RAM) |
| `white-list` | Activar lista blanca de jugadores |
| `enable-rcon` | Activar RCON para comandos remotos |
| `rcon.password` | Contraseña RCON |
| `online-mode` | Verificar cuentas premium (poner false para cuentas offline) |
| `pvp` | Permitir combate entre jugadores |

---

## Atajos de teclado

| Tecla | Acción |
|-------|--------|
| `6` | Ir a Configuración |
| `?` | Abrir esta ayuda |

---

## Preguntas frecuentes

**¿Necesito reiniciar el servidor después de guardar?**
Depende de la opción. Cambios como `max-players`, `difficulty` y `gamemode` pueden aplicarse vía RCON sin reinicio. Cambios como `level-name`, `server-port` o `online-mode` requieren reinicio completo.

**¿Qué `view-distance` es recomendable para esta laptop?**
Con el A8-3520M, un `view-distance` de 6-8 es óptimo para 1-3 jugadores. El valor por defecto de 10 puede causar lag.

**¿Puedo tener cuentas no premium (crackeadas)?**
Sí, cambia `online-mode=false`. Ten en cuenta que cualquiera puede entrar con cualquier nombre, así que activa la whitelist también.

---

## Solución de problemas

- **"No se encontró server.properties"**: El servidor no ha sido iniciado aún. Inícialo desde el Dashboard.
- **Los cambios no surten efecto**: ¿Guardaste con el botón "Guardar"? ¿Reiniciaste el servidor si era necesario?
- **Error al guardar**: Verifica que la carpeta `datos_mc/` tenga permisos de escritura.
