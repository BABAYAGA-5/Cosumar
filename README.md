# Système de Recrutement Numérique Cosumar

## 🏗️ Architecture

- **Backend** : Django REST Framework (Python)
- **Frontend** : Angular 17+ (TypeScript)
- **Base de données** : SQLite (développement)
- **Traitement de documents** : Génération DOCX/PDF et capacités OCR

## 📋 Prérequis

Avant d'exécuter cette application, assurez-vous d'avoir installé les éléments suivants :

- **Python 3.10+** - [Télécharger Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Télécharger Node.js](https://nodejs.org/)
- **npm** (fourni avec Node.js)
- **Git** - [Télécharger Git](https://git-scm.com/)
- **Poppler** - Pour le traitement des PDF avec OCR
  - Windows : [Poppler pour Windows](http://blog.alivate.com.au/poppler-windows/)
    > **Remarque** : Après l'installation, ajoutez le dossier contenant `poppler/bin` à la variable d'environnement `PATH` pour que les commandes soient accessibles depuis le terminal et changer la variable poppler_path dans Cosumar/Cosumar_Digital_Recrutement/resume_service/PDF.py vers celle qui correspond dans votre système.
  - macOS : `brew install poppler`
  - Linux : `sudo apt-get install poppler-utils`

## 🚀 Démarrage Rapide

### 1. Cloner le Référentiel

```bash
git clone https://github.com/BABAYAGA-5/Cosumar
cd Cosumar
```

### 2. Configuration du Backend (Django)

#### Créer un Environnement Virtuel Python

```bash
python -m venv env

# Activer l'environnement virtuel
# Sur Windows :
env\Scripts\activate
# Sur macOS/Linux :
source env/bin/activate
```

#### Installer les Dépendances Python

```bash
cd Cosumar_Digital_Recrutement

pip install -r requirements.txt
```

#### Configuration de la Base de Données

```bash
python manage.py createmigrations
python manage.py migrate
```

#### Démarrer le Serveur Backend

```bash
python manage.py runserver

# Ou pour utiliser https
python manage.py runserver_plus --cert-file cert.pem --key-file key.pem
```

Le backend sera disponible à :
- HTTP : `http://localhost:8000`
- HTTPS : `https://localhost:8000`

### 3. Configuration du Frontend (Angular)

Ouvrir une nouvelle fenêtre de terminal et naviguer vers le répertoire frontend :

```bash
cd Cosumar_Digital_Recrutement_Front
```

#### Installer les Dépendances Node.js

```bash
npm install
```

#### Démarrer le Serveur de Développement Frontend

```bash
ng serve

# Port personnalisé
ng serve --port 3000
```

Le frontend sera disponible à :
- HTTP : `http://localhost:4200` (port par défaut)
- HTTPS : `https://localhost:4200`

### Configuration de l'API Frontend

Mettre à jour `src/environments/environment.ts` :

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/'  // ou https://localhost:8000/
  /* Le projet utilise https://gkwqgv43-8000.uks1.devtunnels.ms/ qui est un port transféré utilisant l'option de transfert de port de vscode pour simuler https, mais vous pouvez le changer vers l'addresse locale ou un autre tunnel que vous voulez
};
```

## 📁 Structure du Projet

```
Cosumar/
├── Cosumar_Digital_Recrutement/     # Backend Django
│   ├── auth_service/                # Module d'authentification
│   ├── resume_service/              # Logique principale de l'application
│   ├── Cosumar_Digital_Recrutement/ # Paramètres Django
│   ├── manage.py                    # Script de gestion Django
│   └── requirements.txt             # Dépendances Python
├── Cosumar_Digital_Recrutement_Front/ # Frontend Angular
│   ├── src/                         # Code source
│   ├── angular.json                 # Configuration Angular
│   ├── package.json                 # Dépendances Node.js
│   └── tsconfig.json               # Configuration TypeScript
├── env/                            # Environnement virtuel Python
└── README.md                       # Ce fichier
```

## 🔑 Fonctionnalités Principales

- **Gestion des Candidats** : Enregistrer et gérer les candidats stagiaires
- **Traitement de Documents** : Traitement automatique des CV et CIN avec OCR
- **Gestion des Stages** : Créer et suivre les stages
- **Génération de Documents** : Génération automatique de documents de stage (DOCX/PDF)
- **Authentification des Utilisateurs** : Système de connexion sécurisé
- **Téléchargement de Fichiers** : Support pour les fichiers PDF, DOCX et images

**Problèmes CORS** : Assurez-vous que `CORS_ALLOW_ALL_ORIGINS = True` dans les paramètres Django pour le développement