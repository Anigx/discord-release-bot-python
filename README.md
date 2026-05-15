# Discord GitHub Release Announcement Bot

Ein Discord Bot in Python, der GitHub Releases automatisch in Discord als formatierte Embeds ankündigt. Mit Slash Commands, Docker Support und vollautomatischem GitHub Actions CI/CD.

## Features

- **GitHub Integration**: Fetcht GitHub Releases und postet sie als Discord Embeds
- **/version Command**: Slash Command zum manuellen Auslösen von Release-Ankündigungen
- **Pre-Release Support**: Optionale Unterstützung für Beta/Alpha Releases
- **Asset Links**: Zeigt Download-Links und Dateigröße von Assets
- **Environment Variables**: Vollständig über Umgebungsvariablen konfigurierbar
- **Docker Ready**: Multi-Stage Dockerfile für optimierte Container Images
- **CI/CD**: GitHub Actions mit automatischem Build und Docker Push mit Caching
- **Python 3.11+**: Modern Python mit discord.py

## Tech Stack

- Python 3.11 (slim)
- discord.py 2.3.2
- aiohttp 3.9.1
- GitHub Actions für CI/CD
- Docker & Docker Compose

## Schnellstart

### 1. Voraussetzungen

- Python 3.11+ oder Docker
- Discord Bot Token
- GitHub Repository (mit öffentlichen Releases)

### 2. Installation (Local)

```bash
# Repository klonen
git clone https://github.com/Anigx/discord-release-bot-python.git
cd discord-release-bot-python

# Virtual Environment erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt
```

### 3. Konfiguration

Kopiere `.env.example` zu `.env` und trage deine Werte ein:

```bash
cp .env.example .env
```

**Erforderliche Environment Variables:**

```env
DISCORD_TOKEN=dein_bot_token
DISCORD_CLIENT_ID=deine_client_id
DISCORD_ANNOUNCEMENT_CHANNEL_ID=channel_id_für_announcements
GITHUB_OWNER=github_username
GITHUB_REPO=repository_name
```

**Optionale Environment Variables:**

```env
GITHUB_TOKEN=optional_github_token    # Für höhere Rate Limits (5000/h statt 60/h)
APP_NAME=Deine App                    # Standard: "MyApp"
INCLUDE_PRE_RELEASES=false            # Standard: false
INCLUDE_ASSETS=true                   # Standard: true
DISCORD_GUILD_ID=                     # Optional: für schnelle Command Registration
```

### 4. Discord Bot Setup

