# 🚀 Deployment Guide - Jak nasadit na server

## 📋 Přehled

Tento projekt používá Docker a Docker Compose. Máme dva režimy:

- **Development** (lokální): `docker-compose.yml` - builduje image lokálně
- **Production** (server): `docker-compose.prod.yml` - stahuje image z Docker Hub

## 🏗️ Postup nasazení na server

### 1. Příprava na lokálním počítači

```powershell
# Build a push image na Docker Hub
docker build -t user2106874/jarvis-backend:latest .
docker push user2106874/jarvis-backend:latest
```

### 2. Na serveru - Příprava

```bash
# Vytvořte adresář pro projekt
mkdir -p ~/jarvis-backend
cd ~/jarvis-backend

# Stáhněte potřebné soubory z repozitáře
wget https://raw.githubusercontent.com/Apollyus/jarvis_backend/main/docker-compose.prod.yml
wget https://raw.githubusercontent.com/Apollyus/jarvis_backend/main/.env.example

# Nebo pomocí git clone
git clone https://github.com/Apollyus/jarvis_backend.git
cd jarvis_backend
```

### 3. Konfigurace .env souboru

```bash
# Zkopírujte .env.example a vyplňte vaše credentials
cp .env.example .env
nano .env  # nebo vim, vi, atd.
```

Vyplňte následující proměnné:
```env
OPENROUTER_API_KEY=your_openrouter_api_key
NOTION_API_KEY=your_notion_api_key
API_KEY=your_jarvis_api_key
USERNAME=your_username
PASSWORD=your_password
```

### 4. Spuštění na serveru

```bash
# Stáhněte nejnovější image z Docker Hub
docker-compose -f docker-compose.prod.yml pull

# Spusťte aplikaci (pozadí)
docker-compose -f docker-compose.prod.yml up -d

# Sledujte logy
docker-compose -f docker-compose.prod.yml logs -f
```

## 📊 Užitečné příkazy

### Kontrola stavu
```bash
# Zobrazí běžící kontejnery
docker-compose -f docker-compose.prod.yml ps

# Zobrazí logy
docker-compose -f docker-compose.prod.yml logs

# Sleduje logy v reálném čase
docker-compose -f docker-compose.prod.yml logs -f jarvis-backend
```

### Restart aplikace
```bash
# Restart všech služeb
docker-compose -f docker-compose.prod.yml restart

# Restart jen backendu
docker-compose -f docker-compose.prod.yml restart jarvis-backend
```

### Zastavení a odstranění
```bash
# Zastaví kontejnery
docker-compose -f docker-compose.prod.yml stop

# Zastaví a odstraní kontejnery (data v Redis zůstanou)
docker-compose -f docker-compose.prod.yml down

# Zastaví, odstraní kontejnery a SMAŽE data
docker-compose -f docker-compose.prod.yml down -v
```

### Update na novou verzi
```bash
# 1. Stáhněte nejnovější image
docker-compose -f docker-compose.prod.yml pull

# 2. Restartujte s novou verzí
docker-compose -f docker-compose.prod.yml up -d

# 3. Sledujte logy
docker-compose -f docker-compose.prod.yml logs -f
```

## 🔧 Troubleshooting

### Redis connection refused
Pokud vidíte `Connection refused` pro Redis:
```bash
# Ujistěte se, že běží oba kontejnery
docker-compose -f docker-compose.prod.yml ps

# Zkontrolujte network
docker network ls
docker network inspect jarvis_backend_jarvis-network
```

### Port už je používán
```bash
# Zjistěte, co běží na portu 8000
netstat -tulpn | grep 8000

# Nebo změňte port v docker-compose.prod.yml
ports:
  - "8001:8000"  # External port 8001 -> Internal 8000
```

### Jak se dostat do kontejneru
```bash
# Shell v běžícím kontejneru
docker exec -it jarvis-backend /bin/bash

# Nebo pro rychlý příkaz
docker exec jarvis-backend python -c "import redis; print(redis.__version__)"
```

## 🏠 Lokální development

Pro lokální vývoj používejte standardní `docker-compose.yml`:

```powershell
# Spusť lokálně s buildem
docker-compose up --build

# Nebo jen spusť (bez buildu)
docker-compose up
```

## 🔐 Bezpečnost

- ⚠️ **NIKDY** necommitujte `.env` soubor do gitu!
- ✅ Používejte silná hesla v produkci
- ✅ Na produkčním serveru omezte přístup k portům (firewall)
- ✅ Pravidelně aktualizujte Docker image (`docker-compose pull`)

## 📝 Checklist pro deployment

- [ ] Build a push nového image na Docker Hub
- [ ] Na serveru: stáhněte `docker-compose.prod.yml`
- [ ] Vytvořte a vyplňte `.env` soubor
- [ ] Spusťte: `docker-compose -f docker-compose.prod.yml up -d`
- [ ] Zkontrolujte logy: `docker-compose -f docker-compose.prod.yml logs -f`
- [ ] Otestujte API: `curl http://localhost:8000/health`
- [ ] Upload Notion tokens (pokud potřebujete)

## 🌐 Přístup k API

Po spuštění bude API dostupné na:
- Lokálně: `http://localhost:8000`
- Na serveru: `http://your-server-ip:8000`

Dokumentace API: `http://localhost:8000/docs`
