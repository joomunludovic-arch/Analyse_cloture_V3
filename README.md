# 📊 Analyse Boursière Automatisée (FastAPI + Telegram)

API cloud intelligente permettant l’analyse quotidienne des marchés financiers et l’envoi automatisé d’alertes stratégiques sur Telegram, avec visualisations professionnelles et détection des tendances clés.

---

## 🚀 Description

Cette API hébergée analyse automatiquement des dizaines d’actions, indices et cryptos pour identifier les titres à fort potentiel. Les résultats sont envoyés directement sur Telegram avec :

- Graphiques personnalisés
- Alertes prêtes à l’action
- Résumés clairs à chaque déclenchement

**100 % automatisée**, aucun déclenchement manuel requis.

---

## 🧩 Fonctionnalités principales

✅ Analyse multi-actifs (actions, indices, cryptos)  
✅ Alertes Telegram enrichies (graphique + message)  
✅ Détection intelligente de volatilité et momentum  
✅ Visualisation professionnelle avec Matplotlib  
✅ Intégration Google Sheets pour gestion des tickers  
✅ Déclenchement automatique en fin de session boursière  
✅ API FastAPI avec endpoints scalables

---

## 🔗 Endpoints disponibles

| Méthode | Endpoint        | Description                                      |
|--------|------------------|--------------------------------------------------|
| GET    | `/`              | Lance l’analyse Ichimoku + volatilité depuis Google Sheets |
| GET    | `/volatilite`    | Détecte les actifs les plus volatils (Top 5)     |
| GET    | `/ouverture`     | Détermine les positions d'ouverture stratégiques |
| GET    | `/cashflow`      | Identifie les opportunités à fort potentiel de cash-flow |
| GET    | `/breakout`      | Analyse les breakouts avec momentum visuel       |

---

## ⚙️ Technologies utilisées

- Python 3.10
- FastAPI
- yfinance
- pandas, numpy
- matplotlib
- telegram-bot v20.3
- gspread + Google Sheets API
- Render.com (déploiement cloud)

---

## 🔐 Sécurité & Configuration

Les accès sont sécurisés via :

- Variables d’environnement (`TELEGRAM_TOKEN`, `CHAT_ID`, `GOOGLE_SHEET_ID`)
- Fichier secret `credentials.json` monté dans `/etc/secrets/`

---

## 🛠️ Démarrage local (dev)

```bash
git clone https://github.com/ton-repo/analyse-cloture-v3.git
cd analyse-cloture-v3
pip install -r requirements.txt
uvicorn main:app --reload --port 10000
