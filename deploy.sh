#!/bin/bash
set -e

echo "🚀 ARA Radar v2.0 - Deployment Script"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if environment variables are set
check_env() {
    echo "📋 Checking environment variables..."

    if [ -f backend/.env ]; then
        echo -e "${GREEN}✓${NC} Backend .env found"
    else
        echo -e "${YELLOW}⚠${NC}  Backend .env not found. Creating from example..."
        cp backend/.env.example backend/.env
        echo -e "${YELLOW}⚠${NC}  Please edit backend/.env with your credentials"
        exit 1
    fi

    if [ -f frontend/.env.local ]; then
        echo -e "${GREEN}✓${NC} Frontend .env.local found"
    else
        echo -e "${YELLOW}⚠${NC}  Frontend .env.local not found. Creating from example..."
        cp frontend/.env.example frontend/.env.local
        echo -e "${YELLOW}⚠${NC}  Please edit frontend/.env.local with your credentials"
        exit 1
    fi
}

# Build frontend
build_frontend() {
    echo ""
    echo "🔨 Building frontend..."
    cd frontend

    if [ ! -d "node_modules" ]; then
        echo "📦 Installing dependencies..."
        npm install --legacy-peer-deps
    fi

    echo "🏗️  Building Next.js..."
    npm run build

    echo -e "${GREEN}✓${NC} Frontend build successful"
    cd ..
}

# Test backend
test_backend() {
    echo ""
    echo "🧪 Testing backend..."
    cd backend

    echo "📦 Installing Python dependencies..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    source venv/bin/activate
    pip install -q -r requirements_prod.txt

    echo "🚀 Starting test server..."
    timeout 10s uvicorn app:app --host 127.0.0.1 --port 8001 &
    SERVER_PID=$!

    sleep 5

    echo "🔍 Testing /health endpoint..."
    if curl -s http://127.0.0.1:8001/health | grep -q "ok"; then
        echo -e "${GREEN}✓${NC} Backend health check passed"
        kill $SERVER_PID 2>/dev/null || true
    else
        echo -e "${RED}✗${NC} Backend health check failed"
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi

    deactivate
    cd ..
}

# Deploy to Fly.io
deploy_fly() {
    echo ""
    echo "🛫 Deploying to Fly.io..."

    if ! command -v fly &> /dev/null; then
        echo -e "${RED}✗${NC} Fly CLI not installed"
        echo "Install: curl -L https://fly.io/install.sh | sh"
        exit 1
    fi

    cd backend

    echo "🔐 Setting secrets..."
    fly secrets set \
        SUPABASE_URL="$SUPABASE_URL" \
        SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
        --app ara-radar-backend 2>/dev/null || true

    echo "🚀 Deploying..."
    fly deploy --app ara-radar-backend

    echo -e "${GREEN}✓${NC} Backend deployed to Fly.io"
    BACKEND_URL=$(fly status --app ara-radar-backend | grep "Hostname" | awk '{print $3}')
    echo "Backend URL: https://$BACKEND_URL"

    cd ..
}

# Deploy to Netlify
deploy_netlify() {
    echo ""
    echo "🌐 Deploying to Netlify..."

    if ! command -v netlify &> /dev/null; then
        echo -e "${YELLOW}⚠${NC}  Netlify CLI not installed"
        echo "Install: npm install -g netlify-cli"
        echo "Or deploy via Netlify dashboard: https://app.netlify.com"
        return
    fi

    cd frontend

    echo "🚀 Deploying..."
    netlify deploy --prod

    echo -e "${GREEN}✓${NC} Frontend deployed to Netlify"
    cd ..
}

# Main menu
main() {
    check_env

    echo ""
    echo "Select deployment option:"
    echo "1. Build frontend only"
    echo "2. Test backend locally"
    echo "3. Deploy backend to Fly.io"
    echo "4. Deploy frontend to Netlify"
    echo "5. Full deployment (Fly.io + Netlify)"
    echo "6. Exit"
    echo ""
    read -p "Enter option (1-6): " option

    case $option in
        1)
            build_frontend
            ;;
        2)
            test_backend
            ;;
        3)
            deploy_fly
            ;;
        4)
            build_frontend
            deploy_netlify
            ;;
        5)
            build_frontend
            test_backend
            deploy_fly
            deploy_netlify
            ;;
        6)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo -e "${RED}✗${NC} Invalid option"
            exit 1
            ;;
    esac

    echo ""
    echo -e "${GREEN}✨ Deployment complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Test backend: curl https://ara-radar-backend.fly.dev/health"
    echo "2. Visit frontend: Check Netlify dashboard for URL"
    echo "3. Test ingest: Go to /ingest and upload data"
    echo "4. Monitor: fly logs (backend) & Netlify logs (frontend)"
}

main
