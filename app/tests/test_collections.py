import logging
import uuid

import pytest

from app.schemas.collections import Collection, Collections
from app.utils.security import encode_string
from app.utils.variables import (
    EMBEDDINGS_MODEL_TYPE,
    INTERNET_COLLECTION_ID,
    LANGUAGE_MODEL_TYPE,
    METADATA_COLLECTION_ID,
    PRIVATE_COLLECTION_TYPE,
    PUBLIC_COLLECTION_TYPE,
)


@pytest.fixture(scope="module")
def setup(args, session_user):
    USER = encode_string(input=args["api_key_user"])
    ADMIN = encode_string(input=args["api_key_admin"])
    logging.info(f"test user ID: {USER}")
    logging.info(f"test admin ID: {ADMIN}")

    response = session_user.get(f"{args["base_url"]}/models", timeout=10)
    models = response.json()
    EMBEDDINGS_MODEL_ID = [model for model in models["data"] if model["type"] == EMBEDDINGS_MODEL_TYPE][0]["id"]
    LANGUAGE_MODEL_ID = [model for model in models["data"] if model["type"] == LANGUAGE_MODEL_TYPE][0]["id"]
    logging.info(f"test embedings model ID: {EMBEDDINGS_MODEL_ID}")
    logging.info(f"test language model ID: {LANGUAGE_MODEL_ID}")

    PUBLIC_COLLECTION_NAME = "pytest-public"
    PRIVATE_COLLECTION_NAME = "pytest-private"

    yield PUBLIC_COLLECTION_NAME, PRIVATE_COLLECTION_NAME, ADMIN, USER, EMBEDDINGS_MODEL_ID, LANGUAGE_MODEL_ID


