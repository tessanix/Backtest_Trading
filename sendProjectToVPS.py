import paramiko
import os

# Détails de la connexion SSH
hostname = '178.170.122.201'
port = 22  # Par défaut, SSH utilise le port 22
username = 'root'
password = 'dmYUp7pMOBIVwdMh'  # Mot de passe SSH du serveur
local_directory = 'C:/Users/tessa/Codes/Backtest_Trading'  # Le répertoire local à envoyer
remote_directory = 'Backtest_Trading/'  # Le répertoire distant où envoyer

# Liste des chaînes à ignorer dans le nom des fichiers et répertoires
ignored_strings = ['PM.csv', 'news.csv', '.pkl']  # Fichiers contenant ces mots
ignored_dirs = ['__pycache__', '.git']  # Répertoires à ignorer


# Connexion SSH
def create_ssh_client(hostname, port, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, password=password)
    return client

# Transfert de fichiers via SFTP avec filtrage des fichiers et répertoires à ignorer
def send_directory(client, local_directory, remote_directory):
    sftp = client.open_sftp()
    
    try:
        sftp.mkdir(remote_directory)  # Créer le répertoire distant
    except IOError:
        pass  # Si le répertoire existe déjà, ignorer l'erreur
    
    # Parcours récursif du répertoire local
    for root, dirs, files in os.walk(local_directory):
        # Conversion du chemin Windows en chemin Linux
        root = root.replace("\\", "/")  # Remplacer les backslashes par des slashes
        # Vérifier si le répertoire actuel doit être ignoré
        if any(ignored_dir in root for ignored_dir in ignored_dirs):
            print(f"Répertoire ignoré : {root}")
            continue  # Ignorer ce répertoire
        
        # Construire le chemin distant correspondant
        remote_root = os.path.join(remote_directory, os.path.relpath(root, local_directory)).replace("\\", "/")
        
        try:
            sftp.mkdir(remote_root)  # Créer les sous-dossiers
        except IOError:
            pass
        
        # Transfert des fichiers
        for file in files:
            # Vérifier si le nom du fichier contient l'une des chaînes à ignorer
            if any(ignored_string in file for ignored_string in ignored_strings):
                print(f"Fichier ignoré : {file}")
                continue  # Ignorer ce fichier
            
            local_file = os.path.join(root, file)
            remote_file = os.path.join(remote_root, file).replace("\\", "/")
            sftp.put(local_file, remote_file)
            print(f"Fichier {local_file} envoyé à {remote_file}")
    
    sftp.close()

# Exécution du transfert
def main():
    ssh_client = create_ssh_client(hostname, port, username, password)
    
    try:
        send_directory(ssh_client, local_directory, remote_directory)
        print(f"Répertoire {local_directory} envoyé avec succès vers {remote_directory}.")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
    finally:
        ssh_client.close()

if __name__ == '__main__':
    main()