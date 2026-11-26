# Frontend Cetolog (`frontend/`)

Application web **Next.js** (TypeScript, App Router) du projet Cetolog.

## Prérequis

- [Node.js](https://nodejs.org/) (version LTS recommandée)
- `npm`

## Installation et lancement en local

Depuis le dossier `frontend/` :

```bash
# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev
```

Ouvrir [http://localhost:3000](http://localhost:3000) dans le navigateur.

Next.js ne lit les fichiers `.env*` que dans `frontend/`. Une seule fois par clone, créer un lien vers le `.env` racine (jamais versionné, déjà ignoré par `.gitignore`) :

```bash
cd frontend
ln -s ../.env .env.local
```

Puis lancer simplement `npm run dev`. Next lit `.env.local` sans passer par le shell : les valeurs ne sont pas évaluées comme du code et il n’y a qu’une seule source de secrets. Sans ce lien, la page affiche « Variables S3 manquantes » : c’est attendu.

Sans lien symbolique possible (Windows), copier le fichier une fois avec `cp ../.env .env.local`, puis le recopier à chaque modification du `.env` racine.

## Commandes utiles

```bash
npm run dev           # Serveur de développement (http://localhost:3000)
npm run build         # Build de production
npm run start         # Serveur de production (après build), écoute sur 0.0.0.0:$PORT
npm run lint          # Vérification ESLint
npm run format        # Formater les fichiers avec Prettier
npm run format:check  # Vérifier le formatage sans modifier les fichiers
```

## Déploiement sur Clever Cloud

### 1) Installer Clever Tools

```bash
# Option recommandée (si npm est installé)
npm install -g clever-tools

# Vérifier l'installation
clever version
```

### 2) Se connecter à Clever Cloud

```bash
clever login
```

La commande ouvre le navigateur pour l’authentification. Pour vérifier le compte connecté :

```bash
clever profile
```

### 3) Lier le repo à l’application Clever Cloud

Informations de l’application **cetolog-web** :

- **Alias** : `cetolog-web`
- **ID** : `app_78d5280a-4316-48dd-90b1-4e61132eb0ab`

Depuis la racine du repo :

```bash
cd /Users/dams/Projects/cetolog
clever link app_78d5280a-4316-48dd-90b1-4e61132eb0ab
```

Vérifier le lien :

```bash
clever status
```

### 6) Déployer une branche

`clever deploy` déploie le **commit Git courant**. Pour déployer une branche, place-toi dessus, commite tes changements, puis déploie :

```bash
# Depuis la racine du repo
git checkout nom-de-ma-branche
git add .
git commit -m "mon message de commit"
clever deploy
```

Suivre les logs de déploiement :

```bash
clever logs
```

## Remarques

- Le fichier `.env` local ne doit pas être commité. Les variables de déploiement Clever Cloud se configurent côté Clever Cloud, pas dans le repo.
- En cas de souci de déploiement, vérifier d’abord : `CC_APP_FOLDER`, la commande `start`, la version Node, le hook de build et les logs Clever Cloud.
