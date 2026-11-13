# Cassandra JSON ETL — architecture Lead Tech

ETL Python démonstratif, structuré et testable :
- lecture d'un fichier JSON (tableau JSON ou JSON Lines) avec Pandas ;
- validation et normalisation du jeu d'événements ;
- routage par dictionnaire de fonctions (`Callable`) ;
- transformations indépendantes par table cible ;
- scoring d'anomalies d'achat avec Scikit-learn (`StandardScaler` + `IsolationForest`) ;
- chargement Cassandra avec requêtes préparées et exécution asynchrone bornée ;
- événements synthétiques réalistes et tests unitaires sans Cassandra.

## 1. Modèle fonctionnel

Un événement source peut alimenter plusieurs vues dénormalisées :

| Table | Partition key | Usage |
|---|---|---|
| `events_by_player_day` | `(player_id, event_day)` | chronologie d'un joueur sur une journée |
| `events_by_type_day` | `(event_type, event_day)` | analyse d'un type d'événement par jour |
| `purchases_by_player_month` | `(player_id, purchase_month)` | achats d'un joueur par mois, avec score d'anomalie |

Les événements `login`, `logout`, `level_completed` et `purchase` alimentent les deux premières tables. Seuls les événements `purchase` alimentent la troisième.

Les tables sont des projections de lecture, pas un modèle relationnel normalisé. Les clés de partition sont choisies en fonction des requêtes métier illustrées. En production, valider la cardinalité, la taille des partitions, la rétention et les patterns de lecture réels.

## 2. Prérequis

- Python 3.9+ (versions de dépendances compatibles Python 3.9 ; Python 3.11 recommandé)
- Docker et Docker Compose
- 4 Go de RAM disponibles pour Cassandra en local (configuration JVM réduite dans compose)

## 3. Démarrage

```bash
python -m venv .venv
source .venv/bin/activate              # Windows : .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env

docker compose up -d
docker compose ps
```

Attendre que Cassandra soit healthy. Initialiser le schéma :

```bash
python -m app.cli init-schema
```

Lancer l'ETL :

```bash
python -m app.cli run
```

Options :

```bash
python -m app.cli run --input data/events.json
python -m app.cli run --dry-run
pytest -q
```

`--dry-run` exécute extraction, validation, transformations et scoring sans connexion Cassandra.

Pour mesurer la couverture des tests unitaires :

```bash
python -m pip install -r requirements-dev.txt
python -m pytest --cov=app --cov-report=term-missing
```

## 4. Dashboard Cassandra

Après installation des dépendances et démarrage de Cassandra, lancer l'interface :

```bash
.venv/bin/python -m streamlit run dashboard.py
```

Si l'environnement virtuel n'existe pas encore, le créer puis y installer les dépendances avec
`python -m venv .venv` et `.venv/bin/python -m pip install -r requirements.txt`. Cela évite de
modifier l'environnement Anaconda global.

Le dashboard permet de consulter les événements par joueur/jour, par type/jour et les achats par
joueur/mois, avec un résumé des montants et des scores d'anomalie. Chaque lecture exige la clé de
partition complète et limite l'affichage à 500 lignes ; aucune lecture globale des tables n'est
effectuée.

## 5. Structure

```text
app/
  cli.py
  config.py
  logging_config.py
  domain/
    models.py
  extract/
    json_extractor.py
  transform/
    common.py
    player.py
    event_type.py
    purchase.py
    anomaly.py
  routing/
    registry.py
    router.py
  load/
    cassandra_client.py
    cassandra_loader.py
  pipeline/
    etl.py
data/
  events.json
  purchase_baseline.json
cassandra/schema.cql
tests/
```

## 6. Scikit-learn : approche retenue

Le pipeline d'anomalie est entraîné sur `data/purchase_baseline.json`, un jeu de référence synthétique représentant des achats habituels. Il utilise :
- `StandardScaler` pour mettre les variables numériques à une échelle comparable ;
- `IsolationForest` pour repérer des achats atypiques selon montant, quantité et heure.

Le modèle est ajusté une fois au démarrage du traitement à partir du jeu de référence, puis utilisé pour scorer le lot. Ce choix évite de réentraîner le modèle sur le lot à analyser, ce qui biaiserait le score. En production, remplacer le baseline fourni par un historique métier qualifié, versionner le modèle et surveiller dérive et faux positifs. Un score d'anomalie n'est pas une décision antifraude.

## 7. Fiabilité et limites

- L'ETL lit les événements en DataFrame et valide les champs obligatoires.
- Les événements invalides sont comptabilisés et journalisés ; ils ne sont pas chargés.
- Les insertions sont asynchrones avec une limite de requêtes en vol.
- Les insertions Cassandra sont idempotentes grâce à l'`event_id` déterministe dans les clés primaires.
- Cassandra garantit l'atomicité d'une mutation sur une partition, pas une transaction globale entre les trois tables. Une panne peut donc laisser une projection chargée et une autre en échec : prévoir reprise, métriques et réconciliation.
- Le chargement n'utilise pas de `BATCH` multi-partitions. Ce n'est pas un mécanisme d'accélération générique dans Cassandra.
- Le schéma local utilise `SimpleStrategy` et RF=1 uniquement pour le développement. En production, choisir `NetworkTopologyStrategy` et un RF adapté au cluster.
- Le code de démonstration ne remplace pas une stratégie de checkpoint/offset, dead-letter queue ou orchestration (Airflow, Dagster, etc.) pour un flux critique.

## 8. Requêtes d'exemple

```sql
-- Chronologie d'un joueur pour une date
SELECT * FROM game_analytics.events_by_player_day
WHERE player_id = 'player-001' AND event_day = '2026-11-13';

-- Événements d'un type pour une date
SELECT * FROM game_analytics.events_by_type_day
WHERE event_type = 'purchase' AND event_day = '2026-11-13';

-- Achats d'un joueur sur un mois
SELECT * FROM game_analytics.purchases_by_player_month
WHERE player_id = 'player-001' AND purchase_month = '2026-11';
```
