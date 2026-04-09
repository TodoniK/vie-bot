# Détecteur de Nouvelles Offres de VIE

Ce script Python permet de détecter automatiquement la publication de nouvelles offres de VIE (Volontariat International en Entreprise) postées sur le site Business France [mon-vie-via.businessfrance.fr](https://mon-vie-via.businessfrance.fr/) et d'envoyer une notification enrichie via un Webhook Discord.

## ✨ Fonctionnalités

- **Détection automatique** : Interroge l'API de Business France pour détecter les nouvelles offres
- **Tri chronologique** : Les offres sont envoyées dans l'ordre de leur publication
- **Détails complets** : Récupère toutes les informations de l'offre (dates, indemnité, localisation, télétravail, etc.)
- **Notifications Discord riches** : Envoie des embeds Discord formatés avec toutes les informations utiles
- **Logs détaillés** : Affichage de logs horodatés pour suivre l'exécution
- **Gestion d'erreurs robuste** : Timeouts, erreurs API, champs manquants
- **Variables d'environnement** : Configuration via fichier .env sécurisé
- **Recherche LinkedIn** : Génère automatiquement un lien de recherche LinkedIn pour le contact

## 📋 Prérequis

- Python 3.7 ou supérieur
- Webhook Discord configuré

## 🚀 Installation

1. Clonez ce dépôt :
   ```bash
   git clone https://github.com/PRFRQ/VIE.git
   cd VIE
   ```

2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

3. Créez un fichier `.env` à la racine du projet :
   ```bash
   cp .env.example .env
   ```

4. Configurez vos variables d'environnement dans `.env` :
   ```env
   DISCORD_WEBHOOK_URL=votre_webhook_discord_ici
   SEARCH_QUERY=engineer                     # Mot-clé de recherche
   SEARCH_LIMIT=5000                         # Nombre max d'offres
   ```

## ⚙️ Configuration

### Variables d'environnement (.env)

- **DISCORD_WEBHOOK_URL** (obligatoire) : URL de votre webhook Discord
- **SEARCH_QUERY** (défaut: "engineer") : Mot-clé de recherche pour filtrer les offres
- **SEARCH_LIMIT** (défaut: 5000) : Nombre maximum d'offres à récupérer

### Personnaliser les critères de recherche

Pour modifier les zones géographiques ou d'autres critères, éditez directement le `payload` dans `vie.py` :

```python
"geographicZones": ["2", "3", "4", "6", "5", "8"],  # Tous les continents
"countriesIds": [],                                   # IDs de pays spécifiques
"activitySectorId": [],                               # Secteurs d'activité
```

### Codes des zones géographiques

- `"2"` : Europe
- `"3"` : Asie
- `"4"` : Amérique du Nord
- `"5"` : Amérique du Sud
- `"6"` : Afrique
- `"8"` : Océanie

## 🔄 Comment ça marche ?

1. Le script interroge l'API `/api/Offers/search` avec les critères configurés
2. Il extrait les IDs des offres retournées
3. Pour chaque nouvelle offre détectée :
   - Récupère les détails complets via l'API `/api/Offers/details/{id}`
   - Formate les données (dates au format DD/MM/YYYY, nom du contact, etc.)
4. **Trie les offres par ordre chronologique** de publication
5. Envoie les notifications Discord dans l'ordre chronologique
6. Sauvegarde les IDs traités dans `ids.txt`

## 🖥️ Utilisation

### Exécution manuelle

```bash
python3 vie.py
```

### Exécution périodique (Linux/macOS)

Configurez un cron job pour une vérification automatique :

```bash
crontab -e
```

Exemples de configurations :
- **Toutes les 10 minutes** :
  ```
  */10 * * * * /usr/bin/python3 /chemin/vers/vie.py >> /chemin/vers/vie.log 2>&1
  ```
- **Toutes les heures** :
  ```
  0 * * * * /usr/bin/python3 /chemin/vers/vie.py >> /chemin/vers/vie.log 2>&1
  ```
- **Tous les jours à 9h** :
  ```
  0 9 * * * /usr/bin/python3 /chemin/vers/vie.py >> /chemin/vers/vie.log 2>&1
  ```

### Exécution périodique (Windows)

Utilisez le Planificateur de tâches Windows :
1. Ouvrez le Planificateur de tâches
2. Créez une nouvelle tâche
3. Configurez le déclencheur (ex: toutes les 10 minutes)
4. Action : Démarrer un programme → `python.exe` avec argument `/chemin/vers/vie.py`

## 📱 Configuration du Webhook Discord

1. Depuis un salon textuel Discord, accédez à ses paramètres
2. Rendez-vous dans l'onglet **Intégrations**
3. Cliquez sur **Webhooks** puis **Nouveau Webhook**

   ![Webhooks Discord](https://github.com/user-attachments/assets/8337ce8d-36bf-473e-b753-2f56bf5e9447)

4. Configurez le nom et l'icône du webhook
5. Copiez l'URL du webhook

   ![Copier URL](https://github.com/user-attachments/assets/c51b925b-8fb7-437d-9b8b-3727d21c04c7)

6. Collez l'URL dans le fichier `vie.py` à la ligne 10

## 📊 Exemple de notification

Chaque nouvelle offre génère une notification Discord contenant :
- 🏭 **Entreprise** : Nom de l'organisation
- 🌍 **Pays** : Pays de la mission
- 🏙️ **Ville** : Ville d'affectation
- 📅 **Durée** : Durée de la mission en mois
- 🎬 **Début** : Date de début de mission (format DD/MM/YYYY)
- 🏁 **Fin** : Date de fin de mission (format DD/MM/YYYY)
- 📧 **Email** : Contact de l'entreprise
- 🌐 **Business France** : Lien vers l'offre complète
- 🔗 **LinkedIn** : Recherche automatique du contact
- 💼 **Télétravail** : Disponibilité du télétravail
- 💵 **Indemnité** : Montant mensuel en euros
- 📆 **Date de publication** : Date de mise en ligne de l'offre

## 🔧 Fonctionnalités avancées

- ✅ **Tri chronologique** : Offres envoyées dans l'ordre de publication
- ✅ **Variables d'environnement** : Configuration sécurisée via fichier .env
- ✅ **Formatage des dates** : Format français DD/MM/YYYY
- ✅ **Rate limiting Discord** : Délai de 1.5s entre chaque notification
- ✅ **Logs détaillés** : Suivi complet de l'exécution avec timestamps
- ✅ **Gestion d'erreurs robuste** : Timeouts, erreurs API, champs manquants

## 📝 Structure du projet

```
VIE/
├── vie.py                  # Script principal
├── ids.txt                 # IDs des offres déjà traitées (auto-généré)
├── .env                    # Configuration (à créer depuis .env.example)
├── .env.example            # Exemple de configuration
├── .gitignore              # Fichiers à ignorer par git
├── requirements.txt        # Dépendances Python
└── README.md               # Documentation
```

## 🐛 Dépannage

### Les notifications ne sont pas envoyées
- Vérifiez que `DISCORD_WEBHOOK_URL` est correctement configuré dans `.env`
- Assurez-vous que le webhook Discord n'a pas été supprimé
- Consultez les logs pour identifier les erreurs

### Erreurs de connexion
- Vérifiez votre connexion Internet
- L'API Business France peut être temporairement indisponible

## 📜 Licence

Ce projet est open source et disponible sous licence MIT.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## ⚠️ Avertissement

Ce script utilise l'API publique de Business France. Veillez à :
- Respecter les conditions d'utilisation de l'API
- Ne pas surcharger l'API avec des requêtes trop fréquentes
- Garder vos variables de configuration confidentielles (fichier `.env` non versionné)
