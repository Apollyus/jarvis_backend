# Průvodce nasazením pomocí Dockeru

Tento průvodce vysvětluje, jak sestavit, spustit a nasadit Jarvis Backend API pomocí Dockeru.

## Požadavky

- Docker Engine 20.10 nebo vyšší
- Docker Compose 1.29 nebo vyšší
- VPS s nainstalovaným Dockerem (pro nasazení)

## Rychlý start

### 1. Lokální vývoj

```bash
# Build and start the container
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

API bude dostupné na `http://localhost:8000`

### 2. Proměnné prostředí

Vytvořte soubor `.env` v kořenovém adresáři projektu s následujícími proměnnými:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
NOTION_API_KEY=your_notion_api_key_here

# API Authentication
# Generate a secure API key: https://www.uuidgenerator.net/ or use: python -c "import secrets; print(secrets.token_urlsafe(32))"
API_KEY=xxx

# Optional: Multiple API keys (comma-separated)
# API_KEYS=key1,key2,key3

# User Login Credentials (for /api/auth/login endpoint)
# Username and password for generating API keys via login
USERNAME=admin
PASSWORD=your_secure_password_here
```

**⚠️ DŮLEŽITÉ**: Nikdy necommitujte soubor `.env` do verzovacího systému. Obsahuje citlivé přihlašovací údaje.

## Sestavení Docker image

### Build pomocí Dockeru

```bash
docker build -t jarvis-backend:latest .
```

### Build pomocí Docker Compose

```bash
docker-compose build
```

## Spuštění kontejneru

### Použití Docker Compose (doporučeno)

```bash
# Start the service
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f jarvis-backend

# Stop the service
docker-compose down

# Restart the service
docker-compose restart
```

### Použití Docker CLI

```bash
# Run the container
docker run -d \
  --name jarvis-backend \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  jarvis-backend:latest

# View logs
docker logs -f jarvis-backend

# Stop the container
docker stop jarvis-backend

# Remove the container
docker rm jarvis-backend
```

## Nasazení na VPS

### Možnost 1: Nasazení pomocí Docker Compose (doporučeno)

1. **Připojte se k VPS:**
   ```bash
   ssh user@your-vps-ip
   ```

2. **Nainstalujte Docker a Docker Compose** (pokud ještě nejsou nainstalované):
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   
   # Add your user to docker group (optional)
   sudo usermod -aG docker $USER
   ```

3. **Naklonujte nebo nahrajte projekt:**
   ```bash
   git clone https://github.com/Apollyus/jarvis_backend.git
   cd jarvis_backend
   ```

4. **Vytvořte a nakonfigurujte soubor .env:**
   ```bash
   nano .env
   # Add your environment variables
   ```

5. **Sestavte a spusťte službu:**
   ```bash
   docker-compose up -d --build
   ```

6. **Ověřte nasazení:**
   ```bash
   # Check container status
   docker-compose ps
   
   # View logs
   docker-compose logs -f
   
   # Test the API
   curl http://localhost:8000/health
   ```

### Možnost 2: Manuální nasazení pomocí Dockeru

1. **Sestavte image na VPS:**
   ```bash
   docker build -t jarvis-backend:latest .
   ```

2. **Spusťte kontejner:**
   ```bash
   docker run -d \
     --name jarvis-backend \
     -p 8000:8000 \
     --env-file .env \
     --restart unless-stopped \
     jarvis-backend:latest
   ```

### Možnost 3: Nasazení pomocí Docker registru

Tento přístup umožňuje sestavit Docker image lokálně a nahrát ji do veřejného nebo soukromého registru (Docker Hub, GitHub Container Registry, atd.), odkud ji pak můžete stáhnout a spustit na VPS.

#### A) Nasazení přes Docker Hub

1. **Přihlaste se k Docker Hubu:**
   ```bash
   docker login
   # Zadejte své Docker Hub přihlašovací údaje
   ```

2. **Sestavte image s vhodným tagem:**
   ```bash
   # Nahraďte 'vase-uzivatelske-jmeno' vaším Docker Hub uživatelským jménem
   docker build -t vase-uzivatelske-jmeno/jarvis-backend:latest .
   
   # Pro verzované image použijte tag s číslem verze
   docker build -t vase-uzivatelske-jmeno/jarvis-backend:v1.0.0 .
   ```

3. **Nahrajte image do Docker Hubu:**
   ```bash
   # Nahrát nejnovější verzi
   docker push vase-uzivatelske-jmeno/jarvis-backend:latest
   
   # Nahrát konkrétní verzi
   docker push vase-uzivatelske-jmeno/jarvis-backend:v1.0.0
   ```

