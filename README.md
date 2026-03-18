# 💊 Pharma Supply Chain Dashboard — Côte d'Ivoire

> **Problème :** En Afrique de l'Ouest, les ruptures de stock de médicaments essentiels touchent 30% des formations sanitaires, causant des décès évitables. Ce projet détecte les risques de rupture **7 jours à l'avance** et recommande les quantités optimales à commander.

[![Streamlit](https://img.shields.io/badge/🔴_Live_Dashboard-Streamlit-FF4B4B?style=for-the-badge)](https://pharma-supply-ci.streamlit.app)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![R](https://img.shields.io/badge/R-276DC3?style=flat&logo=r&logoColor=white)
![scikit--learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat&logo=scikitlearn&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-4479A1?style=flat&logo=postgresql&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)

---

## 💰 Impact Business

| Métrique | Avant | Après | Gain |
|----------|-------|-------|------|
| Détection des ruptures | Réactive (0 jour) | Prédictive (7 jours) | **+7 jours d'anticipation** |
| Précision des prévisions | ±12.5% (méthode naïve) | ±10.3% (XGBoost) | **-18% d'erreur** |
| Médicaments vitaux à risque | Non suivi | 12 alertes temps réel | **0 angle mort** |
| Couverture | Manuel, 1 district | Automatisé, 10 districts | **7.5M habitants couverts** |
| Produits-districts en alerte | Non détectés | 32 High + 6 Medium | **38 alertes actionnables** |

---

## 🔴 Dashboard Live

**→ [Accéder au dashboard](https://pharma-supply-ci.streamlit.app)**

3 vues interactives :
- **📊 Overview** — KPIs nationaux, tendances de consommation, taux de rupture par district, répartition par catégorie thérapeutique
- **🤖 Prévisions ML** — Demande prédite par produit avec comparaison XGBoost vs baseline naïf
- **🚨 Alertes** — Médicaments vitaux à risque, avec score de risque et quantités recommandées à commander

---

## 🔄 Architecture du Pipeline

```
📥 INGESTION          🧹 NETTOYAGE          📊 ANALYSE          🤖 ML              🚨 ALERTES          📈 DASHBOARD
┌──────────┐       ┌──────────┐        ┌──────────┐       ┌──────────┐       ┌──────────┐       ┌──────────┐
│ WHO API  │──────▶│data.table│───────▶│ SQL KPIs │──────▶│ XGBoost  │──────▶│ Scoring  │──────▶│Streamlit │
│ CSV/Excel│       │Validation│        │Agrégation│       │ Prophet  │       │ Risque   │       │ Plotly   │
│ Parquet  │       │ Parquet  │        │ Tendances│       │Prévision │       │ Reorder  │       │  Live    │
└──────────┘       └──────────┘        └──────────┘       └──────────┘       └──────────┘       └──────────┘
  01_ingest.py      02_clean.py        03_transform.py    04_forecast.py     05_alerts.py      dashboard/app.py
```

Chaque étape est un script Python autonome. Le fichier `pipeline.py` les orchestre en séquence.

---

## 📊 Données

| Source | Type | Contenu |
|--------|------|---------|
| [WHO GHO API](https://www.who.int/data/gho/info/gho-odata-api) | API OData | Indicateurs santé Côte d'Ivoire |
| [WHO Essential Medicines List](https://www.who.int/groups/expert-committee-on-selection-and-use-of-essential-medicines) | Référentiel | 50 médicaments essentiels (24ème édition 2025) |
| RGPH Côte d'Ivoire | Open Data | Population par district sanitaire |
| Simulation enrichie | Parquet | 18 000 lignes de consommation mensuelle (50 produits × 10 districts × 36 mois) |

> ⚠️ Les données de consommation sont simulées à partir de patterns réels de la supply chain pharmaceutique ivoirienne (5 ans d'expérience terrain). Saisonnalité paludisme, fiabilité d'approvisionnement par district, et classification VEN sont modélisés. Les données OMS sont réelles.

---

## 📈 Résultats du Pipeline (dernière exécution)

```
═══ PIPELINE RESULTS ═══

📥 Ingestion:    50 produits | 10 districts | 18,000 lignes | 36 mois
🧹 Nettoyage:    18,000 lignes enrichies → 25 colonnes | 0 erreurs de validation
📊 KPIs:         Fill rate 98.8% | Stockout rate 7.6% | Valeur: 4.8 Mrd FCFA
🤖 Forecast:     MAPE modèle 10.3% vs baseline 12.5% → amélioration 18%
🚨 Alertes:      32 High risk | 6 Medium risk | 12 médicaments vitaux à risque
```

---

## 🏗️ Structure du Projet

```
pharma-supply-dashboard/
├── python/
│   ├── 01_ingest.py            # Ingestion multi-sources (CSV, Parquet, API)
│   ├── 02_clean.py             # Nettoyage, validation, feature engineering
│   ├── 03_transform.py         # KPIs globaux et par catégorie
│   ├── 04_forecast.py          # XGBoost demand forecasting (top 20 produits)
│   ├── 05_alerts.py            # Scoring risque rupture + recommandations commande
│   └── pipeline.py             # Orchestrateur (exécute les 5 étapes)
├── R/
│   └── data_processing.R       # Pipeline alternatif en R (data.table)
├── dashboard/
│   └── app.py                  # Dashboard Streamlit 3 onglets
├── sql/
│   └── schema_and_queries.sql  # Schéma SQL + requêtes KPI + trends YoY
├── data/
│   ├── raw/                    # Données sources (CSV, Parquet)
│   └── processed/              # 7 fichiers Parquet transformés
├── docs/
│   └── data_dictionary.md      # Dictionnaire des données (9 tables, 45+ colonnes)
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🛠️ Stack Technique

| Couche | Outil | Rôle |
|--------|-------|------|
| **Ingestion** | Python (pandas, openpyxl) | Lecture CSV, Excel, Parquet |
| **Traitement** | R (data.table, arrow) + Python | Nettoyage haute performance |
| **Stockage** | Apache Parquet | Compression columnar (886 KB CSV → 210 KB Parquet) |
| **ML** | scikit-learn, XGBoost | Prévision de demande (lag features, rolling stats) |
| **Dashboard** | Streamlit + Plotly | Visualisation interactive déployée |
| **SQL** | PostgreSQL-compatible | Schéma + requêtes analytiques |

---

## ▶️ Quick Start

```bash
# 1. Cloner le repo
git clone https://github.com/kouameruben/pharma-supply-dashboard.git
cd pharma-supply-dashboard

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Exécuter le pipeline complet (génère les données → nettoie → ML → alertes)
python python/pipeline.py

# 4. Lancer le dashboard
streamlit run dashboard/app.py
```

Le dashboard s'ouvre à `http://localhost:8501`

---

## 🧑‍💻 Contexte Professionnel

Ce projet est basé sur **5 ans d'expérience en supply chain pharmaceutique** en Côte d'Ivoire :
- Prévision de demande de médicaments pour 10 districts sanitaires (7.5M habitants)
- Plans d'approvisionnement et suivi KPIs pour des programmes financés par la **BAD**, **KfW**, **AFD** et la **Banque Mondiale**
- Optimisation des niveaux de stock et réduction des péremptions
- Cartographie des systèmes de distribution pharmaceutique

---

## 📖 Documentation

- **[Dictionnaire des données](docs/data_dictionary.md)** — 9 tables, 45+ colonnes, formules et relations
- **[Requêtes SQL](sql/schema_and_queries.sql)** — Schéma, KPIs, trends YoY, produits à risque

---

## 👤 Auteur

**Kouamé Ruben** — Senior Data Analyst & Analytics Engineer
- 8 ans d'expérience : Supply Chain Pharma (5 ans) · Telecom (2 ans) · Finance (1 an)
- [LinkedIn](https://www.linkedin.com/in/kouameruben/) · [GitHub](https://github.com/kouameruben)

## 📜 Licence

MIT License
