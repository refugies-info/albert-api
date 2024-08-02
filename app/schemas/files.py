from typing import Literal, List
from uuid import UUID

from pydantic import BaseModel


class File(BaseModel):
    object: Literal["file"] = "file"
    id: UUID
    bytes: int
    filename: str
    created_at: int


class FileResponse(BaseModel):
    object: Literal["list"] = "list"
    data: List[File]


class Upload(BaseModel):
    object: Literal["upload"] = "upload"
    id: UUID
    filename: str
    status: Literal["success", "failed"] = "success"


class UploadResponse(BaseModel):
    object: Literal["list"] = "list"
    data: List[Upload]
