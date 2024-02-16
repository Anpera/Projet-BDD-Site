import db
import secrets
import time
import datetime as dt
from flask import Flask, render_template, request, redirect, url_for, session, flash
from passlib.context import CryptContext
import psycopg2.sql as sql

app = Flask(__name__)
# secrets.token_hex() pour générer clé
app.secret_key = b'852d30325a3a4fdb98928bf12977b40256825b9e18440429d6007e1f103c56dd'
password_ctx = CryptContext(schemes=['bcrypt'])

@app.route("/accueil")
def accueil():
    return render_template("accueil.html", accueil = 1)

@app.route("/")
def renvoiaccueil():
    return redirect(url_for("accueil"))

@app.route("/connexion")
def connexion(erreur = ""):
    return render_template("connexion.html", connexion = 1, erreur_connexion = erreur)

@app.route("/connecting", methods=['POST'])
def connecting():
    with db.connect() as conn:
        with conn.cursor() as cur:
            adresse = request.form.get("adresse")
            mdp = request.form.get("mdp")
            cur.execute(""" --sql
                SELECT mdp FROM personne WHERE email = %s;""",
                (adresse,)
            )
            result = cur.fetchall()
            if result == []:
                return connexion("Votre adresse-email n'existe pas.")
            
            elif password_ctx.verify(mdp, result[0].mdp):
                cur.execute(""" --sql
                SELECT idp from adherent where idp = %s;""",(adresse,))
                result = cur.fetchone()
                if result:
                    session['adherent'] = True

                if adresse == 'administrateur.niture@gmail.com':
                    session['admin'] = True
                session['profil'] = adresse
                return redirect(url_for("profil"))
            
            return connexion("Le mot de passe entré est erroné.")

@app.route("/profil")
def profil():
    if 'profil' in session:
        with db.connect() as conn:
            with conn.cursor() as cur:
                timed = time.localtime()
                date = dt.date(timed.tm_year, timed.tm_mon, timed.tm_mday)
                cur.execute(""" --sql
                        SELECT email, prenom, nom, telephonep, spe
                        FROM personne LEFT JOIN specialisation ON specialisation.idp = email 
                        WHERE email=%s
                        ORDER BY spe ASC;""", (session['profil'],))
                result = cur.fetchall()
                compte = result[0]
                spe = [tuples.spe for tuples in result]

                cur.execute(""" --sql
                SELECT count(id_sortie) AS nbsort, sum(nb_km) AS totalkm
                FROM SORTIE NATURAL JOIN inscrit
                WHERE idp=%s
                and daterdv < %s
                ;""", (session['profil'], date))
                activites = cur.fetchone()

        return render_template("profil.html", profil = compte, specialisation = spe, connexion = 1, activites = activites)
    return redirect(url_for('connexion'))

@app.route("/historique")
def historique():
    if session['profil']:
        with db.connect() as conn:
            with conn.cursor() as cur:
                timed = time.localtime()
                date = dt.date(timed.tm_year, timed.tm_mon, timed.tm_mday)
                cur.execute(""" --sql
                    SELECT theme, lieu, TO_CHAR(daterdv, 'dd/mm/yyyy') AS daterdv, nb_km FROM sortie NATURAL JOIN inscrit
                    WHERE idp = %s
                    AND daterdv <= %s
                    ORDER BY daterdv DESC;""", 
                    (session['profil'], date))
                result = cur.fetchall()
                return render_template("historique.html", resultat = result)

    return redirect(url_for(connexion))

@app.route("/deconnexion")
def deconnexion():
    if 'adherent' in session:
        session.pop('adherent')
    if 'admin' in session:
        session.pop('admin')
    session.pop('profil')
    return redirect(url_for("connexion"))

