CREATE TABLE personne(
    email varchar(40) PRIMARY KEY,
    prenom varchar(25) NOT NULL,
    nom varchar(25) NOT NULL,
    telephoneP char(10),
    mdp varchar(100)
);

CREATE TABLE statut(
    idStatut varchar(25) PRIMARY KEY,
    montant int
);

CREATE TABLE adherent(
    idP varchar(40) UNIQUE REFERENCES personne(email)
    ON DELETE CASCADE ON UPDATE CASCADE,
    idStatut varchar(25) REFERENCES statut(idStatut)
    ON DELETE CASCADE ON UPDATE CASCADE,
    moyenPaiement varchar(11),
    datePaiement date default now(),
    PRIMARY KEY (idP, idStatut)
);

CREATE TABLE specialite(
    spe varchar(25) PRIMARY KEY
);

CREATE TABLE specialisation(
    idP varchar(40) REFERENCES personne(email)
    ON DELETE CASCADE ON UPDATE CASCADE,
    spe varchar(25) REFERENCES specialite(spe)
    ON DELETE RESTRICT ON UPDATE CASCADE,
    PRIMARY KEY (idP, spe)   
);

CREATE TABLE sortie(
    id_sortie serial PRIMARY KEY,
    theme text,
    lieu varchar(50),
    dateRDV date,
    nb_km numeric(4,2) CHECK (nb_km >= 0),
    effectif_max int CHECK (effectif_max >= 20),
    archive boolean default false
);

CREATE TABLE inscrit(
    idP varchar(40) REFERENCES personne(email)
    ON DELETE CASCADE ON UPDATE CASCADE,
    id_sortie int REFERENCES sortie(id_sortie)
    ON DELETE CASCADE,
    animateur boolean default false,
    PRIMARY KEY (idP, id_sortie)
);

CREATE TABLE nichoir(
    id_nid serial PRIMARY KEY,
    dateInstal date NOT NULL,
    coord_latitude float NOT NULL,
    coord_longitude float NOT NULL,
    hauteur int NOT NULL,
    support varchar(25),
    type_environ text
);

CREATE TABLE espece(
    nomEsp varchar(25) PRIMARY KEY,
    typeEsp varchar(15)
);

CREATE TABLE caracteristiques(
    id_cara serial PRIMARY KEY,
    partie varchar(15),
    descript varchar(25)
);

CREATE TABLE cara_espece(
    nomEsp varchar(25) REFERENCES espece(nomEsp)
    ON DELETE CASCADE ON UPDATE CASCADE,
    id_cara int REFERENCES caracteristiques(id_cara)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
    PRIMARY KEY (nomEsp,id_cara)
);

CREATE TABLE observation(
    id_obs serial PRIMARY KEY,
    nidification date default now()
);

CREATE TABLE espece_observe(
    id_obs int REFERENCES observation(id_obs)
    ON DELETE CASCADE ON UPDATE CASCADE,
    nomEsp varchar(25) REFERENCES espece(nomEsp)
    ON DELETE CASCADE ON UPDATE CASCADE,
    nbreOccupants int CHECK (nbreOccupants >= 0),
    nbreOeufs int CHECK (nbreOeufs >= 0),
    PRIMARY KEY (id_obs, nomEsp)    
);

CREATE TABLE observation_adherent(
    idP varchar(40) REFERENCES personne(email)
    ON DELETE CASCADE ON UPDATE CASCADE,
    id_nid int REFERENCES nichoir(id_nid)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
    id_obs int REFERENCES observation(id_obs)
    ON DELETE CASCADE ON UPDATE CASCADE,
    PRIMARY KEY (idP, id_nid, id_obs)
);


CREATE VIEW frequenceEsp AS (
    WITH freqstats AS (
        SELECT id_nid, nomEsp, count(distinct id_obs) AS frequence
        FROM espece_observe NATURAL JOIN observation_adherent
        GROUP BY id_nid, nomEsp
        ORDER BY id_nid, frequence DESC
    )
    SELECT frq1.id_nid, frq1.nomEsp, frq1.frequence
    FROM freqstats AS frq1
    WHERE frq1.frequence = ( 
        SELECT max(frq2.frequence)
        FROM freqstats AS frq2
        WHERE frq1.id_nid = frq2.id_nid
    ) 
    ORDER BY frequence desc, id_nid, nomEsp
);

