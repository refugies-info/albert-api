# Déployer l'API Albert

## Quickstart

1. Créez un fichier *config.yml* à la racine du dépot sur la base du fichier d'exemple *[config.example.yml](./config.example.yml)* Voir la section [Configuration](#configuration) pour plus d'informations.

2. Déployez l'API avec Docker à l'aide du fichier [compose.yml](../compose.yml) à la racine du dépot.

  ```bash
  docker compose up -d
  ```

## Configuration

### Variables d'environnements

| Variable | Description |
| --- | --- |
| APP_CONTACT_URL | URL pour les informations de contact de l'application (par défaut : None) |
| APP_CONTACT_EMAIL | Email de contact pour l'application (par défaut : None) |
| APP_VERSION | Version de l'application (par défaut : "0.0.0") |
| APP_DESCRIPTION | Description de l'application (par défaut : None) |
| GLOBAL_RATE_LIMIT | Limite de taux global pour les requêtes API par adresse IP (par défaut : "100/minute") |
| DEFAULT_RATE_LIMIT | Limite de taux par défaut pour les requêtes API par utilisateur (par défaut : "10/minute") |
| CONFIG_FILE | Chemin vers le fichier de configuration (par défaut : "config.yml") |
| LOG_LEVEL | Niveau de journalisation (par défaut : DEBUG) |

### Clients tiers

Pour fonctionner, l'API Albert nécessite des clients tiers :

* Auth (optionnel) : [Grist](https://www.getgrist.com/)*
* Cache : [Redis](https://redis.io/)
* Internet : [DuckDuckGo](https://duckduckgo.com/) ou [Brave](https://search.brave.com/)
* Vectors : [Qdrant](https://qdrant.tech/) ou [Elasticsearch](https://www.elastic.co/fr/products/elasticsearch)
* Models** :
  * text-generation: [vLLM](https://github.com/vllm-project/vllm)
  * text-embeddings-inference: [HuggingFace Text Embeddings Inference](https://github.com/huggingface/text-embeddings-inference)
  * automatic-speech-recognition: [Whisper OpenAI API](https://github.com/etalab-ia/whisper-openai-api)
  * text-classification: [HuggingFace Text Embeddings Inference](https://github.com/huggingface/text-embeddings-inference)

Vous devez à minima à disposer d'un modèle language (text-generation) et d'un modèle d'embeddings (text-embeddings-inference).

\* *Pour plus d'information sur l'authentification Grist, voir la [documentation](./security.md).*<br>
\** *Pour plus d'information sur le déploiement des modèles, voir la [documentation](./models.md).*

Ces clients sont déclarés dans un fichier de configuration qui doit respecter les  spécifications suivantes (voir *[config.example.yml](./config.example.yml)* pour un exemple) :

```yaml
auth: [optional]
  type: grist
  args: [optional] 
    [arg_name]: [value]
    ...

internet:
  type: duckduckgo|brave
  args:
    default_language_model: [required]
    default_embeddings_model: [required]
    [arg_name]: [value]
    ...

models:
    - url: text-generation|text-embeddings-inference|automatic-speech-recognition|text-classification
      key: [optional]
      type: [required] # at least one of embedding model (text-embeddings-inference)
    ...

databases:
  cache: [required]
    type: redis
    args: [required] 
      [arg_name]: [value]
      ...
    
 search: [required]
    type: elastic|qdrant
    args: [required] 
      [arg_name]: [value]
      ...
```

Pour avoir un détail des arguments de configuration, vous pouvez consulter le schéma Pydantic de la configuration [ici](../app/schemas/config.py).