@app.route("/sorties")
def sorties():
    with db.connect() as conn:
        with conn.cursor() as cur:
            timed = time.localtime()
            date = dt.date(timed.tm_year, timed.tm_mon, timed.tm_mday)
            try:
                if session['profil']:
                    adresse = session['profil']
            except:
                adresse = "Adresse qui n'existe pas"
            # Vrai code à mettre
            cur.execute(""" --sql
                With tablesortie AS(
                    SELECT id_sortie, theme, lieu, daterdv, nb_km, effectif_max, count(distinct idp) AS effectif
                    FROM sortie NATURAL LEFT JOIN inscrit
                    WHERE daterdv > %s
                    GROUP BY id_sortie, theme, lieu, daterdv, nb_km, effectif_max
                    ORDER BY daterdv
                ), inscritsortie AS(
                    SELECT * from inscrit where idp = %s)
                SELECT id_sortie, theme, lieu, TO_CHAR(daterdv, 'dd/mm/yyyy') AS daterdv, nb_km, effectif_max, effectif, idp, animateur  
                from tablesortie natural left join inscritsortie;""", 
                (date, adresse))
            result = cur.fetchall()
            return render_template("sortie.html", sortie = 1, resultat = result)

@app.route("/inscriptionsortie" , methods = ['POST'])
def inscriptionsortie():
    try:
        if session['adherent']:
            sortie = request.form.get("inscription", None)
            with db.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(""" --sql
                        SELECT * 
                        FROM inscrit 
                        WHERE idp = %s 
                        AND id_sortie=%s;""", 
                        (session['profil'], sortie))
                    result = cur.fetchall()
                    if result == []:
                        #inscription
                        cur.execute(""" --sql
                            INSERT INTO inscrit(idp, id_sortie)
                            VALUES (%s, %s);""",
                            (session['profil'], sortie))
                    else:
                        #désinscription
                        cur.execute(""" --sql
                        DELETE FROM inscrit
                        WHERE idp = %s
                        AND id_sortie = %s;""",
                        (session['profil'], sortie))
    except:
        pass
    return redirect(url_for("sorties"))

@app.route("/freqObs")
def freqObs():
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(""" --sql
            SELECT * FROM nichoir NATURAL JOIN frequenceObs;
            """)
            result = cur.fetchall()
    return render_template("frqObs.html", frequence = result, frequenceObs = 1)

@app.route("/freqEsp")
def freqEsp():
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(""" --sql
            SELECT * FROM nichoir NATURAL JOIN frequenceEsp;
            """)
            result = cur.fetchall()
    return render_template("frqEsp.html", frequence = result, frequenceEsp = 1)

@app.route("/inscription")
def inscriptionP():
    if 'profil' in session:
        if 'admin' in session:
            with db.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(""" --sql
                        SELECT spe FROM specialite
                    ORDER BY spe ASC;""")
                    spe = cur.fetchall()
                    cur.execute(""" --sql
                        SELECT * FROM statut
                    ;""")
                    statut = cur.fetchall()
                    
            return render_template("inscription.html", inscription= 1,
            listeStatut = statut, specialite = spe)
    return redirect(url_for('accueil'))


@app.route("/ajoutInscrit", methods=['POST'])
def ajoutInscrit():
    adresse = request.form.get("adresse")
    prenom = request.form.get("prenom")
    nom = request.form.get("nom")
    telephonep = request.form.get("telephone")
    mdp = password_ctx.hash(prenom)
    statut = None
    specialites = None

    try:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(""" --sql
                INSERT INTO personne
                VALUES (%s, %s, %s, %s, %s)
                ;""", (adresse, prenom, nom, telephonep, mdp))

        if request.form.get("adhe") == 'Oui':
            statut = request.form.get('statut')
            specialites = request.form.getlist('spe')
            moyen = request.form.get("moyen")

            if statut == 'None' or moyen is None:
                with db.connect() as conn:
                    with conn.cursor() as cur:
                        cur.execute(""" --sql
                        DELETE FROM personne
                        WHERE email = %s;""",
                        (adresse,))
                        
                if statut == 'None':
                    flash("Vous n'avez pas préciser le statut de l'adhérent.")
                if moyen is None:
                    flash("Vous n'avez pas préciser le moyen de paiement de l'adhérent.")
                return redirect(url_for("inscriptionP"))

            with db.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(""" --sql
                    INSERT INTO adherent(idp, idstatut, moyenpaiement)
                    VALUES (%s, %s, %s)
                    ;""", (adresse, statut, moyen))

            if specialites != [] and specialites != ['None']:
                with db.connect() as conn:
                    with conn.cursor() as cur:
                        for spe in specialites:
                            if spe != 'None':
                                cur.execute(""" --sql
                                INSERT INTO specialisation
                                VALUES (%s, %s)
                                ;""", (adresse, spe))
        flash("Inscription réussie !")
        
    except:
        flash("Inscription échoué, l'adresse e-mail est déjà utilisée.")
    return redirect(url_for('inscriptionP'))