CREATE VIEW frequenceObs AS (
    SELECT id_nid, count(distinct id_obs) AS frequence, EXTRACT(MONTH FROM observation.nidification) as mois, EXTRACT(YEAR FROM observation.nidification) as annee
    FROM observation_adherent NATURAL JOIN observation
    GROUP BY id_nid, EXTRACT(MONTH FROM observation.nidification), EXTRACT(YEAR FROM observation.nidification)
    ORDER BY annee desc, mois desc, frequence DESC
);

COPY personne FROM STDIN csv;
administrateur.niture@gmail.com,Administrateur,Niture,0845963425,$2b$12$B/E5vgUXxpTTUGskoxDiq.wbifBJdyuf4ug.K9L.2nM/vqqPUKzpW
roberto.tourette@gmail.com,Roberto,Tourette,0438573999,$2b$12$uibHwrvVnH3fHxbaPGKg6uS.N/.g/U2qVpOCxFdQz7rZTCaWvbilq
benjamin.pepin@hotmail.com,Benjamin,Pepin,0519276677,$2b$12$Bbxfp3Mm42WSYM5pOlHIuuKKaFMqPQF9HJfBV6sRcRewjDeL0lwO2
hardouinlaforest@rhyta.com,Hardouin,Laforest,0448623242,$2b$12$fUcBMc3GDVKS2.qMTgW3mOSzD/sV2pRjVf5/NJno0n0zYbjF60/V.
elisabethboisvert@dayrep.com,Elisabeth,Boisvert,0476083772,$2b$12$e0s38Q9yY4C8FAg5vGO1cO2SdRxBlJkTCw2p0Fk6cGu6Iaf7xK9Em
germainelussier@rhyta.com,Germaine,Lussier,0316174295,$2b$12$7qNeGQV0QCy8aMK5vHZSTucmW6JSLBelxUls8uHXymUbkaE34aJHO
mariaddeangelis@armyspy.com,Maria,Deangelis,0860613625,$2b$12$CFRm9mv.EejpH3yKgPlNW.wmB15cSA5I7QUKS8ZB0uhJVtZQ8hIgC
tillyboulanger@rhyta.com,Tilly,Boulanger,0167305228,$2b$12$e3f8BPyNCa7fMSp0rtw8g.eqUfl4XkJRQvPUpirktbYIC2Eq7081W
albraccalesperance@armyspy.com,Albracca,Lesperance,0430487541,$2b$12$X9edUuRl53ky5H./AOqFxOUEhT.LbrvIwanNhEcJpqrBTYvrbEFg6
hollylaprise@dayrep.com,Holly,Laprise,0206613399,$2b$12$RDfi8w25b9jenKhOHo.KZOe9ojXQ//qBhJGjK4W/NmUtqyj7rb.DO
leonpelland@armyspy.com,Leon,Pelland,0218521026,$2b$12$ja9wH.A1yxgo.8oqe3INbeUYILFN20jGaca3lfxlXfI9aSms5RIyC
jean-paul.smith@gmail.com,Jean-Paul,Smith,0136587623,$2b$12$lo4hEGAUFbzaI6xZiWx6putjYPpDcYhQR3gfmVBX6SWOfqBsZAQBm
\.

COPY statut FROM STDIN csv;
etudiant,10
personnel,30
exterieur,100
\.

COPY adherent FROM STDIN csv;
roberto.tourette@gmail.com,etudiant,espece,2021-06-10
benjamin.pepin@hotmail.com,exterieur,cheque,2022-01-03
hardouinlaforest@rhyta.com,personnel,CB,2021-10-23
elisabethboisvert@dayrep.com,personnel,cheque,2021-09-11
germainelussier@rhyta.com,exterieur,espece,2021-06-09
mariaddeangelis@armyspy.com,etudiant,CB,2022-04-20
tillyboulanger@rhyta.com,exterieur,espece,2021-07-10
jean-paul.smith@gmail.com,exterieur,CB,2021-05-01
\.

