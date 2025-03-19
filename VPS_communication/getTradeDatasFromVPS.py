import paramiko,configparser
from scp import SCPClient

def create_ssh_client(hostname, port, username, password):
    """Crée une connexion SSH à la machine distante."""
    client = paramiko.SSHClient()
    # Charge les clés d'hôte connues
    client.load_system_host_keys()
    # Si l'hôte n'est pas dans les clés connues, ignorez l'alerte
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Connexion à l'hôte distant
    client.connect(hostname, port=port, username=username, password=password)
    return client

def download_file(hostname, port, username, password, remote_file, local_path):
    """Utilise SCP pour récupérer un fichier depuis la machine distante."""
    ssh_client = create_ssh_client(hostname, port, username, password)
    
    with SCPClient(ssh_client.get_transport()) as scp:
        scp.get(remote_file, local_path)
        print(f"Fichier récupéré : {remote_file} -> {local_path}")
    
    ssh_client.close()


config = configparser.ConfigParser()
config.read('config.ini')

# Détails de la connexion SSH
hostname = config['credentials']['server_ip']
port = 22  # Par défaut, SSH utilise le port 22
username = config['credentials']['username']
password = config['credentials']['password']  # Mot de passe SSH du serveur
project_path = 'Backtest_Trading/trade_datas/ES/2023-03-24_12-00_2025-02-10_10-00/'
local_path = f'C:/Users/tessa/Codes/{project_path}'  # Le répertoire local à envoyer
remote_path = f'~/{project_path}'  # Le répertoire distant où envoyer
remote_file = remote_path + "new_trade_data_method3.pkl"


# Téléchargement du fichier
download_file(hostname, port, username, password, remote_file, local_path)