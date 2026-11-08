# Configuration

Tous les paramètres sont facultatifs. Docker Compose les lit depuis `.env`. En développement, exportez-les avant d'exécuter `scripts/dev.sh`.

## Variables d'environnement

### Service

| Variable | Valeur par défaut | Signification |
| --- | --- | --- |
| `ACT_GUI_PORT` | `8080` | Port hôte du conteneur, lié uniquement à `127.0.0.1`. |
| `ACT_GUI_IMAGE` | `act-gui:0.1.0` | Nom et tag de l'image à construire ou à exécuter. |
| `ACT_GUI_DEVICE` | `cpu` | Appareil Torch utilisé pour les exécutions. `compose.gpu.yaml` définit `cuda`. Le résultat enregistre l'appareil réellement utilisé par ACT. |
| `ACT_GUI_RECORDS` | `var/records` (`/data/records` dans Docker) | Répertoire racine des enregistrements. |
| `ACT_GUI_MODELS` | À côté de la racine des enregistrements | Stockage adressé par contenu des modèles construits. |
| `ACT_GUI_ENGINES` | À côté de la racine des enregistrements | Checkouts des branches ACT importées et sélection du moteur actif. |
| `ACT_GUI_SECRETS` | `/data/secrets` dans Docker | Stockage côté serveur des licences importées. |

### Moteur ACT

| Variable | Valeur par défaut | Signification |
| --- | --- | --- |
| `ACT_ROOT` | `/data1/guanqin/ACT` (`/opt/act` dans Docker) | Checkout ACT de référence. Les réseaux du catalogue, `data/` et `literature/` sont lus ici. |
| `ACT_GUI_ACT_REMOTES` | SVF-tools et guanqin-123 sur GitHub | Dépôts ACT préconfigurés pour changer de branche, au format `name=url,...`. |
| `ACT_GUI_ALLOW_CUSTOM_REMOTES` | `1` | Définissez `0` pour empêcher la saisie d'autres URL de dépôts. |

### Construction

| Variable | Valeur par défaut | Signification |
| --- | --- | --- |
| `ACT_SOURCE` | Le checkout ACT local | Emplacement depuis lequel `scripts/docker_build.sh` récupère le commit épinglé, sous forme de chemin ou d'URL git. |
| `ACT_NETS_FROM` | `$ACT_ROOT` | Source depuis laquelle la construction copie les réseaux du catalogue, chacun devant correspondre à son sha256 épinglé. |
| `ACT_DATA_FROM` | `$ACT_ROOT` | Source hôte de `data/` et `literature/` pour `compose.actdata.yaml`. |
| `GUROBIPY_VERSION` | `13.0.0` | Version de gurobipy installée dans l'image, à faire correspondre à la version majeure de la licence. |
| `GUROBI_LICENSE_FILE` | Vide | Chemin hôte de `gurobi.lic`, utilisé avec `compose.gurobi.yaml`. |

---

## Changer de moteur ACT

L'onglet **Engine** choisit le code ACT importé par l'atelier : la base épinglée ou la tête d'une branche de n'importe quel fork d'ACT. Choisissez un dépôt préconfiguré ou saisissez une URL `https`.

- Un changement redémarre le service, car ACT ne peut pas être réimporté dans un processus en cours.
- L'atelier vérifie chaque fonction par rapport aux API fournies par le moteur sélectionné. Les fonctions non prises en charge sont désactivées et leur raison est affichée.
- Un modèle construit que le nouveau moteur ne peut pas charger est marqué **needs rebuild** et peut être reconstruit à partir de ses paramètres enregistrés.
- La saisie d'une URL exécute le code de ce dépôt sur le serveur. Un déploiement public nécessite un contrôle d'accès, ou `ACT_GUI_ALLOW_CUSTOM_REMOTES=0`.

---

## Gurobi {#gurobi}

gurobipy est installé dans l'image, mais une licence n'y est jamais incluse.

- **Importer.** Importez `gurobi.lic` dans l'onglet **Engine**. Il est stocké côté serveur avec des permissions réservées au propriétaire et transmis à chaque worker d'exécution. L'API ne renvoie jamais son contenu.
- **Monter.** Définissez `GUROBI_LICENSE_FILE` et ajoutez `-f compose.gurobi.yaml`. Une licence importée est prioritaire sur une licence montée.
- L'onglet Engine affiche le contrôle de licence propre à Gurobi. Les licences WLS et de serveur de jetons fonctionnent dans les conteneurs. Les licences liées à l'hôte, telles que les licences utilisateur nommé ou académiques, échouent généralement.
- Les méthodes intervalle et BaB actuelles n'appellent pas Gurobi. Une licence ne change donc aucun verdict actuel.
