from functools import partial
import time
from typing import Dict, List

from fastapi import HTTPException
from openai import OpenAI
from qdrant_client import QdrantClient
from redis import Redis
import requests

from app.schemas.config import Config
from app.schemas.models import Model, Models
from app.utils.config import CONFIG, LOGGER
from app.utils.variables import EMBEDDINGS_MODEL_TYPE, LANGUAGE_MODEL_TYPE, METADATA_COLLECTION_ID

from ._gristkeymanager import GristKeyManager


class ModelDict(dict):
    """
    Overwrite __getitem__ method to raise a 404 error if model is not found.
    """

    def __getitem__(self, key: str):
        try:
            return super().__getitem__(key)
        except KeyError:
            raise HTTPException(status_code=404, detail="Model not found.")


# @TODO: add cache
def get_models_list(self, *args, **kwargs):
    """
    Custom method to overwrite OpenAI's list method (client.models.list()). This method support
    embeddings API models deployed with HuggingFace Text Embeddings Inference (see: https://github.com/huggingface/text-embeddings-inference).
    """
    headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else None
    data = list()

    if self.type == LANGUAGE_MODEL_TYPE:
        endpoint = f"{self.base_url}models"
        response = requests.get(url=endpoint, headers=headers, timeout=10).json()
        assert len(response["data"]) == 1, "Only one model per model API is supported."
        response = response["data"][0]
        data.append(
            Model(
                id=response["id"],
                object="model",
                owned_by=response.get("owned_by", ""),
                created=response.get("created", round(time.time())),
                max_model_len=response.get("max_model_len", None),
                type=LANGUAGE_MODEL_TYPE,
            )
        )

    elif self.type == EMBEDDINGS_MODEL_TYPE:
        endpoint = str(self.base_url).replace("/v1/", "/info")
        response = requests.get(url=endpoint, headers=headers, timeout=10).json()
        data.append(
            Model(
                id=response["model_id"],
                object="model",
                owned_by="huggingface-text-embeddings-inference",
                max_model_len=response.get("max_input_length", None),
                created=round(time.time()),
                type=EMBEDDINGS_MODEL_TYPE,
            )
        )
    else:
        raise HTTPException(status_code=400, detail="Model type not supported.")

    return Models(data=data)


def check_context_length(self, model: str, messages: List[Dict[str, str]], add_special_tokens: bool = True):
    headers = {"Authorization": f"Bearer {self.api_key}"}
    prompt = "\n".join([message["role"] + ": " + message["content"] for message in messages])
    data = {"model": model, "prompt": prompt, "add_special_tokens": add_special_tokens}

    response = requests.post(str(self.base_url).replace("/v1/", "/tokenize"), json=data, headers=headers)
    response.raise_for_status()
    return response.json()["count"] <= response.json()["max_model_len"]


class ClientsManager:
    def __init__(self, config: Config):
        self.config = config
        self.models = self.set_models()
        self.cache = self.set_cache()
        self.vectors = self.set_vectors()
        self.auth = self.set_auth()

    def set_models(self):
        models = ModelDict()
        previous_model_ids = list()
        for model in self.config.models:
            client = OpenAI(base_url=model.url, api_key=model.key, timeout=10)
            client.type = model.type
            client.models.list = partial(get_models_list, client)
            client.search_internet = model.search_internet

            try:
                response = client.models.list()
                model = response.data[0]
                if model.id in previous_model_ids:
                    raise ValueError(f"Model id {model.id} is duplicated, not allowed.")
                previous_model_ids.append(model.id)
            except Exception as e:
                LOGGER.info(f"error to request the model API on {model.url}, skipping:\n{e}")
                continue

            # get vector size
            if client.type == EMBEDDINGS_MODEL_TYPE:
                response = client.embeddings.create(model=model.id, input="hello world")
                client.vector_size = len(response.data[0].embedding)
                if client.search_internet:
                    self.SEARCH_INTERNET_EMBEDDINGS_MODEL_ID = model.id

            if client.type == LANGUAGE_MODEL_TYPE:
                client.check_context_length = partial(check_context_length, client)
                if client.search_internet:
                    self.SEARCH_INTERNET_LANGUAGE_MODEL_ID = model.id

            models[model.id] = client

            if len(models.keys()) == 0:
                raise ValueError("No model can be reached.")

        self.models = models

    def set_cache(self):
        cache = Redis(**self.config.databases.cache.args)

        self.cache = cache

    def set_vectors(self):
        vectors = QdrantClient(**self.config.databases.vectors.args)
        vectors.url = CONFIG.databases.vectors.args["url"]
        vectors.api_key = CONFIG.databases.vectors.args["api_key"]

        if not vectors.collection_exists(collection_name=METADATA_COLLECTION_ID):
            vectors.create_collection(collection_name=METADATA_COLLECTION_ID, vectors_config={}, on_disk_payload=False)

        self.vectors = vectors

    def set_auth(self):
        if self.config.auth:
            auth = GristKeyManager(redis=self.cache, **self.config.auth.args)
        else:
            auth = None

        self.auth = auth