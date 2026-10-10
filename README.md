# 🇫🇷 VIE Bot — Détecteur d'Offres VIE

Bot de monitoring des offres de VIE (Volontariat International en Entreprise) publiées sur [Business France](https://mon-vie-via.businessfrance.fr/). Envoie des notifications Discord en temps réel pour chaque nouvelle offre détectée.

## ✨ Fonctionnalités

- **Monitoring temps réel** — vérifie les nouvelles offres toutes les 60 secondes
- **Filtrage IT/RH** — ne notifie que les offres IT/réseau (Amérique du Nord, Océanie, Asie du Sud-Est) et RH (partout), classification par mots-clés sur le titre
- **Notifications Discord riches** — embeds avec drapeaux pays 🇫🇷🇩🇪🇮🇹, indemnité, dates, télétravail, couleur par catégorie (🟠 IT / 🟣 RH)
- **Async & paginé** — récupération de toutes les offres via `httpx` (l'API plafonne à 200 résultats par page)
- **Stockage SQLite** — persistance crash-safe des IDs (remplace `ids.txt`)
- **Premier démarrage silencieux** — base vide : les offres existantes sont mémorisées sans être postées
- **Clé API automatique** — la clé `X-API-KEY` est lue dans la page publique Business France et relue seule en cas de 401/403
- **Lots Discord** — jusqu'à 10 offres par message, respect des 429 (`retry_after`)
- **Healthcheck Docker** — conteneur `unhealthy` si aucun cycle n'a réussi depuis 3 intervalles + 5 min
- **Arrêt gracieux** — gestion propre de SIGTERM/SIGINT (Docker)
- **Config validée** — Pydantic Settings avec validation au démarrage
- **Alerting Discord** — notifie le salon en cas d'erreur (401, panne API...) et de rétablissement, pas besoin de surveiller les logs

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

> ℹ️ Les IDs vus sont dans `DATA_DIR/vie_bot.db` (volume). Sur un volume neuf, le premier cycle mémorise l'existant sans rien poster.

## ⚙️ Configuration

| Variable | Défaut | Description |
|---|---|---|
| `DISCORD_WEBHOOK_URL` | *(obligatoire)* | URL du webhook Discord |
| `CIVIWEB_API_KEY` | *(auto)* | Header `X-API-KEY` de l'API Business France. Facultatif : lu dans la page publique et rafraîchi sur 401/403 |
| `IT_COUNTRIES` | Amérique du Nord, Océanie, Asie du Sud-Est | Codes pays ISO pour les offres IT, séparés par des virgules |
| `IT_EXTRA_KEYWORDS`, `HR_EXTRA_KEYWORDS`, `EXCLUDE_EXTRA_KEYWORDS` | *(vide)* | Mots-clés ajoutés aux listes de `classify.py` |
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

### Personnaliser la classification IT/RH

Le bot ne notifie que les offres classées **IT** (mots-clés + pays cible) ou **RH**
(mots-clés, sans restriction géo). Tout éditer dans `src/vie_bot/classify.py` :

- `IT_COUNTRIES` — pays cibles pour la catégorie IT (codes ISO)
- `IT_INCLUDE` / `IT_EXCLUDE` — mots-clés IT et exceptions (ex: "Business Developer" est exclu)
- `HR_INCLUDE` — mots-clés RH

Lancez `python src/vie_bot/classify.py` après modification pour valider les asserts.

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
│   ├── api.py          # Client API Business France (async, paginé)
│   ├── classify.py     # Classification des offres (IT / RH / hors critères)
│   ├── discord.py      # Webhook Discord + formatage embed
│   ├── resilience.py   # Cadence des alertes d'erreur Discord
│   ├── scheduler.py    # Logique de vérification des offres
│   └── storage.py      # SQLite (persistance des IDs)
├── pyproject.toml      # Packaging Python moderne
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── tests/              # pytest (lancé en CI avant publication de l'image)
├── .dockerignore
└── README.md
```

## 🔄 Comment ça marche ?

1. Interroge l'API `/api/Offers/search` toutes les 60 secondes (paginé, 200 offres/page)
2. Compare les IDs avec la base SQLite locale
3. Classe chaque nouvelle offre : **IT** (mots-clés + pays cible) / **RH** (mots-clés) / hors critères
4. Pour les offres IT ou RH, formate et envoie un embed Discord (couleur par catégorie)
5. Sauvegarde tous les IDs traités dans SQLite (envoyés + hors critères), pour ne jamais les retraiter

## 📱 Configuration du Webhook Discord

1. Paramètres du salon → **Intégrations** → **Webhooks** → **Nouveau Webhook**
2. Copiez l'URL et configurez-la dans `DISCORD_WEBHOOK_URL`

## 🐛 Dépannage

- **Pas de notifications** → vérifiez `DISCORD_WEBHOOK_URL` et les logs Docker
- **401 Unauthorized sur `/api/Offers/search`** → le bot relit automatiquement la clé dans la page publique. Si l'erreur persiste, Business France a changé le format de sa page (`API_KEY:"..."`) : adapter `extract_api_key` dans `api.py`. Le bot envoie une alerte Discord dès le 1er échec, puis toutes les ~10 min tant que l'erreur persiste.
- **400 Bad Request sur `/api/Offers/search`** → l'API plafonne `limit` à 200 ; le bot pagine automatiquement, mais si Business France change encore ce plafond, ajustez `PAGE_SIZE` dans `api.py`.
- **Pas de notifications alors que de nouvelles offres existent** → normal si elles ne matchent ni les critères IT ni RH (voir `classify.py`)
- **Erreurs de connexion** → l'API Business France peut être temporairement indisponible
- **Trop de notifications au démarrage** → assurez-vous que le volume `/app/data` est bien monté

## 📜 Licence

MIT
