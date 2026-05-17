# Gestor de Plugins

Administra los plugins instalados en el servidor Paper: activa/desactiva, descarga recomendados automáticamente e instala desde URL directa.

---

## Secciones del panel

### Plugins instalados
Lista todos los `.jar` encontrados en `datos_mc/plugins/`. Cada fila muestra el nombre y estado del plugin.

| Botón | Acción |
|-------|--------|
| ✅ Activar | Reactiva el plugin seleccionado (renombra `.jar.disabled` → `.jar`) |
| ❌ Desactivar | Desactiva el plugin seleccionado (renombra `.jar` → `.jar.disabled`) |
| 🔄 Refrescar | Vuelve a escanear la carpeta de plugins |
| ↺ Reiniciar servidor | Reinicia el contenedor Docker para aplicar cambios |

> **Importante:** activar o desactivar un plugin requiere reiniciar el servidor para que Paper lo cargue o descargue.

---

### Plugins recomendados
9 plugins curados listos para instalar con un clic. La descarga se hace automáticamente desde GitHub o Modrinth.

| Plugin | Fuente | Descripción |
|--------|--------|-------------|
| EssentialsX | GitHub | Comandos `/ping`, `/home`, `/tpa`, `/spawn`, `/back` |
| LuckPerms | GitHub | Sistema de permisos por grupos |
| spark | GitHub | Profiler de rendimiento (recomendado por Paper) |
| Dynmap | GitHub | Mapa web interactivo del mundo en tiempo real |
| Coordinates HUD | Modrinth | Coordenadas visibles en pantalla para todos |
| Chunky | GitHub | Pre-generación de chunks (usar antes del primer arranque) |
| CoreProtect | GitHub | Registro de bloques — quién rompió/colocó qué y cuándo |
| Vault | GitHub | Puente de economía/permisos requerido por muchos plugins |
| ViaVersion | GitHub | Permite conectar clientes de versiones más nuevas |

Haz clic en **⬇ Instalar** junto a cualquier plugin. El JAR se descarga directamente a `datos_mc/plugins/` y aparecerá en la tabla de instalados al refrescar.

---

### Instalar desde URL directa
Pega la URL de descarga directa de cualquier `.jar` (Hangar, SpigotMC, GitHub Releases, etc.) y haz clic en **⬇ Instalar JAR**.

- La URL **debe terminar en `.jar`**
- El archivo se descarga directamente a `datos_mc/plugins/`
- Útil para plugins no incluidos en la lista de recomendados

---

## Flujo completo de instalación

1. Haz clic en **⬇ Instalar** o pega la URL y pulsa **⬇ Instalar JAR**
2. Espera la notificación de descarga completada
3. Haz clic en **🔄 Refrescar** para ver el plugin en la tabla
4. Haz clic en **↺ Reiniciar servidor** para que Paper lo cargue

---

## Activar / Desactivar sin eliminar

Paper ignora los archivos `.jar.disabled` al iniciar. MC Manager usa este mecanismo para activar y desactivar plugins sin borrarlos:

- **Desactivar**: el JAR se renombra a `.jar.disabled` → Paper lo ignora al reiniciar
- **Activar**: el `.jar.disabled` vuelve a ser `.jar` → Paper lo carga al reiniciar

---

## Atajos de teclado

| Tecla | Acción |
|-------|--------|
| `15` (sidebar) | Ir a Plugins desde el menú lateral |
| `?` | Abrir esta ayuda |

---

## Preguntas frecuentes

**¿Por qué el plugin no aparece en la tabla después de instalar?**
Haz clic en **🔄 Refrescar** — la tabla no se actualiza automáticamente tras la descarga.

**¿El servidor necesita estar corriendo para instalar plugins?**
No, los plugins se copian a la carpeta directamente. El servidor solo necesita estar corriendo para el botón **Reiniciar**.

**¿Puedo instalar cualquier plugin de SpigotMC?**
Sí, usando la sección "Instalar desde URL directa". Copia la URL del archivo `.jar` de la página de descarga del plugin.

**¿Puedo instalar plugins con versiones específicas?**
La lista de recomendados siempre descarga la **última versión** disponible. Para versiones específicas, usa la URL directa del release que necesitas.

---

## Solución de problemas

- **Error al descargar**: Verifica tu conexión a internet. GitHub y Modrinth pueden tener límites de tasa (rate limit) si haces muchas peticiones seguidas.
- **Plugin no carga**: Revisa la Consola para ver si hay errores del plugin al iniciar el servidor.
- **No aparece en la tabla**: Asegúrate de que el archivo sea un `.jar` válido en `datos_mc/plugins/` y haz clic en Refrescar.
- **Error de permisos**: Verifica que la carpeta `datos_mc/plugins/` tenga permisos de escritura.