1. [Discord Developer Portal](https://discord.com/developers/applications) öffnen
2. Neue Application erstellen
3. Im "Bot" Bereich "Add Bot" klicken
4. Token kopieren → in `.env` eintragen
5. Client ID kopieren → in `.env` eintragen
6. Intents aktivieren: `Guilds`
7. OAuth2 Permissions: `Send Messages`, `Embed Links`
8. Bot auf Server einladen via OAuth2 URL

### 5. Bot starten

```bash
python main.py
```

Der Bot sollte dann online gehen und der `/version` Command verfügbar sein.

## Verwendung

### /version Command

```bash
/version                              # Neueste Release posten
/version tag:v1.0.0                   # Spezifische Version posten
/version tag:v2.0.0-beta pre_releases:true
```

**Parameter:**
- `tag` (optional): Spezifisches Release Tag (z.B. v1.0.0)
- `pre_releases` (optional): Pre-Releases einschließen? (true/false)

### Command-Registrierung

- Mit `DISCORD_GUILD_ID`: Commands sofort verfügbar (< 1 Sekunde)
- Ohne Guild ID: Global Commands (15-60 Minuten Synchronisierung)

## Docker

### Docker Compose (empfohlen für Development)

```bash
# .env Datei erstellen
cp .env.example .env
# Werte eintragen

# Bot starten
docker-compose up --build

# Im Hintergrund:
docker-compose up -d

# Logs anschauen:
docker-compose logs -f bot

# Stoppen:
docker-compose down
```

### Docker CLI

```bash
# Image bauen
docker build -t discord-release-bot .

# Container starten
docker run -d --env-file .env --name discord-bot discord-release-bot

# Logs
docker logs -f discord-bot

# Stoppen
docker stop discord-bot
```

### Image von GHCR verwenden

```bash
docker pull ghcr.io/Anigx/discord-release-bot-python:latest
docker run -d --env-file .env ghcr.io/Anigx/discord-release-bot-python:latest
```

## GitHub Actions CI/CD

Der Bot wird automatisch gebaut und deployed bei:
- Push zu `master`, `main` oder `develop`
- Änderungen an relevanten Dateien

**Docker Images werden zu GitHub Container Registry gepusht unter:**
```
ghcr.io/Anigx/discord-release-bot-python
```

**Automatische Tags:**
- `latest` - auf default branch
- `{branch}-{sha}` - für jeden Push
- `v{version}` - für Release Tags

**Features:**
- Build Caching mit GitHub Actions (schnellere Builds)
- Multi-Stage Build (optimierte Image-Größe)
- Nur Push bei erfolgreichem Build

Siehe [.github/workflows/docker-build.yml](.github/workflows/docker-build.yml) für Details.

## Projektstruktur

```
discord-release-bot-python/
├── main.py                      # Entry Point
├── Dockerfile                   # Multi-Stage Docker Build
├── docker-compose.yml          # Docker Compose Config
├── requirements.txt            # Python Dependencies
├── .env.example               # Environment Variable Template
├── .dockerignore              # Docker Build Exclusions
├── DOCKER.md                  # Docker Dokumentation
├── README.md                  # Diese Datei
│
└── src/
    ├── __init__.py
    ├── bot.py                 # Discord Bot & Slash Commands
    ├── config.py              # Environment Variable Loading
    ├── logger.py              # Logging Setup
    ├── types.py               # Type Definitions
    │
    └── services/
        ├── __init__.py
        ├── github_service.py    # GitHub API Client
        ├── formatter_service.py # Discord Embed Formatter
        └── discord_service.py   # Discord Message Poster
```

## Services

### GitHubService
Fetcht Releases von der GitHub API.

```python
github = GitHubService(owner, repo, token)
release = await github.get_latest_release(include_pre_releases=False)
release = await github.get_release_by_tag("v1.0.0")
```

### FormatterService
Erstellt formatierte Discord Embeds aus Release Daten.

```python
formatter = FormatterService(app_name="MyApp")
embed = formatter.create_release_embed(release)
```

### DiscordService
Postet Embeds in Discord Channels.

```python
discord_svc = DiscordService(bot, channel_id="12345")
await discord_svc.post_release(embed)
```

## Troubleshooting

### Bot startet nicht / Token ungültig

```bash
# Token in .env prüfen
cat .env | grep DISCORD_TOKEN

# Bot Manual starten mit Debugging
python main.py
```

### /version Command nicht sichtbar

- `DISCORD_CLIENT_ID` und `DISCORD_TOKEN` sind korrekt?
- Bei globalen Commands: 15-60 Minuten warten (Discord Cache)
- Alternative: `DISCORD_GUILD_ID` setzen für sofortige Registrierung

### GitHub Release wird nicht gefunden

- GitHub Repository und Owner Name korrekt?
- Releases sind public/sichtbar?
- Rate Limit erreicht? (`GITHUB_TOKEN` hinzufügen)
  - Ohne Token: 60 Requests/h
  - Mit Token: 5000 Requests/h

### Docker Image baut nicht

- Dockerfile vorhanden?
- `requirements.txt` valide?
- Docker/Docker Compose Installation ok?

## Logs

Bot loggt zu stdout. Bei Docker Compose:

```bash
docker-compose logs -f bot
```

Bei direktem Container Run:

```bash
docker logs -f container_name
```

## Lizenz

MIT

## Contributing

Issues und Pull Requests sind willkommen!

---

**Version**: 1.0.0  
**Python**: 3.11+  
**discord.py**: 2.3.2
