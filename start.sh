#!/usr/bin/env bash
set -e

# ── Colores ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "  ${GREEN}✔${NC}  $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC}  $1"; }
fail() { echo -e "  ${RED}✘${NC}  $1"; }
info() { echo -e "  ${CYAN}→${NC}  $1"; }

echo -e "${BOLD}"
echo "  ╔══════════════════════════════════════╗"
echo "  ║       MC Server Manager v1.0         ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "${NC}"

# ── Posicionarse en la carpeta del proyecto ──────────────────────────────────
# Funciona sin importar desde qué directorio se llame al script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ERRORES=0

# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BOLD}Verificando requisitos...${NC}"

# 1. Python3
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PY_MIN=$(python3 -c 'import sys; print(1 if sys.version_info >= (3,8) else 0)')
    if [ "$PY_MIN" = "1" ]; then
        ok "Python $PY_VER"
    else
        warn "Python $PY_VER detectado — se requiere 3.8 o superior"
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
    info "Visita: https://docs.docker.com/engine/install/ubuntu/"
    ERRORES=$((ERRORES + 1))
fi

# 4. Docker daemon activo
if docker info &>/dev/null 2>&1; then
    ok "Docker daemon activo"
else
    warn "Docker daemon no está corriendo"
    info "Inicia con: sudo systemctl start docker"
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

# 6. Archivo .env
if [ -f ".env" ]; then
    ok ".env presente"
else
    warn ".env no encontrado — el túnel Playit.gg no funcionará"
    info "Copia .env.example como .env y añade tu PLAYIT_SECRET"
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
    warn "datos_mc/ no existe — se creará cuando levantes el servidor por primera vez"
fi

echo ""

# ── Abortar si hay errores críticos ──────────────────────────────────────────
if [ "$ERRORES" -gt 0 ]; then
    echo -e "${RED}${BOLD}  $ERRORES problema(s) crítico(s). Corrígelos antes de continuar.${NC}"
    exit 1
fi

# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BOLD}Preparando entorno Python...${NC}"

if [ ! -f "venv/bin/activate" ]; then
    info "Creando entorno virtual..."
    python3 -m venv venv
    source venv/bin/activate
    info "Instalando dependencias..."
    pip install -q -r requirements.txt
    ok "Dependencias instaladas"
else
    source venv/bin/activate
    ok "Entorno virtual activado"
fi

echo ""
echo -e "${BOLD}  Lanzando MC Manager...${NC}"
echo ""

exec python app.py
