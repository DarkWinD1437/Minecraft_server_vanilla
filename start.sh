#!/usr/bin/env bash
# MC Server Manager — Launcher para Linux/macOS
# Uso: bash start.sh   (o chmod +x start.sh && ./start.sh)

# ── Colores ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "  ${GREEN}✔${NC}  $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC}  $1"; }
fail() { echo -e "  ${RED}✘${NC}  $1"; }
info() { echo -e "  ${CYAN}→${NC}  $1"; }

echo -e "${BOLD}"
echo "  ╔══════════════════════════════════════╗"
echo "  ║    MC Server Manager — DarkWinD      ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "${NC}"

# ── Posicionarse en la carpeta del proyecto ──────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ERRORES=0

# ── Auto-actualización desde git ──────────────────────────────────────────────
echo -e "${BOLD}Verificando actualizaciones...${NC}"

if command -v git &>/dev/null && git rev-parse --is-inside-work-tree &>/dev/null 2>&1; then
    # Ignorar archivos sin seguimiento; contar solo cambios en archivos tracked
    LOCAL_CHANGES=$(git status --porcelain 2>/dev/null | grep -v '^??' | wc -l | tr -d ' ')
    if [ "$LOCAL_CHANGES" -gt 0 ]; then
        warn "Hay cambios locales sin commit — se omite el auto-update"
    else
        git fetch origin --quiet 2>/dev/null || true
        LOCAL=$(git rev-parse HEAD 2>/dev/null)
        REMOTE=$(git rev-parse "@{u}" 2>/dev/null || echo "")

        if [ -n "$REMOTE" ] && [ "$LOCAL" != "$REMOTE" ]; then
            info "Commits nuevos disponibles:"
            git log HEAD..@{u} --oneline 2>/dev/null | while IFS= read -r line; do
                echo -e "      ${CYAN}•${NC} $line"
            done
            git pull --quiet 2>/dev/null && ok "Proyecto actualizado" || warn "No se pudo actualizar — continuando con la versión local"
        else
            ok "Proyecto al día"
        fi
    fi
else
    warn "git no disponible o no es un repositorio — se omite el auto-update"
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BOLD}Verificando requisitos...${NC}"

# 1. Python3
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PY_MIN=$(python3 -c 'import sys; print(1 if sys.version_info >= (3,10) else 0)')
    if [ "$PY_MIN" = "1" ]; then
        ok "Python $PY_VER"
    else
        warn "Python $PY_VER detectado — se requiere 3.10 o superior"
        ERRORES=$((ERRORES + 1))
    fi
else
    fail "Python3 no encontrado"
    info "Instala con: sudo apt install python3 python3-venv"
    ERRORES=$((ERRORES + 1))
fi

# 2. python3-venv disponible
if python3 -m venv --help &>/dev/null 2>&1; then
    ok "python3-venv disponible"
else
    fail "python3-venv no encontrado"
    info "Instala con: sudo apt install python3-venv"
    ERRORES=$((ERRORES + 1))
fi

# 3. Docker instalado
if command -v docker &>/dev/null; then
    DOCKER_VER=$(docker --version | awk '{print $3}' | tr -d ',')
    ok "Docker $DOCKER_VER"
else
    fail "Docker no instalado"
    info "Instala con: curl -fsSL https://get.docker.com | sudo sh"
    ERRORES=$((ERRORES + 1))
fi

# 4. Docker daemon activo
if docker info &>/dev/null 2>&1; then
    ok "Docker daemon activo"
else
    warn "Docker daemon no está corriendo"
    info "Inicia con: sudo systemctl start docker"
    info "  (te pedirá tu contraseña de usuario — es normal en Linux)"
    warn "El manager abrirá, pero los controles del servidor no funcionarán"
fi

# 5. Docker Compose
if docker compose version &>/dev/null 2>&1; then
    ok "Docker Compose v2 (integrado)"
elif command -v docker-compose &>/dev/null; then
    warn "Docker Compose v1 detectado — funciona, pero v2 es preferible"
else
    warn "Docker Compose no encontrado"
    info "Instala con: sudo apt install docker-compose-plugin"
fi

# 6. Archivo .env — auto-crear desde .env.example si no existe
if [ -f ".env" ]; then
    ok ".env presente"
else
    if [ -f ".env.example" ]; then
        warn ".env no encontrado — creando desde .env.example..."
        cp .env.example .env
        ok ".env creado"
        echo ""
        info "NOTA: Si usas el túnel Playit.gg, edita .env y añade tu SECRET_KEY:"
        info "  nano .env"
        echo ""
    else
        warn ".env no encontrado — el túnel Playit.gg no funcionará"
    fi
fi

# 7. docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    ok "docker-compose.yml presente"
else
    fail "docker-compose.yml no encontrado — el servidor no puede levantarse"
    ERRORES=$((ERRORES + 1))
fi

# 8. Carpeta datos_mc
if [ -d "datos_mc" ]; then
    ok "datos_mc/ presente"
else
    warn "datos_mc/ no existe — se creará la primera vez que levantes el servidor"
fi

echo ""

# ── Abortar si hay errores críticos ──────────────────────────────────────────
if [ "$ERRORES" -gt 0 ]; then
    echo -e "${RED}${BOLD}  $ERRORES problema(s) crítico(s). Corrígelos antes de continuar.${NC}"
    echo ""
    exit 1
fi

# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BOLD}Preparando entorno Python...${NC}"

if [ ! -f "venv/bin/activate" ]; then
    info "Creando entorno virtual..."
    python3 -m venv venv
    source venv/bin/activate
    info "Instalando dependencias (primera vez)..."
    pip install -q -r requirements.txt
    ok "Dependencias instaladas"
else
    source venv/bin/activate
    ok "Entorno virtual activado"
    # Verificar si requirements.txt cambió desde la última instalación
    REQ_HASH_FILE="venv/.req_hash"
    REQ_HASH_NOW=$(md5sum requirements.txt 2>/dev/null | awk '{print $1}')
    REQ_HASH_OLD=$(cat "$REQ_HASH_FILE" 2>/dev/null || echo "")
    if [ "$REQ_HASH_NOW" != "$REQ_HASH_OLD" ]; then
        info "requirements.txt cambió — actualizando dependencias..."
        pip install -q -r requirements.txt
        echo "$REQ_HASH_NOW" > "$REQ_HASH_FILE"
        ok "Dependencias actualizadas"
    fi
fi

echo ""
echo -e "${BOLD}  Lanzando MC Manager...${NC}"
echo ""

exec python3 app.py