@app.route("/listeInscrit")
def listeInscrit():
    if 'profil' in session:
        if 'admin' in session:
            with db.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(""" --sql
                    SELECT email, prenom, nom, telephonep
                    FROM personne
                    WHERE email <> 'administrateur.niture@gmail.com'
                    EXCEPT
                    SELECT email, prenom, nom, telephonep
                    FROM personne 
                    JOIN adherent ON email = idp
                    ORDER BY email ASC;""")
                    resultat = cur.fetchall()
            return render_template("listeInscrit.html", liste = resultat, listeins = 1)
    return redirect(url_for('accueil'))

@app.route("/passageAdherent", methods=['POST'])
def passageAdherent():
    if 'profil' in session:
        if 'admin' in session:
            email = request.form.get("email")

            with db.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(""" --sql
                        SELECT spe FROM specialite
                    ORDER BY spe ASC;""")
                    spe = cur.fetchall()
                    cur.execute(""" --sql
                        SELECT * FROM statut
                    ;""")
                    statut = cur.fetchall()
                    cur.execute(""" --sql
                        SELECT * FROM personne
                        WHERE email = %s;""", (email,))
                    resultat = cur.fetchone()
            return render_template("passageadherent.html", personne = resultat, 
            listeStatut = statut, specialite = spe)

    return redirect(url_for('accueil'))

@app.route("/ajoutAdherent", methods=['POST'])
def ajoutAdherent():
    if 'profil' in session:
        if 'admin' in session:
            email = request.form.get("email")
            statut = request.form.get("statut")
            moyen = request.form.get("moyen")
            specialisation = request.form.getlist("spe")

            if statut == "None" or moyen is None:

                if statut == 'None':
                    flash("Vous n'avez pas préciser le statut de l'adhérent.")

                if moyen is None:
                    flash("Vous n'avez pas préciser le moyen de paiement de l'adhérent.")

                with db.connect() as conn:
                    with conn.cursor() as cur:
                        cur.execute(""" --sql
                        SELECT * from specialite
                        ORDER BY spe ASC;""")
                        spe = cur.fetchall()
                        cur.execute(""" --sql
                            SELECT * FROM statut
                            ;""")
                        statut = cur.fetchall()
                        cur.execute(""" --sql
                            SELECT * FROM personne
                            WHERE email = %s
                        ;""", (email,))
                        resultat = cur.fetchone()

                return render_template("passageadherent.html", listeStatut = statut, 
                    specialite = spe, personne = resultat)

            with db.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(""" --sql
                    INSERT INTO adherent(idp, idstatut, moyenpaiement)
                    VALUES (%s, %s, %s)
                    ;""", (email, statut, moyen))

            if specialisation != [] and specialisation != ['None']:
                with db.connect() as conn:
                    with conn.cursor() as cur:
                        for spe in specialisation:
                            if spe != 'None':
                                cur.execute(""" --sql
                                INSERT INTO specialisation
                                VALUES (%s, %s)
                                ;""", (email, spe))
            return redirect(url_for("listeInscrit"))
    return redirect(url_for('accueil'))

