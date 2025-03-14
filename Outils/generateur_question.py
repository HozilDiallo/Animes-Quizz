import os
import re
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
from sympy.physics.units import seconds

from config import QUESTIONS_DIR, QUESTIONS_FILE

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
load_dotenv()

# Configuration API
api_key = os.getenv("DEEPSEEK_KEY")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)

def generate_questions(note_title, note_content):
    """
    Génère des questions à partir du contenu des notes en utilisant l'API DeepSeek.
    :param note_title: Titre de la note
    :param note_content: Contenu de la note
    :return: Une liste de questions générées
    """
    try:
        prompt = (
            f"À partir de cette question, crée une séries de questions relativement ouvertes qui permettent de savoir si un joueur connait les animés. "
            f"Tu choisiras 10 questions en fonction de l'information donnée.\n"
            f"Les questions que tu choisiras doivent etre des QCM (Question à Choix Multiples).\n"
            f"Pour chaque question, retourne un JSON avec deux clés : "
            f"'text' pour la question et 'reponse' pour la réponse correcte.\n"
            f"Texte : {note_content}\n"
            f"Retourne uniquement du JSON, rien d'autre."
        )

        # Envoyer la requête à l'API
        response = client.chat.completions.create(
            extra_body={},
            model="deepseek/deepseek-chat",
            messages=[
                {"role": "user", "content": prompt},
            ],
        )

        # Vérification de la réponse
        logging.info("Réponse brute de l'API : %s", response)
        generated_text = response.choices[0].message.content.strip()
        if generated_text.startswith("```json") and generated_text.endswith("```"):
            generated_text = generated_text.strip("```json").strip("```")
        if not generated_text:
            raise ValueError("Réponse vide retournée par l'API.")

        # Chargement du JSON
        try:
            questions = json.loads(generated_text)
        except json.JSONDecodeError as json_err:
            logging.error("Erreur lors de l'analyse du JSON : %s", json_err)
            raise ValueError("La réponse de l'API n'est pas un JSON valide.")

        # Sauvegarder les questions dans un fichier JSON
        json_file_path = os.path.join(QUESTIONS_DIR, f"{note_title}.json")
        with open(json_file_path, "w") as file:
            json.dump(questions, file, indent=4, ensure_ascii=False)
        logging.info("Questions sauvegardées dans : %s", json_file_path)
        return questions

    except Exception as e:
        logging.error("Erreur lors de la génération des questions : %s", e)
        return []


def save_questions(questions):
    """
    Sauvegarde les questions générées dans un fichier JSON.
    :param questions: Liste des questions
    """
    try:
        if not os.path.exists(os.path.dirname(QUESTIONS_FILE)):
            os.makedirs(os.path.dirname(QUESTIONS_FILE))
        with open(QUESTIONS_FILE, "w") as file:
            json.dump(questions, file, indent=4)
        logging.info("Questions sauvegardées dans le fichier principal : %s", QUESTIONS_FILE)
    except Exception as e:
        logging.error("Erreur lors de la sauvegarde des questions : %s", e)


def load_questions():
    """
    Charge les questions sauvegardées à partir du fichier JSON.
    :return: Liste des questions
    """
    try:
        if os.path.exists(QUESTIONS_FILE):
            with open(QUESTIONS_FILE, "r") as file:
                return json.load(file)
    except Exception as e:
        logging.error("Erreur lors du chargement des questions : %s", e)
    return []


def evaluate_answer(question, user_answer, correct_answer):
    """
    Évalue la réponse de l'utilisateur en utilisant l'API
    """
    try:
        prompt = (
            f"Tu es un bot qui évalue une réponse d'un joueur de manière bienveillante.\n"
            f"Question: {question}\n"
            f"Minuteur: {seconds}\n"
            f"Réponse correcte: {correct_answer}\n"
            f"Réponse du joueur: {user_answer}\n\n"
            f"Règles d'évaluation:\n"
            f"- Apres la generation des questions un minuteur est lancé.\n"
            f"- Une seule réponse est possible pour chaque question.\n"
            f"- Chaque réponse est noté score de 2 points.\n"
            f"- Chaque réponse juste, mérite 2 points sinon il ne mérite 0 points.\n"
            f"- A la fin tu calcule le temps .\n"
            f"Retourne UNIQUEMENT un JSON valide avec ce format exact: {{\"score\": X}} où X est la somme des point. pour chaque questions juste.\n"
            f"Utilise les guillemets doubles pour la clé \"score\"."
        )

        response = client.chat.completions.create(
            extra_body={},
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
        )

        if not response or not response.choices:
            raise ValueError("L'API n'a pas retourné de choix valides.")

        raw_content = response.choices[0].message.content
        if not raw_content:
            raise ValueError("La réponse de l'API est vide.")

        # Nettoyage plus robuste du JSON
        cleaned_content = re.sub(r"^```json\s*|\s*```$", "", raw_content.strip(), flags=re.MULTILINE)

        # Correction des guillemets simples en doubles si nécessaire
        cleaned_content = cleaned_content.replace("'", '"')

        try:
            evaluation = json.loads(cleaned_content)
        except json.JSONDecodeError:
            # Si le parsing échoue, tentative de correction du format
            score_match = re.search(r'score["\']?\s*:\s*(\d+)', cleaned_content)
            if score_match:
                return {"score": int(score_match.group(1))}
            raise

        if "score" not in evaluation:
            raise ValueError("Le JSON retourné ne contient pas la clé 'score'")

        return {"score": evaluation["score"]}

    except Exception as e:
        logging.exception("Erreur lors de l'évaluation de la réponse")
        return {"score": 0}

