# MC Server Manager

> **DarkWinD Software** — Panel de control de terminal (TUI) para gestionar un servidor Minecraft Java Edition en Docker.

Construido con Python y Textual. Ofrece monitoreo en tiempo real, historial de comandos, gestión de jugadores, backups con retención automática, túnel de red, programador de tareas y más — todo desde la terminal.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Textual](https://img.shields.io/badge/Textual-0.85.0-purple)
![Docker](https://img.shields.io/badge/Docker-required-2496ED)
![License](https://img.shields.io/badge/license-MIT-green)
![DarkWinD](https://img.shields.io/badge/by-DarkWinD_Software-black)

---

## Características

El panel incluye **15 módulos** accesibles desde el menú lateral:

| # | Módulo | Descripción |
|---|--------|-------------|
| 1 | **Dashboard** | Estado, uptime, jugadores, mini-gráficos y enlace del túnel |
| 2 | **Monitoreo** | Gráficas en tiempo real de CPU, RAM, red y disco (servidor + host) |
| 3 | **Consola** | Logs en vivo + envío de comandos vía RCON con historial ↑↓ |
| 4 | **Jugadores** | Gestión de online, whitelist, bans y operadores |
| 5 | **Backups** | Crear, restaurar y eliminar copias de seguridad con retención automática |
| 6 | **Configuración** | Editor visual de `server.properties` con formularios dinámicos |
| 7 | **Log Viewer** | Visor con búsqueda, filtros por nivel y exportación a `.txt` |
| 8 | **Túnel Playit.gg** | Control del agente de túnel para conexión externa sin abrir puertos |
| 9 | **Programador** | Tareas automáticas: reinicios, backups periódicos, comandos, anuncios |
| 10 | **Rendimiento JVM** | Edición de flags JVM y memoria directamente en `docker-compose.yml` |
| 11 | **Historial Eventos** | Registro en SQLite de joins, muertes, errores y backups |
| 12 | **Editor Compose** | Editor visual de `docker-compose.yml` con vista YAML |
| 13 | **Alertas** | Reglas configurables por CPU/RAM con indicador en la sidebar |
| 14 | **Stats Mundo** | Tamaño en disco por dimensión, nombre del mundo y semilla |
| 15 | **Plugins** | Gestión de plugins: activar/desactivar + descarga desde GitHub y Modrinth |

---

## Requisitos

### Generales
- [Docker](https://docs.docker.com/get-docker/) con `docker compose` v2 (o `docker-compose` v1)
- Python **3.10 o superior**
- Terminal con soporte de colores y Unicode (mínimo **120×35** caracteres)

### Puertos usados
| Puerto | Uso |
|--------|-----|
| `25565` | Minecraft Java (jugadores) |
| `25575` | RCON (control remoto interno) |

---

## Instalación en Linux

Probado en **Linux Mint** y distribuciones basadas en Debian/Ubuntu.

### 1. Instalar dependencias del sistema

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv
python3 --version   # debe ser 3.10+
```

> **Nota sobre contraseñas:** Los comandos `sudo` te pedirán tu contraseña de usuario — es el comportamiento normal de Linux para instalar software del sistema. Una vez que tu usuario esté en el grupo `docker` (paso 2), el panel y los scripts de inicio ya no necesitan `sudo`.

### 2. Instalar Docker

```bash
# Instalar Docker oficial
curl -fsSL https://get.docker.com | sudo sh

# Agregar tu usuario al grupo docker (evita usar sudo para docker)
sudo usermod -aG docker $USER

# Aplicar el nuevo grupo sin cerrar sesión
newgrp docker

# Verificar
docker --version && docker compose version
```

> Si cierras y vuelves a abrir la sesión también aplica el cambio de grupo. La línea `newgrp docker` lo activa inmediatamente en la terminal actual.

### 3. Clonar el repositorio

```bash
git clone https://github.com/DarkWinD1437/Minecraft_server_vanilla.git
cd Minecraft_server_vanilla
```

### 4. Dar permisos de ejecución al script de inicio

```bash
chmod +x start.sh
```

> **¿Por qué necesito esto?** En Linux, los archivos descargados no tienen permiso de ejecución por defecto. `chmod +x` se lo otorga. No requiere `sudo`.

### 5. Ejecutar el panel

```bash
./start.sh
```

El script hace automáticamente **en cada ejecución**:
1. **Auto-update**: hace `git pull` si hay commits nuevos en el remoto (se omite si hay cambios locales sin commit)
2. Verifica que Docker y Python estén disponibles
3. Crea `.env` desde `.env.example` si no existe
4. Crea el entorno virtual de Python la primera vez
5. Instala o actualiza dependencias si `requirements.txt` cambió
6. Lanza el panel

### Configurar variables de entorno (opcional — solo para Playit.gg)

El script crea `.env` automáticamente. Si usas el túnel Playit.gg, edítalo:

```bash
nano .env
```

Agrega tu `SECRET_KEY` de Playit.gg:
```
SECRET_KEY=tu_clave_aqui
```

> **¿Cómo obtener el SECRET_KEY?** Crear cuenta en [playit.gg](https://playit.gg) → **Agents** → **Add Agent** → copiar el valor de `SECRET_KEY=` del comando `docker run` que muestra la página.

---

## Instalación en Windows

> Usa **Windows Terminal** o **PowerShell 7** para mejor experiencia. Ajusta el tamaño a al menos **120×35** caracteres.

### 1. Instalar Python 3.10+

1. Descargar desde [python.org](https://www.python.org/downloads/)
2. Durante la instalación, marcar **"Add Python to PATH"**
3. Verificar: `python --version`

### 2. Instalar Docker Desktop

1. Descargar desde [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
2. Instalar y reiniciar si se solicita
3. Asegurarse de que Docker Desktop esté corriendo (ícono en la bandeja del sistema)
4. Verificar: `docker --version && docker compose version`

### 3. Clonar el repositorio

```powershell
git clone https://github.com/DarkWinD1437/Minecraft_server_vanilla.git
cd Minecraft_server_vanilla
```

### 4. Ejecutar el panel

**Opción A — Doble clic (recomendado):**

Haz doble clic en `start.bat`. No requiere configurar PowerShell ni permisos adicionales.

**Opción B — Desde PowerShell:**

```powershell
.\start.ps1
```

> Si PowerShell bloquea la ejecución de scripts:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

El script hace automáticamente **en cada ejecución**:
1. **Auto-update**: hace `git pull` si hay commits nuevos en el remoto (se omite si hay cambios locales sin commit)
2. Verifica que Docker y Python estén disponibles
3. Crea `.env` desde `.env.example` si no existe
4. Crea el entorno virtual de Python la primera vez
5. Instala o actualiza dependencias si `requirements.txt` cambió
6. Lanza el panel

### Configurar variables de entorno (opcional — solo para Playit.gg)

El script crea `.env` automáticamente. Si usas el túnel:

```powershell
notepad .env
```

---

## Configuración inicial

### Cambiar contraseña RCON y memoria

Editar `docker-compose.yml` antes de levantar el servidor por primera vez (o usar el módulo **Editor Compose** desde el panel):

```yaml
environment:
  INIT_MEMORY: 4G             # Heap mínimo JVM
  MAX_MEMORY: 5G              # Heap máximo JVM
  RCON_PASSWORD: mcpassword   # Cambiar por una contraseña segura
```

Si cambias la contraseña RCON, actualizar también en `mc_manager/core/config.py`:

```python
rcon_password: str = "mcpassword"   # Debe coincidir con docker-compose.yml
```

### Configurar el túnel Playit.gg (opcional)

1. Crear cuenta en [playit.gg](https://playit.gg)
2. Ir a **Agents** → **Add Agent**
3. Copiar el valor de `SECRET_KEY=` del comando `docker run` mostrado
4. Pegarlo en `.env`:
   ```
   SECRET_KEY=xxxxxxxxxxxxxxxx
   ```
5. El agente inicia automáticamente con `docker compose up -d`

---

## Primer uso — Asistente de inicio

Al abrir el panel por primera vez, aparece el **asistente de inicio** que:
- Detecta si el servidor Docker está creado, detenido o nunca iniciado
- Ofrece los botones para crearlo y levantarlo directamente desde el panel
- Descarga Chunky automáticamente para pre-generación del mapa (primera vez)

**No es necesario ejecutar `docker compose up -d` manualmente** — el asistente lo hace.

---

## Estructura del proyecto

```
Minecraft_server_vanilla/
├── app.py                     # Punto de entrada
├── start.sh                   # Launcher Linux (bash) — auto-instala dependencias
├── start.ps1                  # Launcher Windows (PowerShell) — auto-instala dependencias
├── start.bat                  # Launcher Windows (doble clic) — invoca start.ps1 sin configurar permisos
├── docker-compose.yml         # Configuración Docker (servidor + túnel)
├── .env.example               # Plantilla de variables de entorno
├── .env                       # Variables locales — NO subir a git
├── requirements.txt           # Dependencias Python
├── backups/                   # Backups generados por el panel
├── logs/                      # Logs exportados
└── mc_manager/
    ├── __about__.py           # Versión y marca (DarkWinD Software)
    ├── core/
    │   ├── config.py          # Configuración centralizada (puertos, rutas, RCON)
    │   ├── docker_client.py   # Cliente Docker via subprocess
    │   ├── events.py          # Eventos Textual entre pantallas
    │   └── os_detect.py       # Detección de SO y WSL
    ├── utils/
    │   ├── formatting.py      # Conversión de unidades (bytes, tiempo, etc.)
    │   └── validators.py      # Validadores de entrada
    ├── styles/                # Estilos TCSS (Textual CSS)
    ├── screens/               # Pantallas (startup, main, help)
    ├── workers/               # Workers async (stats, logs)
    └── features/              # 15 módulos independientes
```

---

## Atajos de teclado

### Navegación principal (1-9)

| Tecla | Módulo |
|-------|--------|
| `1` | Dashboard |
| `2` | Monitoreo |
| `3` | Consola |
| `4` | Jugadores |
| `5` | Backups |
| `6` | Configuración |
| `7` | Log Viewer |
| `8` | Túnel Playit.gg |
| `9` | Programador |

### Navegación avanzada (Ctrl+1-6)

| Tecla | Módulo |
|-------|--------|
| `Ctrl+1` | Rendimiento JVM |
| `Ctrl+2` | Historial Eventos |
| `Ctrl+3` | Editor Compose |
| `Ctrl+4` | Alertas |
| `Ctrl+5` | Stats Mundo |
| `Ctrl+6` | Plugins |

### Controles globales

| Tecla | Acción |
|-------|--------|
| `s` | Iniciar / Detener el servidor |
| `r` | Refrescar datos |
| `?` | Mostrar ayuda del módulo actual |
| `q` | Salir de la aplicación |

### En la Consola

| Tecla | Acción |
|-------|--------|
| `↑` / `↓` | Navegar historial de comandos |
| `Enter` | Enviar comando |
| `Ctrl+L` | Limpiar la consola |

---

## Stack tecnológico

| Componente | Tecnología |
|-----------|-----------|
| UI / TUI | [Textual](https://textual.textualize.io/) 0.85.0 |
| Stats del sistema | [psutil](https://pypi.org/project/psutil/) 5.9.8 |
| Configuración | [PyYAML](https://pypi.org/project/PyYAML/) ≥6.0 |
| Servidor Minecraft | [itzg/minecraft-server](https://github.com/itzg/docker-minecraft-server) (Paper 1.20.4) |
| Túnel de red | [Playit.gg](https://playit.gg/) agent (Docker) |
| Base de datos eventos | SQLite (stdlib) |
| Protocolo RCON | Socket puro con auto-reconexión |
| Cliente Docker | subprocess con stats en JSON |

---

## Solución de problemas

**El panel no inicia / error de importación**
```bash
# Verificar que el entorno virtual esté activo
source venv/bin/activate       # Linux
.\venv\Scripts\Activate.ps1   # Windows

# Reinstalar dependencias
pip install -r requirements.txt
```

**"Cannot connect to Docker"**
- Linux: verificar que el servicio esté corriendo: `sudo systemctl start docker`
- Windows: abrir Docker Desktop y esperar a que esté listo
- Asegurarse de que tu usuario esté en el grupo `docker` (Linux):
  ```bash
  sudo usermod -aG docker $USER && newgrp docker
  ```

**Linux pide contraseña al ejecutar `sudo systemctl start docker`**

Esto es normal — `sudo` requiere tu contraseña de usuario para iniciar servicios del sistema. Una vez Docker esté corriendo, el panel y los scripts de inicio no necesitan más `sudo`.

Para que Docker inicie automáticamente con el sistema (sin necesitar iniciar manualmente):
```bash
sudo systemctl enable docker
```

**Linux pide contraseña al ejecutar `./start.sh` la primera vez**

El script `start.sh` no usa `sudo`, así que no debería pedir contraseña. Si pasa, verifica que el archivo tenga permisos de ejecución:
```bash
chmod +x start.sh
```

**Los logs no aparecen en el visor (Consola / Log Viewer)**
- Verificar que el contenedor esté corriendo: `docker ps`
- En Linux, comprobar permisos Docker: `docker info` — si falla con "permission denied", agregar usuario al grupo docker
- Asegurarse de tener al menos **120×35** caracteres de terminal

**La terminal se ve mal / botones cortados**
- Usar una terminal con soporte Unicode y colores: **Windows Terminal**, **GNOME Terminal**, **iTerm2**
- Ajustar el tamaño mínimo a **120×35** caracteres — fuente de tamaño 10-11pt en pantallas pequeñas

**RCON no conecta / módulo Jugadores no funciona**
- Verificar que el servidor esté corriendo: `docker ps`
- Confirmar que `RCON_PASSWORD` en `docker-compose.yml` coincide con `config.py`
- El servidor tarda ~30-60 segundos en iniciar completamente antes de aceptar RCON
- El cliente RCON reintenta automáticamente si la conexión se cae momentáneamente

**Chunky no aparece en datos_mc/plugins/**
- Ir al módulo **Plugins** y pulsar "⬇ Instalar" en Chunky manualmente
- Una vez instalado, reiniciar el servidor y ejecutar `/chunky radius 1500 && /chunky start`

**Puerto 25565 ya en uso**
```bash
# Linux
sudo lsof -i :25565
# Windows PowerShell
netstat -ano | findstr :25565
```

---

## Licencia

MIT — © 2026 DarkWinD Software. Libre de usar, modificar y distribuir.
