import os
from config import PARTIE_DIR

def load_parties():
    partie = []
    if not os.path.exists(PARTIE_DIR):
        os.makedirs(PARTIE_DIR)
    for filename in os.listdir(PARTIE_DIR):
        if filename.endswith(".txt"):
            with open(os.path.join(PARTIE_DIR, filename), "r") as file:
                partie.append({"title": filename.replace(".txt", ""), "content": file.read()})
    return partie

def save_partie(title, content):
    if not os.path.exists(PARTIE_DIR):
        os.makedirs(PARTIE_DIR)
    with open(os.path.join(PARTIE_DIR, f"{title}.txt"), "w") as file:
        file.write(content)

def delete_partie(title):
    filepath = os.path.join(PARTIE_DIR, f"{title}.txt")
    if os.path.exists(filepath):
        os.remove(filepath)

def update_partie(title, new_content):
    """
    Met à jour le contenu d'une note existante
    :param title: Titre de la partie
    :param new_content: Nouveau contenu
    :return: True si la mise à jour est réussie, False sinon
    """
    filepath = os.path.join(PARTIE_DIR, f"{title}.txt")
    if os.path.exists(filepath):
        with open(filepath, "w") as file:
            file.write(new_content)
        return True
    return False