-- Schéma de la base de Cétolog.
-- Explications : backend/README.md
-- PostgreSQL avec l'extension pgvector. À lancer une seule fois.

CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Les photos et leurs métadonnées : une ligne par photo, les colonnes du manifeste
CREATE TABLE photos (
    id              serial PRIMARY KEY,
    jeu             text NOT NULL CHECK (jeu IN ('catalogue', 'best_of', 'historique')),
    livraison       text NOT NULL,          -- nom du zip, sans extension
    fichier_origine text NOT NULL,          -- nom de la photo, tel que reçu
    individu        text NOT NULL,          -- TUTRxxxx, ou INDx dans un best-of
    cote            char(1) CHECK (cote IN ('D', 'G')),
    date            date,                   -- celle du nom, à défaut celle de l'EXIF
    sha256          text NOT NULL,
    anomalies       text,
    UNIQUE (jeu, sha256)                    -- une photo identique n'entre qu'une fois par jeu
);

-- 2. Les empreintes : une ligne par photo et par modèle
CREATE TABLE empreintes (
    photo_id int  NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    modele   text NOT NULL,                 -- cetaceanet, miewid…
    vecteur  vector NOT NULL,               -- de norme 1 ; sans dimension fixe, pour plusieurs modèles
    PRIMARY KEY (photo_id, modele)
);

-- 3. Les propositions : le top 10 des dauphins du catalogue pour chaque individu d'un best-of
CREATE TABLE propositions (
    best_of    text NOT NULL,               -- la livraison du best-of
    individu   text NOT NULL,               -- INDx
    modele     text NOT NULL,
    rang       int  NOT NULL,
    candidat   text NOT NULL,               -- TUTRxxxx
    score      real NOT NULL,               -- le meilleur cosinus, tous côtés confondus
    cosinus_d  real,
    cosinus_g  real,
    calcule_le timestamptz DEFAULT now(),
    PRIMARY KEY (best_of, individu, modele, rang)
);