COPY specialite FROM STDIN csv;
ornithologie
photographie
botanique
garde_forestier
guide
\.

COPY specialisation FROM STDIN csv;
roberto.tourette@gmail.com,ornithologie
roberto.tourette@gmail.com,photographie
roberto.tourette@gmail.com,botanique
benjamin.pepin@hotmail.com,garde_forestier
benjamin.pepin@hotmail.com,guide
elisabethboisvert@dayrep.com,botanique
mariaddeangelis@armyspy.com,ornithologie
tillyboulanger@rhyta.com,ornithologie
\.

COPY sortie(theme, lieu, daterdv, nb_km, effectif_max) FROM STDIN csv;
Les rapaces,Le Parc aux Rapaces de Madiran,2022-11-29,5.4,50
Plantes et insectes du milieu aquatiques,L'Aquarium marin de Tregastel,2019-07-14,7.9,35
Comment installer un nichoir,Parc Naturel régional de l'Aubrac,2023-08-07,10.5,20
\.

COPY inscrit FROM STDIN csv;
roberto.tourette@gmail.com,1,true
roberto.tourette@gmail.com,2,false
roberto.tourette@gmail.com,3,true
benjamin.pepin@hotmail.com,2,false
benjamin.pepin@hotmail.com,3,true
hardouinlaforest@rhyta.com,1,true
elisabethboisvert@dayrep.com,1,false
elisabethboisvert@dayrep.com,2,false
germainelussier@rhyta.com,2,false
mariaddeangelis@armyspy.com,2,false
mariaddeangelis@armyspy.com,3,false
tillyboulanger@rhyta.com,2,false
tillyboulanger@rhyta.com,1,false
hollylaprise@dayrep.com,2,true
\.

COPY nichoir(dateInstal, coord_latitude, coord_longitude, hauteur, support, type_environ) FROM STDIN csv;
2017-07-24,48.701569,2.43909,30,Bois,Forêt
2016-04-13,48.3974860,0.67280249,20,Bois,Plaine
\.

COPY espece FROM STDIN csv;
Héron cendré,oiseau
Faucon crécerelle,oiseau
Pigeon biset,oiseau
Canard de Duclair,oiseau
Dionée attrape_mouche,plante
Sabline des chaumes,plante
Ricin,plante
Renard roux,mammifères
Sanglier d'Europe,mammifères
Loup gris,mammifères
\.

COPY caracteristiques(partie, descript) FROM STDIN csv;
gorge,rouge
gorge,blanc
plumage,noir
plumage,blanc
plumage,gris
plumage,orange
fleurs,blanche
feuilles,verte
feuilles,rouges
fourrure,gris
fourrure,orange
\.

COPY cara_espece FROM STDIN csv;
Héron cendré,1
Faucon crécerelle,6
Pigeon biset,5
Canard de Duclair,2
Canard de Duclair,3
Dionée attrape_mouche,8
Sabline des chaumes,7
Ricin,8
Renard roux,11
Loup gris,10
\.

COPY observation(nidification) FROM STDIN csv;
2018-03-08
2018-03-13
2019-01-03
2019-06-24
2020-09-04
2020-10-31
2021-04-14
2021-04-26
2022-08-28
2022-07-20
\.

COPY espece_observe FROM STDIN csv;
1,Héron cendré,2,5
2,Héron cendré,1,3
3,Faucon crécerelle,0,3
3,Héron cendré,1,0
4,Canard de Duclair,2,0
5,Dionée attrape_mouche,1,0
6,Ricin,2,0
7,Renard roux,2,0
7,Sanglier d'Europe,1,0
8,Loup gris,7,0
\.

COPY observation_adherent FROM STDIN csv;
roberto.tourette@gmail.com,1,1
roberto.tourette@gmail.com,2,2
benjamin.pepin@hotmail.com,1,3
hardouinlaforest@rhyta.com,2,4
mariaddeangelis@armyspy.com,1,5
tillyboulanger@rhyta.com,2,6
albraccalesperance@armyspy.com,1,7
albraccalesperance@armyspy.com,1,8
hollylaprise@dayrep.com,2,9
leonpelland@armyspy.com,1,10
\.
