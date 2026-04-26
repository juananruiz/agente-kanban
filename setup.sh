#!/bin/bash
set -e

cd "$(dirname "$0")"

echo ""
echo "  📦 Agente Kanban — Setup"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "  ❌ Python 3 no encontrado. Instálalo primero."
    exit 1
fi

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "  🔧 Creando entorno virtual..."
    python3 -m venv venv
    echo "  ✅ Entorno virtual creado"
else
    echo "  ℹ️  Entorno virtual ya existe"
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "  📥 Instalando dependencias..."
pip install -r requirements.txt -q
echo "  ✅ Dependencias instaladas"

echo ""
echo "  ✨ ¡Listo! Ahora puedes hacer:"
echo ""
echo "     ./server.sh   (en una terminal)"
echo "     ./watcher.sh  (en otra terminal)"
echo ""
echo "     http://localhost:3000"
echo ""
