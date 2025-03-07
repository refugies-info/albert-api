from fastapi import APIRouter, Request, Security

from app.schemas.completions import CompletionRequest, Completions
from app.schemas.security import User
from app.utils.exceptions import WrongModelTypeException
from app.utils.lifespan import clients, limiter
from app.utils.route import forward_request
from app.utils.security import check_api_key, check_rate_limit
from app.utils.settings import settings
from app.utils.variables import DEFAULT_TIMEOUT, LANGUAGE_MODEL_TYPE

router = APIRouter()


@router.post(path="/completions")
@limiter.limit(limit_value=settings.rate_limit.by_key, key_func=lambda request: check_rate_limit(request=request))
async def completions(request: Request, body: CompletionRequest, user: User = Security(dependency=check_api_key)) -> Completions:
    """
    Completion API similar to OpenAI's API.
    See https://platform.openai.com/docs/api-reference/completions/create for the API specification.
    """
    client = clients.models[body.model]
    if client.type != LANGUAGE_MODEL_TYPE:
        raise WrongModelTypeException()

    body.model = client.id  # replace alias by model id
    url = f"{client.base_url}completions"
    headers = {"Authorization": f"Bearer {client.api_key}"}

    response = await forward_request(url=url, method="POST", headers=headers, json=body.model_dump(), timeout=DEFAULT_TIMEOUT)
    return Completions(**response.json())
