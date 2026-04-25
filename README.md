# FinModel Pro 📊

Application de modélisation financière : prévisions budgétaires, amortissements et analyse DCF.

## Fonctionnalités

- **Budget & Prévisions** : CA, coûts, EBITDA, résultat net sur N ans, 3 scénarios
- **Amortissements** : méthode linéaire ou dégressive (double taux), investissements supplémentaires
- **Analyse DCF** : FCF ajustés (DA + Capex + BFR), valeur terminale, equity value
- **Sensibilité** : heatmap WACC × taux de croissance terminal
- **Export CSV** de tous les tableaux

## Déploiement gratuit sur Streamlit Cloud

### Étape 1 — Créer un compte GitHub (gratuit)
1. Aller sur https://github.com/signup
2. Créer un compte gratuit

### Étape 2 — Créer un dépôt GitHub
1. Cliquer sur "New repository"
2. Nom : `finmodel-pro` (ou autre)
3. Visibilité : **Public** (requis pour Streamlit Cloud gratuit)
4. Cliquer "Create repository"

### Étape 3 — Uploader les fichiers
Uploader les deux fichiers dans le dépôt :
- `app.py`
- `requirements.txt`

### Étape 4 — Déployer sur Streamlit Cloud
1. Aller sur https://share.streamlit.io
2. Se connecter avec GitHub
3. Cliquer "New app"
4. Sélectionner votre dépôt → branche `main` → fichier `app.py`
5. Cliquer "Deploy!" ✅

L'application sera en ligne en ~2 minutes sur une URL publique gratuite.

## Lancer localement

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Structure

```
finmodel-pro/
├── app.py            # Application principale
└── requirements.txt  # Dépendances Python
```
