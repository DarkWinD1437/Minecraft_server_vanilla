# MC Server Manager — Launcher para Windows
# Uso: .\start.ps1
# Si PowerShell bloquea la ejecucion, ejecuta primero:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

$ErrorActionPreference = "Continue"

# ── Colores ──────────────────────────────────────────────────────────────────
function ok   { param($msg) Write-Host "  " -NoNewline; Write-Host "v" -ForegroundColor Green -NoNewline; Write-Host "  $msg" }
function warn { param($msg) Write-Host "  " -NoNewline; Write-Host "!" -ForegroundColor Yellow -NoNewline; Write-Host "  $msg" }
function fail { param($msg) Write-Host "  " -NoNewline; Write-Host "x" -ForegroundColor Red -NoNewline; Write-Host "  $msg" }
function info { param($msg) Write-Host "  " -NoNewline; Write-Host ">" -ForegroundColor Cyan -NoNewline; Write-Host "  $msg" }

Write-Host ""
Write-Host "  +======================================+" -ForegroundColor Cyan
Write-Host "  |       MC Server Manager v1.0         |" -ForegroundColor Cyan
Write-Host "  +======================================+" -ForegroundColor Cyan
Write-Host ""

# ── Posicionarse en la carpeta del script ─────────────────────────────────────
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

$ERRORES = 0

# ─────────────────────────────────────────────────────────────────────────────
Write-Host "  Verificando requisitos..." -ForegroundColor White

# 1. Python
$PythonCmd = $null
foreach ($cmd in @("python", "python3")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 8)) {
                ok "Python $major.$minor"
                $PythonCmd = $cmd
                break
            } else {
                warn "Python $major.$minor detectado — se requiere 3.8 o superior"
                $ERRORES++
            }
        }
    } catch {}
}
if ($null -eq $PythonCmd) {
    fail "Python no encontrado"
    info "Descarga desde: https://www.python.org/downloads/"
    info "Marcar 'Add Python to PATH' durante la instalacion"
    $ERRORES++
}

# 2. Docker instalado
$DockerOk = $false
try {
    $dver = & docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        ok "Docker $($dver -replace 'Docker version ','' -replace ',.*','')"
        $DockerOk = $true
    } else {
        throw "no encontrado"
    }
} catch {
    fail "Docker no instalado o no en PATH"
    info "Instala Docker Desktop: https://www.docker.com/products/docker-desktop/"
    $ERRORES++
}

# 3. Docker daemon activo
if ($DockerOk) {
    try {
        $null = & docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            ok "Docker daemon activo"
        } else {
            warn "Docker daemon no esta corriendo"
            info "Abre Docker Desktop y espera que el icono en la bandeja este listo"
            warn "El manager abrira, pero los controles del servidor no funcionaran"
        }
    } catch {
        warn "No se pudo verificar el estado del Docker daemon"
    }
}

# 4. Docker Compose
$ComposeCmd = $null
try {
    $null = & docker compose version 2>&1
    if ($LASTEXITCODE -eq 0) {
        ok "Docker Compose v2 (integrado)"
        $ComposeCmd = "docker compose"
    }
} catch {}

if ($null -eq $ComposeCmd) {
    try {
        $null = & docker-compose --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            warn "Docker Compose v1 detectado — funciona, pero v2 es preferible"
            $ComposeCmd = "docker-compose"
        }
    } catch {}
}

if ($null -eq $ComposeCmd) {
    warn "Docker Compose no encontrado"
    info "Asegurate de tener Docker Desktop con Compose incluido"
}

# 5. Archivo .env
if (Test-Path ".env") {
    ok ".env presente"
} else {
    warn ".env no encontrado — el tunel Playit.gg no funcionara"
    info "Copia .env.example como .env y anade tu SECRET_KEY"
    if (Test-Path ".env.example") {
        info "Ejecuta: Copy-Item .env.example .env"
    }
}

# 6. docker-compose.yml
if (Test-Path "docker-compose.yml") {
    ok "docker-compose.yml presente"
} else {
    fail "docker-compose.yml no encontrado — el servidor no puede levantarse"
    $ERRORES++
}

# 7. Carpeta datos_mc
if (Test-Path "datos_mc" -PathType Container) {
    ok "datos_mc\ presente"
} else {
    warn "datos_mc\ no existe — se creara cuando levantes el servidor por primera vez"
}

Write-Host ""

# ── Abortar si hay errores criticos ──────────────────────────────────────────
if ($ERRORES -gt 0) {
    Write-Host "  $ERRORES problema(s) critico(s). Corrigelos antes de continuar." -ForegroundColor Red
    Write-Host ""
    Read-Host "  Presiona Enter para salir"
    exit 1
}

# ─────────────────────────────────────────────────────────────────────────────
Write-Host "  Preparando entorno Python..." -ForegroundColor White

$VenvActivate = ".\venv\Scripts\Activate.ps1"
$VenvPython   = ".\venv\Scripts\python.exe"

if (-not (Test-Path $VenvActivate)) {
    info "Creando entorno virtual..."
    & $PythonCmd -m venv venv
    if ($LASTEXITCODE -ne 0) {
        fail "No se pudo crear el entorno virtual"
        exit 1
    }
    . $VenvActivate
    info "Instalando dependencias..."
    & pip install -q -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        ok "Dependencias instaladas"
    } else {
        warn "Algunas dependencias no se instalaron correctamente"
    }
} else {
    . $VenvActivate
    ok "Entorno virtual activado"
}

Write-Host ""
Write-Host "  Lanzando MC Manager..." -ForegroundColor White
Write-Host ""

& python app.py