@app.route("/listeAdherent")
def listeAdherent():
    if 'profil' in session:
        if 'admin' in session:
            with db.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(""" --sql
                    SELECT email, prenom, nom, telephonep, idstatut, moyenpaiement, datepaiement
                    FROM personne 
                    JOIN adherent ON email = idp
                    ORDER BY email ASC;""")
                    adherent = cur.fetchall()
                    cur.execute(""" --sql
                    SELECT email, spe
                    FROM personne 
                    JOIN specialisation ON email = idp
                    ORDER BY email ASC, spe ASC;""")
                    spe = cur.fetchall()
            return render_template("listeAdherent.html", listadhe = adherent, listespe = spe, adhe = 1)
    return redirect(url_for('accueil'))

@app.route("/encyclopedie")
def encyclopedie():
    return render_template("encyclopedie.html", encyclopedie = 1)

@app.route("/recherche_via_espece", methods=['GET'])
def recherche_via_espece():
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""--sql
                SELECT nomesp FROM espece
                ;""")
            lstespeces = cur.fetchall()

            nom_esp = request.args.get("espece")

            cur.execute("""--sql
                SELECT nomesp, typeesp, partie, descript FROM caracteristiques
                NATURAL JOIN cara_espece
                NATURAL JOIN espece
                WHERE nomEsp LIKE %s;""",(nom_esp,))
            res = cur.fetchall()
    return render_template("recherche_via_espece.html", lstespeces = lstespeces, esp=nom_esp, res=res, encyclopedie = 1)

@app.route("/recherche_via_caracteristique", methods=['GET'])
def recherche_via_caracteristique():
    with db.connect() as conn:
        with conn.cursor() as cur:
            # Partie récupération du formulaire
            esp = request.args.get("type_esp")
            carac = request.args.getlist("carac")
            print(esp, carac)
            
            # Partie affichage menu déroulant du formulaire
            cur.execute("""--sql
                SELECT DISTINCT typeEsp FROM espece;""")
            type_esp = cur.fetchall()
            cur.execute("""--sql
                SELECT DISTINCT * FROM caracteristiques;""")
            partie_desc = cur.fetchall()
            
            #Recherche dans la base de données l'animal en question
            if esp and carac:
                cur.execute(sql.SQL("""--sql
                    SELECT nomEsp FROM espece
                    NATURAL JOIN cara_espece
                    WHERE typeEsp = {}
                    AND id_cara IN {}GROUP BY nomEspHAVING count(*) = {};""")
                    .format(sql.Literal(esp),sql.Literal(tuple(carac)), sql.Literal(len(carac))))
                    
                esp = cur.fetchall()
                nomesp = [tuples.nomesp for tuples in esp]

                if nomesp:
                    cur.execute(sql.SQL("""--sql 
                    SELECT nomEsp, partie, descript
                    FROM cara_espece
                    NATURAL JOIN caracteristiques
                    WHERE nomEsp in {};""")
                    .format(sql.Literal(tuple(nomesp)))
                    )
                    res = cur.fetchall()
                else:
                    flash("Aucune espece correspond à votre recherche.")
                    res = []
            else: 
                res = []
            print(res)
    return render_template("recherche_via_caracteristique.html",type=type_esp, partie_desc = partie_desc, 
    resultat = res, esp = esp, ecr_esp=esp, encyclopedie = 1) 

@app.route("/CreaSortie")
def creasortie():
    timed = time.localtime()
    date = dt.date(timed.tm_year, timed.tm_mon, timed.tm_mday) + dt.timedelta(days=1)
    return render_template("creasortie.html", today=date, creasortie = 1)

@app.route("/ajoutSortie", methods = ['POST'])
def ajoutsortie():
    theme = request.form.get("theme")
    lieu = request.form.get("lieu")
    date = request.form.get("dateS")
    distance = request.form.get("distance")
    effectif = request.form.get("effectif")
    
    try:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(""" --sql
                INSERT INTO sortie(theme,lieu,daterdv,nb_km,effectif_max)
                VALUES (%s,%s,%s,%s,%s);
                """, (theme, lieu, date, distance, effectif))
            flash("Sortie créée avec succès !")
    except:
        flash("Une erreur est survenue lors de la création de la sortie,\
            veuillez vérifier vos paramètres et réessayer.")
        flash("Si le problème persiste, contactez un opérateur pour résoudre le problème.")
    return redirect(url_for("creasortie"))

@app.route("/sortieAdmin")
def sortieadmin():
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(""" --sql
                With tablesortie AS(
                SELECT id_sortie, theme, lieu, daterdv, nb_km, effectif_max, count(idp) AS effectif
                FROM sortie NATURAL LEFT JOIN inscrit
                WHERE archive = false
                GROUP BY id_sortie, theme, lieu, daterdv, nb_km, effectif_max
                ORDER BY daterdv
                )
                SELECT id_sortie, theme, lieu, TO_CHAR(daterdv, 'dd/mm/yyyy') AS daterdv, nb_km, effectif_max, effectif
                FROM tablesortie
                ;""")
            result = cur.fetchall()
            return render_template("sortieadmin.html", liste = result, listesorties = 1)

@app.route("/listePar/<id_sortie>")
def listePar(id_sortie):
    if 'profil' in session and 'admin' in session and id_sortie != 0:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(""" --sql
                SELECT email, adherent.idp as adherent, prenom, nom, id_sortie, animateur, archive
                FROM (inscrit JOIN personne ON inscrit.idp = email)
                LEFT JOIN adherent on email = adherent.idp
                NATURAL RIGHT JOIN sortie
                WHERE id_sortie = %s 
                ORDER BY email
                ;""", (id_sortie,))
                result = cur.fetchall()

                cur.execute(""" --sql
                    SELECT email, spe
                    FROM personne 
                    JOIN specialisation ON email = idp
                    ORDER BY email ASC, spe ASC;""")
                spe = cur.fetchall()
                
                return render_template("participantsortie.html", liste = result, listespe = spe)

    else:
        return redirect(url_for("accueil"))


@app.route("/passageAnim", methods=['POST'])
def passageAnim():
    if request.form.get("suppression"):
        email = request.form.get("suppression")
        sortie = request.form.get("sortieid")
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(""" --sql
                DELETE FROM inscrit
                WHERE idp = %s
                AND id_sortie = %s;""",
                (email, sortie))

    else:
        sortie = request.form.get("sortieid")
        email = request.form.get("email")
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(""" --sql
                SELECT animateur FROM inscrit
                WHERE idp = %s
                AND id_sortie = %s;""",
                (email, sortie))

                result = cur.fetchone()

                if result.animateur:
                    cur.execute(""" --sql
                    UPDATE inscrit SET
                    animateur = false
                    WHERE idp = %s
                    AND id_sortie = %s;""",
                    (email, sortie))
                
                else:
                    cur.execute(""" --sql
                    UPDATE inscrit SET
                    animateur = true
                    WHERE idp = %s
                    AND id_sortie = %s;""",
                    (email, sortie))


    return redirect(url_for('listePar', id_sortie=sortie)) 

@app.route("/archivage", methods =['POST'])
def archivage():
    if request.form.get("archive"):
        id_sortie =  request.form.get("archive")
    else:
        id_sortie = 0
    if 'profil' in session and 'admin' in session and id_sortie != 0:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(""" --sql
                UPDATE sortie SET archive = true
                WHERE id_sortie = %s
                ;""", (id_sortie,))

        return redirect(url_for('sortieadmin'))
            
    else:
        return redirect(url_for("accueil"))

@app.route("/NoAdhIns", methods = ['POST'])
def noadhins():
    sortie = request.form.get("sortie")
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(""" --sql
                SELECT distinct email, prenom, nom, telephoneP FROM personne
                WHERE email <> 'administrateur.niture@gmail.com'
                EXCEPT
                SELECT email, prenom, nom, telephoneP FROM personne
                JOIN adherent ON email = adherent.idp
                EXCEPT
                SELECT email, prenom, nom, telephoneP FROM personne
                JOIN inscrit ON email = inscrit.idp
                WHERE id_sortie = %s
                ORDER BY email;""",
                (sortie,))
            result = cur.fetchall()
    return render_template("noadhetosortie.html", liste = result, id_sortie = sortie)

@app.route("/inscripInSortie", methods = ['POST'])
def inscripInSortie():
    email = request.form.get("email")
    sortie = request.form.get("id_sortie")
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(""" --sql
            INSERT INTO inscrit
            VALUES(%s, %s, true);""",
            (email, sortie))
    return redirect(url_for('listePar', id_sortie = sortie))

@app.route("/archive")
def archive():
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(""" --sql
                With tablesortie AS(
                SELECT id_sortie, theme, lieu, daterdv, nb_km, effectif_max, count(idp) AS effectif
                FROM sortie NATURAL LEFT JOIN inscrit
                WHERE archive = true
                GROUP BY id_sortie, theme, lieu, daterdv, nb_km, effectif_max
                ORDER BY daterdv
                )
                SELECT id_sortie, theme, lieu, TO_CHAR(daterdv, 'dd/mm/yyyy') AS daterdv, nb_km, effectif_max, effectif
                FROM tablesortie
                ;""")
            result = cur.fetchall()
            return render_template("sortiearchive.html", liste = result, archivage = 1)

@app.route("/restauration", methods =['POST'])
def restauration():
    if request.form.get("restor"):
        id_sortie =  request.form.get("restor")
    else:
        id_sortie = 0
    if 'profil' in session and 'admin' in session and id_sortie != 0:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(""" --sql
                UPDATE sortie SET archive = false
                WHERE id_sortie = %s
                ;""", (id_sortie,))

        return redirect(url_for('archive'))
            
    else:
        return redirect(url_for("accueil"))

@app.route("/ajoutEncy")
def ajoutEncy():
    return render_template('ajoutEncy.html', ajoutEncyclo = 1)

@app.route("/selecCaracteristiques")
def selecCaracteristiques():
    if 'profil' in session and 'admin' in session:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(""" --sql
                SELECT DISTINCT partie from caracteristiques
                ORDER BY partie
                ;""")
                result = cur.fetchall()

        return render_template("selecCaracteristiques.html", resultat = result)
    return redirect(url_for('accueil'))
    

@app.route("/ajoutCaracteristiques",  methods = ['POST'])
def ajoutCaracteristiques():
    if request.form.get("zone") == "creation":
        partie = request.form.get("partie")
    else:
        partie = request.form.get("zone")

    descript = request.form.get("descr")

    print(partie, descript)

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(""" --sql
            SELECT * FROM caracteristiques
            WHERE partie = %s
            AND descript = %s;""",
            (partie, descript))

            result = cur.fetchall()
            if result !=[]:
                flash("La caractéristique que vous tentez d'ajouter est déjà dans la base de donnée.")
                return redirect(url_for('selecCaracteristiques'))

            cur.execute(""" --sql
            INSERT INTO caracteristiques(partie, descript)
            VALUES (%s, %s);""",
            (partie, descript))
            flash("La caractéristique à été ajouté avec succès !")
    return redirect(url_for('selecCaracteristiques'))

@app.route("/selecEspeces")
def selecEspeces():
    if 'profil' in session and 'admin' in session:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(""" --sql
                SELECT * FROM caracteristiques
                ORDER BY partie, descript
                ;""")
                result = cur.fetchall()

                cur.execute(""" --sql
                SELECT DISTINCT typeesp
                FROM espece
                ORDER BY typeesp
                ;""")
                typeesp = cur.fetchall()

        return render_template("selecEspeces.html", resultat = result, type=typeesp)
    return redirect(url_for('accueil'))

@app.route("/ajoutEspeces", methods = ['POST'])
def ajoutEspeces():

    liste_cara = request.form.getlist('carac')
    nom = request.form.get('espece')
    typeE = request.form.get('typeesp')

    if liste_cara == []:
        flash("Veuillez choisir au moins une caractéristique")
        return redirect(url_for('selecEspeces'))

    try:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(""" --sql
                INSERT INTO espece
                VALUES (%s, %s);""",
                (nom, typeE))
    except:
        flash("Ce nom d'animal a déjà été pris. Veuillez en choisir un autre.")
        return redirect(url_for('selecEspeces'))

    with db.connect() as conn:
        with conn.cursor() as cur:
            for cara in liste_cara:
                cur.execute(""" --sql
                INSERT INTO cara_espece
                VALUES (%s, %s);""",
                (nom, cara))
    
    flash("Espèce ajouté avec succès !")
    return redirect(url_for('selecEspeces'))

@app.route("/observation", methods=['GET'])
def observation():
    return render_template("observation.html", observation = 1)

@app.route("/listeobs")
def listeobs():
    if 'profil' in session:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(""" --sql
                    With lstobs AS(
                        SELECT nomEsp, nbreOccupants, nbreOeufs,
                        (observation.nidification) AS nid, (nichoir.coord_latitude) AS lat, (nichoir.coord_longitude) AS long,
                        (nichoir.hauteur) as ht, (nichoir.support) as support, (nichoir.type_environ) AS envir
                        FROM espece_observe
                        NATURAL JOIN observation NATURAL JOIN observation_adherent NATURAL JOIN nichoir
                        WHERE idP = %s
                        ORDER BY nid ASC
                    )
                    SELECT nomEsp, nbreOccupants, nbreOeufs, TO_CHAR(nid, 'dd/mm/yyyy') AS nid, lat, long, ht, support, envir
                    FROM lstobs
                    ;""",(session['profil'],))
                esp = cur.fetchall()
    return render_template("listeobs.html", espece = esp, observation = 1)

@app.route("/ecritureobs")
def ecritureobs():
    timed = time.localtime()
    date = dt.date(timed.tm_year, timed.tm_mon, timed.tm_mday)
    with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""--sql
                    SELECT nomesp FROM espece
                    ;""")
                lstespeces = cur.fetchall()
    return render_template("ecritureobs.html", today = date, lst_esp = lstespeces, observation = 1)

