# MC Server Manager

Panel de control de terminal (TUI) para gestionar un servidor de Minecraft Java Edition corriendo en Docker. Construido con Python y Textual, ofrece monitoreo en tiempo real, gestión de jugadores, backups, túnel de red, programador de tareas y más, todo desde la terminal.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Textual](https://img.shields.io/badge/Textual-0.85.0-purple)
![Docker](https://img.shields.io/badge/Docker-required-2496ED)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Características

El panel incluye **14 módulos** accesibles desde un menú lateral:

| # | Módulo | Descripción |
|---|--------|-------------|
| 1 | **Dashboard** | Vista general del servidor: estado, uptime, jugadores, mini-gráficos, enlace del túnel |
| 2 | **Monitoreo** | Gráficas en tiempo real de CPU, RAM, red y disco (servidor + host) |
| 3 | **Consola** | Logs del servidor en vivo + envío de comandos vía RCON |
| 4 | **Jugadores** | Gestión de online, whitelist, bans y operadores |
| 5 | **Backups** | Crear, restaurar y eliminar copias de seguridad (`.tar.gz`) |
| 6 | **Configuración** | Editor visual de `server.properties` con formularios dinámicos |
| 7 | **Log Viewer** | Visor con búsqueda, filtros por nivel y exportación a `.txt` |
| 8 | **Túnel Playit.gg** | Control del agente de túnel para conexión externa sin abrir puertos |
| 9 | **Programador** | Tareas automáticas: reinicios, backups periódicos, comandos, anuncios |
| 10 | **Rendimiento JVM** | Edición de flags JVM y memoria directamente en `docker-compose.yml` |
| 11 | **Historial Eventos** | Registro en SQLite de joins, muertes, errores y backups |
| 12 | **Editor Compose** | Editor visual de `docker-compose.yml` con vista YAML |
| 13 | **Alertas** | Reglas configurables de alertas por CPU y RAM con anti-flapping |
| 14 | **Stats Mundo** | Tamaño en disco por dimensión, nombre del mundo y semilla |

---

## Requisitos

### Generales
- [Docker](https://docs.docker.com/get-docker/) con `docker compose` v2 (o `docker-compose` v1)
- Python **3.10 o superior**
- Acceso a terminal con soporte de colores (la mayoría de terminales modernas)

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
# Actualizar paquetes
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.10+ y pip
sudo apt install -y python3 python3-pip python3-venv

# Verificar versión (debe ser 3.10+)
python3 --version
```

### 2. Instalar Docker

```bash
# Instalar Docker oficial
curl -fsSL https://get.docker.com | sudo sh

# Agregar tu usuario al grupo docker (evita usar sudo)
sudo usermod -aG docker $USER

# Cerrar sesión y volver a entrar para que surta efecto
# Verificar instalación
docker --version
docker compose version
```

### 3. Clonar el repositorio

```bash
git clone https://github.com/DarkWinD1437/Minecraft_server_vanilla.git
cd Minecraft_server_vanilla
```

### 4. Crear entorno virtual e instalar dependencias

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 5. Levantar el servidor de Minecraft

```bash
# Esto descarga la imagen y crea el contenedor (primera vez tarda unos minutos)
docker compose up -d
```

> La imagen `itzg/minecraft-server` descargará automáticamente Minecraft **Paper 1.20.4** y aceptará el EULA. Los datos del servidor se guardan en la carpeta `datos_mc/`.

### 6. Ejecutar el panel

```bash
# Con el entorno virtual activo
python app.py
```

---

## Instalación en Windows

> **Nota:** En Windows se usa **Docker Desktop** y la aplicación corre perfectamente en **Windows Terminal** o **PowerShell 7**.

### 1. Instalar Python 3.10+

1. Descargar el instalador desde [python.org](https://www.python.org/downloads/)
2. Durante la instalación, marcar **"Add Python to PATH"**
3. Verificar en PowerShell:
   ```powershell
   python --version
   ```

### 2. Instalar Docker Desktop

1. Descargar desde [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
2. Instalar y reiniciar si se solicita
3. Asegurarse de que Docker Desktop esté corriendo (ícono en la bandeja del sistema)
4. Verificar en PowerShell:
   ```powershell
   docker --version
   docker compose version
   ```

> Si usas WSL2 (recomendado), Docker Desktop se integra automáticamente.

### 3. Clonar el repositorio

```powershell
git clone https://github.com/DarkWinD1437/Minecraft_server_vanilla.git
cd Minecraft_server_vanilla
```

> Si no tienes Git: [git-scm.com](https://git-scm.com/download/win)

### 4. Crear entorno virtual e instalar dependencias

```powershell
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Si PowerShell bloquea la ejecución de scripts, ejecuta primero:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Instalar dependencias
pip install -r requirements.txt
```

### 5. Levantar el servidor de Minecraft

```powershell
docker compose up -d
```

> La primera vez descarga la imagen (aprox. 300-500 MB). Los datos quedan en `datos_mc\`.

### 6. Ejecutar el panel

```powershell
# Con el entorno virtual activo
python app.py
```

> **Recomendación:** Usa [Windows Terminal](https://aka.ms/terminal) para mejor experiencia visual. Ajusta el tamaño de la ventana a al menos **120×35** caracteres.

---

## Configuración inicial

### Cambiar contraseña RCON y memoria

Editar `docker-compose.yml` antes de levantar el servidor (o usar el módulo **Editor Compose** desde el panel):

```yaml
environment:
  MEMORY: 5G                  # RAM asignada al servidor
  RCON_PASSWORD: mcpassword   # Cambiar por una contraseña segura
```

Si cambias la contraseña, también actualizar en `mc_manager/core/config.py`:

```python
rcon_password: str = "mcpassword"   # Debe coincidir con docker-compose.yml
```

### Configurar el túnel Playit.gg (opcional)

El servicio `playit-agent` en `docker-compose.yml` permite que jugadores externos se conecten sin necesidad de abrir puertos en el router.

1. Levantar el servidor con `docker compose up -d`
2. Abrir el módulo **Túnel Playit.gg** en el panel
3. El enlace de conexión aparecerá automáticamente en el log cuando el agente se registre
4. Compartir ese enlace con los jugadores (formato: `xxx.xx.playit.gg:porta`)

---

## Estructura del proyecto

```
Minecraft_server_vanilla/
├── app.py                     # Punto de entrada
├── docker-compose.yml         # Configuración Docker (servidor + túnel)
├── requirements.txt           # Dependencias Python
├── backups/                   # Backups generados por el panel
├── logs/                      # Logs exportados
└── mc_manager/
    ├── core/
    │   ├── config.py          # Configuración centralizada (puertos, rutas, RCON)
    │   ├── docker_client.py   # Cliente Docker via subprocess
    │   ├── events.py          # Eventos Textual entre pantallas
    │   └── os_detect.py       # Detección de SO y WSL
    ├── utils/
    │   ├── formatting.py      # Conversión de unidades (bytes, tiempo, etc.)
    │   └── validators.py      # Validadores (nombres de jugador, memoria, puertos)
    ├── styles/                # Estilos TCSS (Textual CSS)
    ├── screens/               # Pantallas (startup, main, help)
    ├── workers/               # Workers async (stats, logs, procesos)
    └── features/              # 14 módulos (dashboard, monitoring, console...)
```

---

## Atajos de teclado

| Tecla | Acción |
|-------|--------|
| `1` – `9` | Navegar entre los primeros 9 módulos |
| `s` | Iniciar / Detener el servidor |
| `r` | Refrescar datos |
| `?` | Mostrar ayuda del módulo actual |
| `q` | Salir de la aplicación |

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
| Protocolo RCON | Socket puro (stdlib) |
| Cliente Docker | subprocess (sin SDK externo) |

---

## Solución de problemas

**El panel no inicia / error de importación**
```bash
# Verificar que el entorno virtual esté activo
source venv/bin/activate   # Linux
.\venv\Scripts\Activate.ps1  # Windows

# Reinstalar dependencias
pip install -r requirements.txt
```

**"Cannot connect to Docker"**
- Linux: verificar que el servicio esté corriendo: `sudo systemctl start docker`
- Windows: abrir Docker Desktop y esperar a que esté listo
- Asegurarse de que tu usuario esté en el grupo `docker` (Linux): `sudo usermod -aG docker $USER`

**La terminal se ve mal / caracteres extraños**
- Usar una terminal con soporte Unicode y colores: **Windows Terminal**, **iTerm2**, **GNOME Terminal**
- Ajustar el tamaño mínimo a 120×35 caracteres

**RCON no conecta / módulo Jugadores no funciona**
- Verificar que el servidor esté corriendo: `docker ps`
- Confirmar que `RCON_PASSWORD` en `docker-compose.yml` coincide con `config.py`
- El servidor tarda ~30-60 segundos en iniciar completamente antes de aceptar RCON

**Puerto 25565 ya en uso**
```bash
# Linux
sudo lsof -i :25565

# Windows PowerShell
netstat -ano | findstr :25565
```

---

## Licencia

MIT — libre de usar, modificar y distribuir.
