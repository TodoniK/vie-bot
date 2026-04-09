# 🇫🇷 VIE Bot — Détecteur d'Offres VIE

Bot de monitoring des offres de VIE (Volontariat International en Entreprise) publiées sur [Business France](https://mon-vie-via.businessfrance.fr/). Envoie des notifications Discord en temps réel pour chaque nouvelle offre détectée.

## ✨ Fonctionnalités

- **Monitoring temps réel** — vérifie les nouvelles offres toutes les 60 secondes
- **Notifications Discord riches** — embeds avec drapeaux pays 🇫🇷🇩🇪🇮🇹, indemnité, dates, télétravail
- **Async & parallèle** — récupération des détails par batch avec `httpx`
- **Stockage SQLite** — persistance crash-safe des IDs (remplace `ids.txt`)
- **Migration automatique** — importe `ids.txt` legacy vers SQLite au premier lancement
- **Arrêt gracieux** — gestion propre de SIGTERM/SIGINT (Docker)
- **Config validée** — Pydantic Settings avec validation au démarrage

## 🚀 Déploiement

### Docker Compose (recommandé)

```bash
cp .env.example .env
# Éditez .env avec votre DISCORD_WEBHOOK_URL
docker compose up -d
```

### Dokploy

1. **Créer une application** → Source : **GitHub** → `TodoniK/vie-bot`
2. **Build** : **Docker Compose**
3. **Variables d'environnement** (onglet "Environment") : configurer `DISCORD_WEBHOOK_URL`
4. **Déployer**

> ℹ️ Les IDs connus sont embarqués dans l'image via `ids.txt`. À chaque démarrage, ils sont importés dans SQLite. Si le container redémarre, seules les offres apparues entre-temps peuvent être renvoyées.

## ⚙️ Configuration

| Variable | Défaut | Description |
|---|---|---|
| `DISCORD_WEBHOOK_URL` | *(obligatoire)* | URL du webhook Discord |
| `CHECK_INTERVAL` | `60` | Intervalle en secondes entre chaque vérification |
| `SEARCH_LIMIT` | `5000` | Nombre max d'offres à récupérer |
| `DATA_DIR` | `/app/data` | Répertoire de stockage SQLite |
| `LOG_LEVEL` | `INFO` | Niveau de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

### Personnaliser les critères de recherche

Éditez le payload dans `src/vie_bot/api.py` :

```python
"geographicZones": ["2", "3", "4", "6", "5", "8"],  # Tous les continents
"countriesIds": [],                                   # IDs de pays spécifiques
"activitySectorId": [],                               # Secteurs d'activité
```

## 🖥️ Utilisation locale

```bash
cp .env.example .env
# Éditez .env avec votre DISCORD_WEBHOOK_URL

# Avec uv (recommandé)
uv pip install .
vie-bot

# Ou avec pip
pip install .
python -m vie_bot
```

### Test avec Docker

```bash
docker compose up --build
```

## 📝 Structure du projet

```
vie-bot/
├── src/vie_bot/
│   ├── __init__.py
│   ├── __main__.py     # Point d'entrée + boucle scheduler
│   ├── config.py       # Pydantic Settings
│   ├── api.py          # Client API Business France (async)
│   ├── discord.py      # Webhook Discord + formatage embed
│   ├── scheduler.py    # Logique de vérification des offres
│   └── storage.py      # SQLite (persistance des IDs)
├── pyproject.toml      # Packaging Python moderne
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── ids.txt             # IDs connus (fallback embarqué dans l'image)
├── .dockerignore
└── README.md
```

## 🔄 Comment ça marche ?

1. Interroge l'API `/api/Offers/search` toutes les 60 secondes
2. Compare les IDs avec la base SQLite locale
3. Pour chaque nouvelle offre :
   - Récupère les détails via `/api/Offers/details/{id}` (par batch de 10 en parallèle)
   - Formate un embed Discord riche
4. Trie les offres par date de publication et envoie les notifications
5. Sauvegarde les IDs dans SQLite

## 📱 Configuration du Webhook Discord

1. Paramètres du salon → **Intégrations** → **Webhooks** → **Nouveau Webhook**
2. Copiez l'URL et configurez-la dans `DISCORD_WEBHOOK_URL`

## 🐛 Dépannage

- **Pas de notifications** → vérifiez `DISCORD_WEBHOOK_URL` et les logs Docker
- **Erreurs de connexion** → l'API Business France peut être temporairement indisponible
- **Trop de notifications au démarrage** → assurez-vous que le volume `/app/data` est bien monté

## 📜 Licence

MIT