@app.route("/ajoutobs", methods=['GET', 'POST'])
def ajoutobs():
    if 'profil' in session:
        if 'admin' not in session:
            adresse = session['profil']
            #Récupération des infos du formulaire
            esp = request.form.get("esp")
            date = request.form.get("dateobs")
            nb_occu = request.form.get("nb_occu")
            nb_oeufs = request.form.get("nb_oeufs")
            lat = request.form.get("lat")
            long = request.form.get("long")
            hauteur = request.form.get("hauteur")
            support = request.form.get("support")
            environnement = request.form.get("environnement")
            with db.connect() as conn:
                with conn.cursor() as cur:
                    #Insertion des valeurs des tables puis récupération de leur id pour inserer dans les associations
                    cur.execute(""" --sql
                        INSERT INTO observation(nidification)
                        VALUES (%s)
                        RETURNING id_obs
                        ;""", (date,))
                    recup_obs = cur.fetchone()
                    
                    cur.execute(""" --sql
                        INSERT INTO nichoir(dateInstal, coord_latitude, coord_longitude, hauteur, support, type_environ)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id_nid
                        ;""", (date, lat, long, hauteur, support, environnement))
                    recup_nichoir = cur.fetchone()
                    
                    #Insertion dans les associations
                    cur.execute(""" --sql
                        INSERT INTO espece_observe(id_obs, nomEsp, nbreOccupants, nbreOeufs)
                        VALUES (%s, %s, %s, %s)
                        ;""", (recup_obs, esp, nb_occu, nb_oeufs))
                    
                    cur.execute(""" --sql
                        INSERT INTO observation_adherent(idP, id_nid, id_obs)
                        VALUES (%s, %s, %s)
                        ;""", (adresse, recup_nichoir, recup_obs))                
    return redirect(url_for("ecritureobs"))

@app.errorhandler(404)
def erreur404(error):
    return render_template("error404.html"), 404

@app.errorhandler(405)
def erreur405(error):
    return render_template("error405.html"), 405

if __name__ == '__main__':
    app.run(debug= True)
