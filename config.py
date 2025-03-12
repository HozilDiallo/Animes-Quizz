import os

# Dossier ou les notes seront sauvegardées
PARTIE_DIR = "./Partie/"
if not os.path.exists(PARTIE_DIR):
    os.makedirs(PARTIE_DIR)

# Dossier ou les questions seront sauvegardées
QUESTIONS_DIR = "./Questions/"
if not os.path.exists(QUESTIONS_DIR):
    os.makedirs(QUESTIONS_DIR)

# Chemin du fichier contenant les questions
QUESTIONS_FILE = os.path.join(QUESTIONS_DIR, "questions.json")

# Ajouter cette ligne avec les autres constantes
STATS_DIR = "./Stats/"
if not os.path.exists(STATS_DIR):
    os.makedirs(STATS_DIR)
