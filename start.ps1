# MC Server Manager — Launcher para Windows
# Uso: .\start.ps1
# Si PowerShell bloquea la ejecucion, ejecuta primero:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

$ErrorActionPreference = "Continue"

# ── Colores ──────────────────────────────────────────────────────────────────
function ok   { param($msg) Write-Host "  " -NoNewline; Write-Host "v" -ForegroundColor Green  -NoNewline; Write-Host "  $msg" }
function warn { param($msg) Write-Host "  " -NoNewline; Write-Host "!" -ForegroundColor Yellow -NoNewline; Write-Host "  $msg" }
function fail { param($msg) Write-Host "  " -NoNewline; Write-Host "x" -ForegroundColor Red    -NoNewline; Write-Host "  $msg" }
function info { param($msg) Write-Host "  " -NoNewline; Write-Host ">" -ForegroundColor Cyan   -NoNewline; Write-Host "  $msg" }

Write-Host ""
Write-Host "  +======================================+" -ForegroundColor Cyan
Write-Host "  |    MC Server Manager - DarkWinD      |" -ForegroundColor Cyan
Write-Host "  +======================================+" -ForegroundColor Cyan
Write-Host ""

# ── Posicionarse en la carpeta del script ─────────────────────────────────────
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

$ERRORES = 0

# ── Auto-actualización desde git ──────────────────────────────────────────────
Write-Host "  Verificando actualizaciones..." -ForegroundColor White

$GitOk  = $false
$IsRepo = $false

try {
    $null = & git --version 2>&1
    if ($LASTEXITCODE -eq 0) { $GitOk = $true }
} catch {}

if ($GitOk) {
    try {
        $null = & git rev-parse --is-inside-work-tree 2>&1
        if ($LASTEXITCODE -eq 0) { $IsRepo = $true }
    } catch {}
}

if ($GitOk -and $IsRepo) {
    # Contar cambios en archivos tracked (ignorar untracked)
    $LocalChanges = (& git status --porcelain 2>&1 | Where-Object { $_ -notmatch '^\?\?' } | Measure-Object).Count

    if ($LocalChanges -gt 0) {
        warn "Hay cambios locales sin commit — se omite el auto-update"
    } else {
        $null = & git fetch origin --quiet 2>&1
        $Local  = (& git rev-parse HEAD 2>&1) -join ""
        $Remote = ""
        try { $Remote = (& git rev-parse "@{u}" 2>&1) -join "" } catch {}

        if ($Remote -ne "" -and $Local -ne $Remote) {
            info "Commits nuevos disponibles:"
            $NewCommits = & git log "HEAD..@{u}" --oneline 2>&1
            foreach ($line in $NewCommits) {
                Write-Host "      • $line" -ForegroundColor Cyan
            }
            $null = & git pull --quiet 2>&1
            if ($LASTEXITCODE -eq 0) {
                ok "Proyecto actualizado"
                # Si el launcher mismo cambió → reiniciar para usar la versión nueva
                $ChangedFiles = (& git diff "HEAD@{1}" HEAD --name-only 2>&1)
                if ($ChangedFiles -contains "start.ps1") {
                    info "start.ps1 fue actualizado — aplicando nueva version..."
                    Start-Sleep -Seconds 1
                    & powershell -NoLogo -ExecutionPolicy RemoteSigned -File $MyInvocation.MyCommand.Definition
                    exit 0
                }
                # Si docker-compose.yml cambió → avisar para reiniciar el contenedor
                if ($ChangedFiles -contains "docker-compose.yml") {
                    warn "docker-compose.yml cambio — reinicia el servidor desde el manager para aplicar la nueva config"
                    info "Los datos del mundo NO se veran afectados (datos_mc/ esta protegido)"
                }
            } else {
                warn "No se pudo actualizar — continuando con la version local"
            }
        } else {
            ok "Proyecto al dia"
        }
    }
} else {
    warn "git no disponible o no es un repositorio — se omite el auto-update"
}

Start-Sleep -Seconds 1
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────────
Write-Host "  Verificando requisitos..." -ForegroundColor White

# 1. Python (requiere 3.10+)
$PythonCmd = $null
foreach ($cmd in @("python", "python3")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]; $minor = [int]$Matches[2]
            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 10)) {
                ok "Python $major.$minor"
                $PythonCmd = $cmd
                break
            } else {
                warn "Python $major.$minor detectado — se requiere 3.10 o superior"
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
    } else { throw }
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
    if ($LASTEXITCODE -eq 0) { ok "Docker Compose v2 (integrado)"; $ComposeCmd = "docker compose" }
} catch {}
if ($null -eq $ComposeCmd) {
    try {
        $null = & docker-compose --version 2>&1
        if ($LASTEXITCODE -eq 0) { warn "Docker Compose v1 detectado — funciona, pero v2 es preferible"; $ComposeCmd = "docker-compose" }
    } catch {}
}
if ($null -eq $ComposeCmd) {
    warn "Docker Compose no encontrado — asegurate de tener Docker Desktop con Compose incluido"
}

# 5. Archivo .env — auto-crear desde .env.example si no existe
if (Test-Path ".env") {
    ok ".env presente"
} else {
    if (Test-Path ".env.example") {
        warn ".env no encontrado — creando desde .env.example..."
        Copy-Item ".env.example" ".env"
        ok ".env creado"
        Write-Host ""
        info "NOTA: Si usas el tunel Playit.gg, edita .env y agrega tu SECRET_KEY:"
        info "  notepad .env"
        Write-Host ""
    } else {
        warn ".env no encontrado — el tunel Playit.gg no funcionara"
        info "Copia .env.example como .env y agrega tu SECRET_KEY"
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

Start-Sleep -Seconds 1
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
$ReqHashFile  = ".\venv\.req_hash"

if (-not (Test-Path $VenvActivate)) {
    info "Creando entorno virtual..."
    & $PythonCmd -m venv venv
    if ($LASTEXITCODE -ne 0) { fail "No se pudo crear el entorno virtual"; exit 1 }
    . $VenvActivate
    info "Instalando dependencias (primera vez)..."
    & pip install -q -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        ok "Dependencias instaladas"
        (Get-FileHash "requirements.txt" -Algorithm MD5).Hash | Set-Content $ReqHashFile
    } else {
        warn "Algunas dependencias no se instalaron correctamente"
    }
} else {
    . $VenvActivate
    ok "Entorno virtual activado"
    # Verificar si requirements.txt cambio
    $ReqHashNow = (Get-FileHash "requirements.txt" -Algorithm MD5).Hash
    $ReqHashOld = if (Test-Path $ReqHashFile) { Get-Content $ReqHashFile } else { "" }
    if ($ReqHashNow -ne $ReqHashOld) {
        info "requirements.txt cambio — actualizando dependencias..."
        & pip install -q -r requirements.txt
        $ReqHashNow | Set-Content $ReqHashFile
        ok "Dependencias actualizadas"
    }
}

Start-Sleep -Seconds 1
Write-Host ""
Write-Host "  Lanzando MC Manager..." -ForegroundColor White
Write-Host ""
Start-Sleep -Seconds 2

& python app.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    fail "La aplicacion termino con error (codigo $LASTEXITCODE)"
    Read-Host "  Presiona Enter para salir"
}
