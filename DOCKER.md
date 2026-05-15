# Docker Setup für Discord Release Bot

## Lokale Entwicklung mit Docker Compose

### Voraussetzungen
- Docker und Docker Compose installiert
- `.env` Datei mit allen benötigten Umgebungsvariablen

### .env Datei erstellen

```bash
cp .env.example .env
```

Bearbeite `.env` und füge folgende Variablen ein:
```
DISCORD_TOKEN=your_token_here
GITHUB_TOKEN=your_github_token_here
GITHUB_OWNER=your_username
GITHUB_REPO=your_repo_name
```

### Bot starten

```bash
docker-compose up --build
```

Für Background-Betrieb:
```bash
docker-compose up -d
```

### Logs anschauen

```bash
docker-compose logs -f bot
```

### Bot stoppen

```bash
docker-compose down
```

---

## GitHub Actions - Automatischer Docker Build

Der Bot wird automatisch gebaut wenn:
- Du zu `master`, `main` oder `develop` pushst
- Folgende Dateien geändert werden:
  - `Dockerfile`
  - `requirements.txt`
  - `main.py`
  - `src/**`
  - `.github/workflows/docker-build.yml`

### Features des CI/CD Workflows

✅ **Automatischer Build** - Auf jeden Push  
✅ **GitHub Container Registry** - Images werden unter `ghcr.io/username/repo` gespeichert  
✅ **Build Caching** - Nutzt GitHub Actions Cache für schnellere Builds  
✅ **Automatische Tags** - Versioniert nach Branch, SHA und Semver  
✅ **Multi-Stage Build** - Optimierte Image-Größe  

### Image Tags

Folgende Tags werden automatisch erstellt:

| Trigger | Tags |
|---------|------|
| Push zu master | `latest`, `master-<sha>` |
| Push zu develop | `develop-<sha>` |
| Tag erstellt (z.B. v1.0.0) | `v1.0.0`, `1.0`, `latest` |

### Image verwenden

```bash
docker pull ghcr.io/your-username/your-repo:latest
docker run -e DISCORD_TOKEN=xxx ghcr.io/your-username/your-repo:latest
```

---

## Dockerfile Details

Das Setup nutzt einen **Multi-Stage Build**:

1. **Builder Stage** - Installiert Python Abhängigkeiten
2. **Final Stage** - Nur Runtime Dependencies

Dies reduziert die final Image-Größe um ~50%.

### Optimierungen

- Slim Base Image (Python 3.11-slim)
- Kein Cache bei pip install
- Keine Build Dependencies im Final Image
- PYTHONUNBUFFERED für sofortige Log-Ausgabe
