#!/usr/bin/env bash
# setup.sh — One-command setup for the download engine
# Installs Python deps, Deno, PO token provider, manages the server
# Usage:
#   ./setup.sh              # full setup + start PO token server
#   ./setup.sh --no-server  # full setup, skip starting the server
#   ./setup.sh --start-server   # start the PO token server only
#   ./setup.sh --stop-server    # stop the PO token server
#   ./setup.sh --status         # check if server is running
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PO_TOKEN_DIR="$HOME/bgutil-ytdlp-pot-provider"
PORT=4416
START_SERVER=true
ACTION=""

# Deno is installed to ~/.deno/bin. Login bash sources ~/.deno/env via
# .bashrc/.profile, but interactive zsh (and this script) often do not.
export DENO_INSTALL="${DENO_INSTALL:-$HOME/.deno}"
export PATH="$DENO_INSTALL/bin:$PATH"

ensure_deno() {
    if command -v deno >/dev/null 2>&1; then
        return 0
    fi
    if [ -x "$DENO_INSTALL/bin/deno" ]; then
        export PATH="$DENO_INSTALL/bin:$PATH"
        return 0
    fi
    echo "⚠️  deno not found. Install it, or add this to ~/.zshrc:"
    echo "   export PATH=\"\$HOME/.deno/bin:\$PATH\""
    return 1
}

# Parse args
for arg in "$@"; do
    case $arg in
        --no-server)     START_SERVER=false ;;
        --start-server)  ACTION="start"; START_SERVER=false ;;
        --stop-server)   ACTION="stop"; START_SERVER=false ;;
        --status)        ACTION="status"; START_SERVER=false ;;
        *) echo "Unknown arg: $arg" ;;
    esac
done

echo "=== Download Engine Setup ==="

# ── Handle server management actions ──────────────────────────────────────────
if [ -n "$ACTION" ]; then
    case $ACTION in
        start)
            echo "→ Starting PO token server on 127.0.0.1:$PORT..."
            if [ ! -f "$PO_TOKEN_DIR/server/src/main.ts" ]; then
                echo "⚠️  PO token provider missing at $PO_TOKEN_DIR"
                echo "  Run: ./setup.sh --no-server"
                exit 1
            fi
            if ! ensure_deno; then
                exit 1
            fi
            if curl -sf "http://127.0.0.1:$PORT/ping" >/dev/null 2>&1; then
                echo "→ PO token server is already running."
            else
                LOG_FILE="${TMPDIR:-/tmp}/bgutil-pot-${PORT}.log"
                (cd "$PO_TOKEN_DIR/server" && deno run --allow-env --allow-net --allow-ffi=. --allow-read=. \
                    src/main.ts --port $PORT >"$LOG_FILE" 2>&1) &
                SERVER_PID=$!
                for i in $(seq 1 10); do
                    if curl -sf "http://127.0.0.1:$PORT/ping" >/dev/null 2>&1; then
                        echo "→ PO token server started (PID: $SERVER_PID)."
                        break
                    fi
                    sleep 1
                done
                if ! curl -sf "http://127.0.0.1:$PORT/ping" >/dev/null 2>&1; then
                    echo "⚠️  PO token server failed to start."
                    echo "  deno: $(command -v deno || echo missing)"
                    echo "  provider: $PO_TOKEN_DIR"
                    echo "  log: $LOG_FILE"
                    if [ -f "$LOG_FILE" ]; then
                        echo "  --- last log lines ---"
                        tail -n 20 "$LOG_FILE" || true
                    fi
                    exit 1
                fi
            fi
            ;;
        stop)
            if curl -sf "http://127.0.0.1:$PORT/ping" >/dev/null 2>&1; then
                echo "→ Stopping PO token server..."
                fuser -k $PORT/tcp 2>/dev/null || true
                echo "→ PO token server stopped."
            else
                echo "→ PO token server is not running."
            fi
            ;;
        status)
            if curl -sf "http://127.0.0.1:$PORT/ping" >/dev/null 2>&1; then
                echo "→ PO token server is running on port $PORT."
                curl -s "http://127.0.0.1:$PORT/ping"
                echo ""
            else
                echo "→ PO token server is NOT running."
                if ! command -v deno >/dev/null 2>&1; then
                    echo "  Note: deno is not on PATH (expected at \$HOME/.deno/bin)."
                fi
            fi
            ;;
    esac
    exit 0