4. **Na VPS se přihlaste k Docker Hubu:**
   ```bash
   ssh user@your-vps-ip
   docker login
   ```

5. **Stáhněte image na VPS:**
   ```bash
   docker pull vase-uzivatelske-jmeno/jarvis-backend:latest
   ```

6. **Vytvořte soubor .env na VPS:**
   ```bash
   nano .env
   # Přidejte všechny požadované proměnné prostředí
   ```

7. **Spusťte kontejner na VPS:**
   ```bash
   docker run -d \
     --name jarvis-backend \
     -p 8000:8000 \
     --env-file .env \
     --restart unless-stopped \
     vase-uzivatelske-jmeno/jarvis-backend:latest
   ```

8. **Ověřte nasazení:**
   ```bash
   # Zkontrolujte stav kontejneru
   docker ps
   
   # Zobrazit logy
   docker logs -f jarvis-backend
   
   # Otestujte API
   curl http://localhost:8000/health
   ```

#### B) Nasazení přes GitHub Container Registry (ghcr.io)

1. **Vytvořte Personal Access Token (PAT) na GitHubu:**
   - Jděte na GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Vytvořte nový token s oprávněními: `write:packages`, `read:packages`, `delete:packages`
   - Uložte si token bezpečně

2. **Přihlaste se k GitHub Container Registry:**
   ```bash
   # Použijte váš GitHub username a vytvořený PAT
   echo "YOUR_GITHUB_PAT" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
   ```

3. **Sestavte image s GitHub Container Registry tagem:**
   ```bash
   # Nahraďte 'your-github-username' vaším GitHub uživatelským jménem
   docker build -t ghcr.io/your-github-username/jarvis-backend:latest .
   
   # Pro verzované image
   docker build -t ghcr.io/your-github-username/jarvis-backend:v1.0.0 .
   ```

4. **Nahrajte image do GitHub Container Registry:**
   ```bash
   # Nahrát nejnovější verzi
   docker push ghcr.io/your-github-username/jarvis-backend:latest
   
   # Nahrát konkrétní verzi
   docker push ghcr.io/your-github-username/jarvis-backend:v1.0.0
   ```

5. **Nastavte viditelnost balíčku (volitelné):**
   - Jděte na GitHub → Your profile → Packages
   - Vyberte `jarvis-backend`
   - Package settings → Change visibility (Public/Private)

6. **Na VPS se přihlaste k GitHub Container Registry:**
   ```bash
   ssh user@your-vps-ip
   echo "YOUR_GITHUB_PAT" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
   ```

7. **Stáhněte image na VPS:**
   ```bash
   docker pull ghcr.io/your-github-username/jarvis-backend:latest
   ```

8. **Vytvořte soubor .env na VPS:**
   ```bash
   nano .env
   # Přidejte všechny požadované proměnné prostředí
   ```

9. **Spusťte kontejner na VPS:**
   ```bash
   docker run -d \
     --name jarvis-backend \
     -p 8000:8000 \
     --env-file .env \
     --restart unless-stopped \
     ghcr.io/your-github-username/jarvis-backend:latest
   ```

10. **Ověřte nasazení:**
    ```bash
    # Zkontrolujte stav kontejneru
    docker ps
    
    # Zobrazit logy
    docker logs -f jarvis-backend
    
    # Otestujte API
    curl http://localhost:8000/health
    ```

#### Aktualizace aplikace přes registr

Když potřebujete aktualizovat aplikaci na VPS:

```bash
# 1. Na lokálním stroji: Sestavte a nahrajte novou verzi
docker build -t vase-uzivatelske-jmeno/jarvis-backend:v1.0.1 .
docker push vase-uzivatelske-jmeno/jarvis-backend:v1.0.1

# Označte také jako latest
docker tag vase-uzivatelske-jmeno/jarvis-backend:v1.0.1 vase-uzivatelske-jmeno/jarvis-backend:latest
docker push vase-uzivatelske-jmeno/jarvis-backend:latest

# 2. Na VPS: Zastavte a odstraňte starý kontejner
ssh user@your-vps-ip
docker stop jarvis-backend
docker rm jarvis-backend

# 3. Stáhněte novou verzi
docker pull vase-uzivatelske-jmeno/jarvis-backend:latest

# 4. Spusťte nový kontejner
docker run -d \
  --name jarvis-backend \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  vase-uzivatelske-jmeno/jarvis-backend:latest

# 5. Ověřte, že nová verze běží
docker logs -f jarvis-backend
```

#### Tipy pro práci s registry