@pytest.mark.usefixtures("args", "session_user", "session_admin", "setup", "cleanup_collections")
class TestFiles:
    def test_create_private_collection_with_user(self, args, session_user, setup):
        _, PRIVATE_COLLECTION_NAME, _, _, EMBEDDINGS_MODEL_ID, _ = setup

        params = {"name": PRIVATE_COLLECTION_NAME, "model": EMBEDDINGS_MODEL_ID, "type": PRIVATE_COLLECTION_TYPE}
        response = session_user.post(f"{args["base_url"]}/collections", json=params)
        assert response.status_code == 201
        assert "id" in response.json().keys()

    def test_create_public_collection_with_user(self, args, session_user, setup):
        PUBLIC_COLLECTION_NAME, _, _, _, EMBEDDINGS_MODEL_ID, _ = setup

        params = {"name": PUBLIC_COLLECTION_NAME, "model": EMBEDDINGS_MODEL_ID, "type": PUBLIC_COLLECTION_TYPE}
        response = session_user.post(f"{args["base_url"]}/collections", json=params)
        assert response.status_code == 400

    def test_create_public_collection_with_admin(self, args, session_admin, setup):
        PUBLIC_COLLECTION_NAME, _, _, _, EMBEDDINGS_MODEL_ID, _ = setup

        params = {"name": PUBLIC_COLLECTION_NAME, "model": EMBEDDINGS_MODEL_ID, "type": PUBLIC_COLLECTION_TYPE}
        response = session_admin.post(f"{args["base_url"]}/collections", json=params)
        assert response.status_code == 201
        assert "id" in response.json().keys()

    def test_create_private_collection_with_language_model_with_user(self, args, session_user, setup):
        _, PRIVATE_COLLECTION_NAME, _, _, _, LANGUAGE_MODEL_ID = setup

        params = {"name": PRIVATE_COLLECTION_NAME, "model": LANGUAGE_MODEL_ID, "type": PRIVATE_COLLECTION_TYPE}
        response = session_user.post(f"{args["base_url"]}/collections", json=params)
        assert response.status_code == 400

    def test_create_private_collection_with_unknown_model_with_user(self, args, session_user, setup):
        _, PRIVATE_COLLECTION_NAME, _, _, _, _ = setup

        params = {"name": PRIVATE_COLLECTION_NAME, "model": "unknown-model", "type": PRIVATE_COLLECTION_TYPE}
        response = session_user.post(f"{args["base_url"]}/collections", json=params)
        assert response.status_code == 404

    def test_get_collections(self, args, session_user, setup):
        PUBLIC_COLLECTION_NAME, PRIVATE_COLLECTION_NAME, ADMIN, USER, _, _ = setup

        response = session_user.get(f"{args["base_url"]}/collections")
        assert response.status_code == 200

        collections = response.json()
        collections["data"] = [Collection(**collection) for collection in collections["data"]]
        collections = Collections(**collections)

        assert isinstance(collections, Collections)
        assert all(isinstance(collection, Collection) for collection in collections.data)

        assert METADATA_COLLECTION_ID not in [collection.id for collection in collections.data]
        assert INTERNET_COLLECTION_ID in [collection.id for collection in collections.data]

        assert PRIVATE_COLLECTION_NAME in [collection.name for collection in collections.data]
        assert PUBLIC_COLLECTION_NAME in [collection.name for collection in collections.data]

        assert [collection.user for collection in collections.data if collection.name == PRIVATE_COLLECTION_NAME][0] == USER
        assert [collection.user for collection in collections.data if collection.name == PUBLIC_COLLECTION_NAME][0] == ADMIN
        assert len(collections.data) == 3

        collection_id = [collection.id for collection in collections.data if collection.name == PRIVATE_COLLECTION_NAME][0]
        response = session_user.get(f"{args["base_url"]}/collections/{collection_id}")
        assert response.status_code == 200
        collection = Collection(**response.json())
        assert isinstance(collection, Collection)
        assert collection_id == collection.id

    def test_get_collection_of_other_user(self, args, session_admin, setup):
        _, PRIVATE_COLLECTION_NAME, _, _, _, _ = setup

        response = session_admin.get(f"{args["base_url"]}/collections")
        collections = response.json()
        collections = [collection["name"] for collection in collections["data"]]

        assert PRIVATE_COLLECTION_NAME not in collections

    def test_get_internet_collection(self, args, session_user, setup):
        _, _, _, _, _, _ = setup

        response = session_user.get(f"{args["base_url"]}/collections/{INTERNET_COLLECTION_ID}")
        assert response.status_code == 200
        assert INTERNET_COLLECTION_ID == response.json()["id"]

    def test_get_collection_with_unknown_id(self, args, session_user, setup):
        _, _, _, _, _, _ = setup

        response = session_user.get(f"{args["base_url"]}/collections/{str(uuid.uuid4())}")
        assert response.status_code == 400

    def test_delete_private_collection_with_user(self, args, session_user, setup):
        _, PRIVATE_COLLECTION_NAME, _, _, _, _ = setup

        response = session_user.get(f"{args["base_url"]}/collections")
        collection_id = [collection["id"] for collection in response.json()["data"] if collection["name"] == PRIVATE_COLLECTION_NAME][0]
        response = session_user.delete(f"{args["base_url"]}/collections/{collection_id}")
        assert response.status_code == 204

    def test_delete_public_collection_with_user(self, args, session_user, setup):
        PUBLIC_COLLECTION_NAME, _, _, _, _, _ = setup

        response = session_user.get(f"{args["base_url"]}/collections")
        collection_id = [collection["id"] for collection in response.json()["data"] if collection["name"] == PUBLIC_COLLECTION_NAME][0]
        response = session_user.delete(f"{args["base_url"]}/collections/{collection_id}")
        assert response.status_code == 400

    def test_delete_public_collection_with_admin(self, args, session_admin, setup):
        PUBLIC_COLLECTION_NAME, _, _, _, _, _ = setup

        response = session_admin.get(f"{args["base_url"]}/collections")
        collection_id = [collection["id"] for collection in response.json()["data"] if collection["name"] == PUBLIC_COLLECTION_NAME][0]
        response = session_admin.delete(f"{args["base_url"]}/collections/{collection_id}")
        assert response.status_code == 204

    def test_create_internet_collection_with_user(self, args, session_user, setup):
        _, _, _, _, EMBEDDINGS_MODEL_ID, _ = setup

        params = {"name": INTERNET_COLLECTION_ID, "model": EMBEDDINGS_MODEL_ID, "type": PUBLIC_COLLECTION_TYPE}
        response = session_user.post(f"{args["base_url"]}/collections", json=params)
        assert response.status_code == 400

    def test_create_collection_with_empty_name(self, args, session_user, setup):
        _, _, _, _, EMBEDDINGS_MODEL_ID, _ = setup

        params = {"name": " ", "model": EMBEDDINGS_MODEL_ID, "type": PRIVATE_COLLECTION_TYPE}
        response = session_user.post(f"{args["base_url"]}/collections", json=params)
        assert response.status_code == 422