fi

# ── Full setup ────────────────────────────────────────────────────────────────
cd "$SCRIPT_DIR"

# ── 1. Python virtual environment ──────────────────────────────────────────────
if [ ! -d "env" ]; then
    echo "→ Creating Python virtual environment..."
    python3 -m venv env
else
    echo "→ Virtual environment already exists."
fi

source env/bin/activate
echo "→ Installing Python packages..."
pip install -q -r requirements.txt

# ── 2. PO Token Provider plugin ────────────────────────────────────────────────
echo "→ Installing PO token provider plugin..."
pip install -q bgutil-ytdlp-pot-provider

# ── 3. Deno (for PO token JS challenge solving) ──────────────────────────────
if ! ensure_deno; then
    echo "→ Installing Deno..."
    curl -fsSL https://deno.land/install.sh | sh -s v2.9.5
    export DENO_INSTALL="$HOME/.deno"
    export PATH="$DENO_INSTALL/bin:$PATH"
fi
if ! ensure_deno; then
    echo "⚠️  Deno install failed."
    exit 1
fi
echo "→ Deno: $(command -v deno) ($(deno --version | head -n1))"

# ── 4. PO Token Provider Server (bgutil) ───────────────────────────────────────
if [ ! -d "$PO_TOKEN_DIR" ]; then
    echo "→ Cloning PO token provider server..."
    git clone --depth 1 --branch 1.3.2 \
        https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git \
        "$PO_TOKEN_DIR"
fi

echo "→ Setting up PO token provider (Deno deps)..."
cd "$PO_TOKEN_DIR/server"
deno install --allow-scripts=npm:canvas --frozen
cd "$SCRIPT_DIR"

# ── 5. FFmpeg (required by yt-dlp for merging) ─────────────────────────────────
if ! command -v ffmpeg &>/dev/null; then
    echo "→ FFmpeg not found. Installing..."
    if command -v apt &>/dev/null; then
        sudo apt update && sudo apt install -y ffmpeg
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm ffmpeg
    elif command -v brew &>/dev/null; then
        brew install ffmpeg
    else
        echo "⚠️  Please install FFmpeg manually: https://ffmpeg.org/download.html"
    fi
else
    echo "→ FFmpeg already installed."
fi

# ── 6. Start PO token server (background, localhost only) ──────────────────────
if [ "$START_SERVER" = true ]; then
    echo "→ Starting PO token server on 127.0.0.1:$PORT (localhost only)..."

    # Check if already running
    if curl -sf "http://127.0.0.1:$PORT/ping" >/dev/null 2>&1; then
        echo "→ PO token server is already running."
    else
        (cd "$PO_TOKEN_DIR/server" && deno run --allow-env --allow-net --allow-ffi=. --allow-read=. \
            src/main.ts --port $PORT >/dev/null 2>&1) &
        SERVER_PID=$!
        # Wait for server to be ready (up to 10 seconds)
        for i in $(seq 1 10); do
            if curl -sf "http://127.0.0.1:$PORT/ping" >/dev/null 2>&1; then
                echo "→ PO token server started (PID: $SERVER_PID)."
                break
            fi
            sleep 1
        done
        # Final check
        if ! curl -sf "http://127.0.0.1:$PORT/ping" >/dev/null 2>&1; then
            echo "⚠️  PO token server failed to start. You can try starting it manually:"
            echo "   ./setup.sh --start-server"
        fi
    fi
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Download high-quality YouTube videos:"
echo "  python yt_download.py -u \"URL\" -q 1440p --browser brave"
echo ""
echo "Server management:"
echo "  ./setup.sh --start-server    # start the PO token server"
echo "  ./setup.sh --stop-server     # stop the PO token server"
echo "  ./setup.sh --status          # check server status"
