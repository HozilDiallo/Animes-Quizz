import streamlit as st

st.set_page_config(
    page_title="Animes Geek",
    page_icon="fav.png",
    layout="wide"
)

import os, json
from Outils.partie_num import load_parties, save_partie, delete_partie, update_partie
from Outils.generateur_question import generate_questions, evaluate_answer
from config import QUESTIONS_DIR
from Outils.manager_stats import get_all_stats, save_quiz_result, delete_note_stats, delete_all_stats

# Application principale

# Sidebar
st.sidebar.title("📝 **AnimesGeek**")
st.sidebar.markdown("<h3>Menu</h3>", unsafe_allow_html=True)
menu = st.sidebar.radio(
    "📂 <span style='color: #0066CC;'>Choisissez une option :</span>",
    ["Dashboard","Prise de Outils", "Mode Quiz", "Performances"],
    format_func=lambda x: f"🔹 {x}",
    index=0,
    label_visibility="hidden",
    key="menu_radio"
)

# Main content
if menu == "Dashboard":
    # Header with custom styles
    st.markdown("<h1>Bienvenue sur _AnimesGeek_ ⚡️</h1>", unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("Ici vous pouvez tester vos connaissances sur les animes ou mangas!")

    # Feature list with emojis and custom formatting
    st.markdown(
        """
        <div style='padding: 10px;'>
            <p><strong>AnimesGeek</strong> vous permet de :</p>
            <ul>
                <li>🗒️ <strong>Classer vos differentes animes</strong> par ordre de préférences.</li>
                <li>❓ <strong>Générer des questions</strong> pour des quizz entre amis.</li>
                <li>✅ <strong>Consulter des quizz faites par d'autres</strong> et de vous tester vous-memes.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

elif menu == "Prise de Outils":
    st.header("Prise de Outils")

    if "parties" not in st.session_state:
        st.session_state.parties = load_parties()

    if "editing_partie" not in st.session_state:
        st.session_state.editing_partie = None

    # Affichage des notes existantes
    st.write("### Vos parties :")
    if st.session_state.parties:
        for partie in st.session_state.parties:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"📝 {partie['title']}")
            with col2:
                if st.button("Voir/Modifier", key=f"edit_{partie['title']}"):
                    st.session_state.editing_partie = partie
            with col3:
                if st.button("Supprimer", key=f"delete_{partie['title']}"):
                    delete_partie(partie['title'])
                    st.session_state.notes = load_parties()
                    if st.session_state.editing_partie and st.session_state.editing_partie['title'] == partie['title']:
                        st.session_state.editing_partie = None
                    st.rerun()

    else:
        st.info("Aucune partie disponible pour le moment.")

    # Section d'édition/visualisation
    if st.session_state.editing_partie:
        st.markdown("---")
        st.subheader(f"Modifier la partie : {st.session_state.editing_partie['title']}")
        edited_content = st.text_area(
            "Contenu de la partie",
            value=st.session_state.editing_partie['content'],
            height=300,
            key="edit_content"
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sauvegarder les modifications"):
                if update_partie(st.session_state.editing_note['title'], edited_content):
                    st.success("Partie mise à jour avec succès!")
                    st.session_state.notes = load_parties()
                    st.session_state.editing_note = None
                    st.rerun()
                else:
                    st.error("Erreur lors de la mise à jour de la Partie")
        with col2:
            if st.button("Annuler"):
                st.session_state.editing_partie = None
                st.rerun()

    # Section pour créer une nouvelle note
    st.markdown("---")
    st.subheader("Créer une nouvelle Partie")
    partie_title = st.text_input("Les noms des Adversaires")
    partie_content = st.text_area("Contenu de la Partie", height=200)
    if st.button("Sauvegarder"):
        if partie_title and partie_content:
            save_partie(partie_title, partie_content)
            st.session_state.notes = load_parties()
            st.success(f"Note '{partie_title}' sauvegardée avec succès !")
            st.rerun()
        else:
            st.warning("Veuillez fournir un titre et un contenu pour votre Partie.")


elif menu == "Mode Quiz":
    st.header("Mode Quiz")

    # Charger les notes disponibles
    parties = load_parties()
    partie_titles = [partie["title"] for partie in parties]
    selected_partie = st.selectbox("Choisissez une partie", partie_titles)

    if selected_partie:
        partie_content = next(partie["content"] for partie in parties if partie["title"] == selected_partie)
        json_file_path = os.path.join(QUESTIONS_DIR, f"{selected_partie}.json")

        # Initialisation des questions
        if "questions" not in st.session_state or st.session_state.get("current_partie") != selected_partie:
            if os.path.exists(json_file_path):
                with open(json_file_path, "r") as file:
                    st.session_state.questions = json.load(file)
            else:
                st.session_state.questions = []
            st.session_state.current_partie = selected_partie
            # Initialiser un dictionnaire pour stocker les réponses
            st.session_state.user_answers = {}

        # Générer de nouvelles questions
        if st.button("Générer des questions"):
            try:
                with st.spinner("Génération des questions en cours..."):
                    new_questions = generate_questions(selected_partie, partie_content)

                if new_questions:
                    with open(json_file_path, "w") as file:
                        json.dump(new_questions, file, indent=4, ensure_ascii=False)

                    st.session_state.questions = new_questions
                    st.session_state.user_answers = {}  # Réinitialiser les réponses
                    st.success("Questions générées et sauvegardées avec succès !")
                else:
                    st.error("L'API n'a retourné aucune question.")
            except Exception as e:
                st.error(f"Une erreur s'est produite : {e}")

        # Afficher les questions
        if st.session_state.questions:
            st.write("### Questions :")

            # Afficher toutes les questions avec des champs de réponse
            for i, question in enumerate(st.session_state.questions, 1):
                st.write(f"**Question {i}:** {question['text']}")
                # Stocker la réponse dans session_state
                answer_key = f"answer_{i}"
                user_answer = st.text_area(
                    "Votre réponse",
                    key=answer_key,
                    height=100
                )
                st.session_state.user_answers[answer_key] = user_answer
                st.markdown("---")
            # Bouton unique pour vérifier toutes les réponses
            if st.button("📝 Vérifier toutes les réponses"):
                total_score = 0
                with st.spinner("Évaluation des réponses en cours..."):
                    for i, question in enumerate(st.session_state.questions, 1):
                        answer_key = f"answer_{i}"
                        user_answer = st.session_state.user_answers.get(answer_key, "")

                        # Évaluer la réponse
                        evaluation = evaluate_answer(
                            question['text'],
                            user_answer,
                            question['reponse']
                        )

                        # Sauvegarder le résultat
                        save_quiz_result(
                            selected_partie,
                            question['text'],
                            user_answer,
                            question['reponse'],
                            evaluation['score']
                        )

                        total_score += evaluation['score']

                        # Afficher le résultat pour cette question
                        with st.expander(f"Résultat Question {i}"):
                            st.write(f"**Votre réponse:** {user_answer}")
                            st.write(f"**Réponse correcte:** {question['reponse']}")
                            st.write(f"**Score:** {evaluation['score']}")

                # Afficher le score total
                nb_points = total_score
                st.success(f"Score total : {nb_points:.1f}")

                # Option pour recommencer
                if st.button("🔄 Recommencer le quiz"):
                    st.session_state.user_answers = {}
                    st.rerun()

            # Bouton pour supprimer les questions
            if st.button("🗑️ Supprimer toutes les questions"):
                try:
                    os.remove(json_file_path)
                    st.session_state.questions = []
                    st.session_state.user_answers = {}
                    st.success("Les questions ont été supprimées avec succès !")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors de la suppression : {e}")

        else:
            st.info("Aucune question disponible. Cliquez sur 'Générer des questions' pour commencer.")

elif menu == "Performances":
    st.header("📊 Evolution de vos parties")

    stats = get_all_stats()
    if not stats:
        st.info(
            "Aucune statistique disponible pour le moment. Commencez à répondre à des quiz pour voir votre niveaux !")
    else:
        # Vue d'ensemble globale
        st.subheader("Vue d'ensemble")

        # Calculer les statistiques globales
        all_scores = []
        parties_nb_points = {}
        for partie_title, partie_stats in stats.items():
            if partie_stats["attempts"]:
                scores = [attempt["score"] for attempt in partie_stats["attempts"]]
                parties_nb_points[partie_title] = sum(scores) / len(scores)
                all_scores.extend(scores)

        # Afficher le score moyen global
        if all_scores:
            global_avg = sum(all_scores) / len(all_scores)
            st.metric("Score moyen global", f"{global_avg:.1f}")

            # Graphique des scores moyens par note
            st.bar_chart(parties_nb_points)

        # Détails par note
        st.subheader("Détails par note")
        for partie_title, partie_stats in stats.items():
            with st.expander(f"📝 {partie_title}"):
                if partie_stats["attempts"]:
                    col1, col2 = st.columns(2)

                    # Statistiques de base
                    scores = [attempt["score"] for attempt in partie_stats["attempts"]]
                    avg_score = sum(scores) / len(scores)
                    with col1:
                        st.metric("Meilleur score", f"{max(scores)}")
                    with col2:
                        st.metric("Nombre de questions", len(scores))

                    # Graphique d'évolution des scores
                    scores_df = {
                        "Question": range(1, len(scores) + 1),
                        "Score": scores
                    }
                    st.line_chart(scores_df, x="Question", y="Score")

                    # Historique détaillé
                    st.write("### Historique détaillé")
                    for attempt in reversed(partie_stats["attempts"]):
                        st.markdown(f"""
                        **📅 {attempt['timestamp'][:16].replace('T', ' à ')}**
                        - **Question:** {attempt['question']}
                        - **Votre réponse:** {attempt['user_answer']}
                        - **Réponse correcte:** {attempt['correct_answer']}
                        - **Score:** {attempt['score']}/5
                        ---
                        """)

                    # Bouton pour supprimer l'historique de cette note
                    if st.button("🗑️ Supprimer l'historique", key=f"delete_{partie_title}"):
                        if delete_partie(partie_title):
                            st.success(f"Historique supprimé pour {partie_title}")
                            st.rerun()
                        else:
                            st.error("Erreur lors de la suppression de l'historique")

        # Bouton pour supprimer tout l'historique
        st.markdown("---")
        if st.button("🗑️ Supprimer tout l'historique", type="secondary"):
            if delete_all_stats():
                st.success("Tout l'historique a été supprimé")
                st.rerun()
            else:
                st.error("Erreur lors de la suppression de l'historique")



# Divider
st.markdown("---")


st.markdown("### 🌟 Notre Chaine Whatshapp :")
# Align the buttons horizontally
col1, col2 = st.columns(2)
with col1:
    st.link_button("👍 Chaine Whatshapp", url="https://chat.whatsapp.com/Dk6RaJw6PsOEyJnIxCIrs8")
with col2:
    st.text("👍 Made by Hozil")
