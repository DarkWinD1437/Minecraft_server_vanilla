# Editor Compose — Ayuda

## ¿Qué hace esta sección?

Editor visual de `docker-compose.yml` que te permite cambiar la versión de Minecraft, el tipo de servidor (Paper, Fabric, etc.), la memoria RAM y otras opciones sin necesidad de editar YAML manualmente.

---

## Cómo usar

1. Haz clic en **🔍 Leer archivo** para cargar la configuración actual.
2. Modifica los campos que necesites.
3. Haz clic en **💾 Guardar** para escribir los cambios.
4. Reinicia los contenedores para aplicar: detén el servidor desde el Dashboard y vuélvelo a iniciar.
5. Usa **👁 Ver YAML** para ver el archivo raw si eres usuario avanzado.

---

## Opciones disponibles

| Opción | Descripción |
|--------|-------------|
| Versión | Versión de Minecraft (1.21.4, 1.20.4, etc.) |
| Tipo | Motor del servidor: Paper, Vanilla, Fabric, Forge, etc. |
| Memoria RAM | Heap de Java para el servidor (ej: 5G) |
| Puerto | Puerto del servidor (por defecto 25565) |
| Política de reinicio | Cuándo Docker reinicia el contenedor automáticamente |
| RCON habilitado | Activar control remoto por RCON |
| Contraseña RCON | Password para el RCON |

---

## Tipos de servidor

| Tipo | Descripción |
|------|-------------|
| PAPER | Recomendado — Mejor rendimiento, soporta plugins Spigot |
| VANILLA | Servidor oficial de Mojang, sin mods ni plugins |
| SPIGOT | Base de Paper, más antiguo |
| FABRIC | Para mods de Fabric (no plugins Spigot) |
| FORGE | Para mods de Forge (modpacks) |
| PURPUR | Fork de Paper con más opciones de configuración |

---

## Preguntas frecuentes

**¿Puedo cambiar la versión de Minecraft?**
Sí, pero ten cuidado: cambiar de versión puede hacer que los mundos existentes sean incompatibles. Haz un backup antes.

**¿Qué pasa si cambio de Paper a Fabric?**
Los plugins de Paper/Spigot NO funcionan en Fabric. Necesitarás mods de Fabric en su lugar.

**¿Cuándo aplican los cambios?**
Solo al reiniciar los contenedores (`docker compose up -d`). Un servidor corriendo ignora los cambios hasta el próximo inicio.

---

## Atajos de teclado

| Tecla / Acción | Descripción |
|----------------|-------------|
| Sidebar → Avanzado → Editor Compose | Navegar a esta sección |
| `?` | Abrir esta ayuda |

---

## Solución de problemas

- **El servidor no inicia tras cambiar la versión**: La versión puede no existir. Verifica en la imagen Docker de itzg.
- **Error al guardar**: Verifica que `docker-compose.yml` exista y tenga permisos de escritura.