- **Verzování**: Vždy používejte konkrétní verze tagů (např. `v1.0.0`) vedle `latest` pro lepší sledovatelnost
- **Bezpečnost**: Pro privátní projekty používejte soukromé registry nebo soukromé repositáře
- **Úklid**: Pravidelně mažte staré, nepoužívané image z registry
- **CI/CD**: Zvažte automatizaci buildu a push procesu pomocí GitHub Actions nebo jiných CI/CD nástrojů
- **Multi-arch**: Pro podporu různých architektur (ARM, x86) použijte `docker buildx` s multi-platform builds

#### Automatizace s Docker Compose a registry

Můžete také použít Docker Compose s image z registry:

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  jarvis-backend:
    image: vase-uzivatelske-jmeno/jarvis-backend:latest
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

Nasazení na VPS:

```bash
# Stáhněte docker-compose.prod.yml na VPS
scp docker-compose.prod.yml user@your-vps-ip:~/

# Na VPS
ssh user@your-vps-ip
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Správa kontejneru

### Zobrazení stavu kontejneru
```bash
docker-compose ps
# or
docker ps -a
```

### Zobrazení logů
```bash
# All logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100
```

### Spuštění příkazů v kontejneru
```bash
# Interactive shell
docker-compose exec jarvis-backend /bin/bash

# Run a specific command
docker-compose exec jarvis-backend python -c "print('Hello')"
```

### Aktualizace aplikace
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build

# Or force recreate
docker-compose up -d --force-recreate --build
```

### Zastavení a odstranění všeho
```bash
# Stop containers
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop and remove everything including images
docker-compose down --rmi all -v
```

## Health Checks

Kontejner obsahuje kontroly stavu, které monitorují endpoint `/health`.

Zkontrolujte stav kontejneru:
```bash
docker inspect --format='{{.State.Health.Status}}' jarvis-backend
```

## Řešení problémů

### Kontejner se nespustí

1. **Zkontrolujte logy:**
   ```bash
   docker-compose logs jarvis-backend
   ```

2. **Ověřte proměnné prostředí:**
   ```bash
   docker-compose config
   ```

3. **Zkontrolujte, zda port 8000 není již používán:**
   ```bash
   sudo lsof -i :8000
   # or
   sudo netstat -tulpn | grep 8000
   ```

### Chyby aplikace

1. **Zkontrolujte logy aplikace:**
   ```bash
   docker-compose logs -f jarvis-backend
   ```

2. **Ověřte, že soubor .env existuje a obsahuje požadované proměnné**

3. **Otestujte health endpoint:**
   ```bash
   curl http://localhost:8000/health
   ```

### Problémy s oprávněními

Pokud narazíte na chyby oprávnění:
```bash
# Add your user to the docker group
sudo usermod -aG docker $USER

# Log out and back in for changes to take effect
```

## Optimalizace výkonu

### Limity prostředků

Přidejte limity prostředků do [`docker-compose.yml`](../docker-compose.yml:1):

```yaml
services:
  jarvis-backend:
    # ... existing configuration ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Produkční optimalizace

Pro produkční nasazení:

1. Použijte multi-stage builds (již optimalizováno v Dockerfile)
2. Spouštějte jako non-root uživatel (již nakonfigurováno)
3. Aktivujte health checks (již nakonfigurováno)
4. Použijte restart policies (již nakonfigurováno)
5. Monitorujte logy a metriky
6. Pravidelné zálohy konfigurace prostředí

## API Endpointy

Po nasazení jsou dostupné následující endpointy:

- `GET /` - Kořenový endpoint
- `GET /health` - Kontrola stavu
- `GET /docs` - API dokumentace (Swagger UI)
- `POST /api/chat` - REST chat endpoint
- `WS /ws/chat` - WebSocket chat endpoint
- `GET /api/chat/stream` - Server-Sent Events chat

## Bezpečnostní poznámky

1. **Nikdy necommitujte soubor `.env`** - Je již v `.gitignore` a `.dockerignore`
2. **Použijte správu secrets** pro produkci (Docker Secrets, HashiCorp Vault, atd.)
3. **Udržujte Docker images aktuální** - Pravidelně přestavujte s nejnovějšími base images
4. **Aktivujte firewall** na VPS a vystavte pouze potřebné porty
5. **Používejte HTTPS** v produkci s SSL/TLS certifikáty
6. **Implementujte rate limiting** pokud vystavujete na veřejný internet
7. **Pravidelné bezpečnostní aktualizace** - Udržujte VPS a Docker aktuální

## Podpora

Pro problémy nebo dotazy:
- Zkontrolujte logy aplikace: `docker-compose logs -f`
- Přečtěte si hlavní API dokumentaci: [`README_API.md`](README_API.md:1)
- Zkontrolujte Docker dokumentaci: https://docs.docker.com/

## Licence


Stejná jako hlavní projekt.

