from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

FieldName = Literal['learning_goal', 'experience', 'age', 'education', 'objective']


class Profile(BaseModel):
    model_config = ConfigDict(extra='forbid')
    learning_goal: str | None = Field(default=None, max_length=500)
    experience: str | None = Field(default=None, max_length=1000)
    age: int | None = Field(default=None, ge=1, le=120)
    education: str | None = Field(default=None, max_length=500)
    objective: str | None = Field(default=None, max_length=500)


class Change(BaseModel):
    model_config = ConfigDict(extra='forbid')
    field: FieldName
    value: str | None = Field(max_length=1000)
    evidence: str = Field(min_length=1, max_length=2000)


class Extraction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    changes: list[Change] = Field(max_length=5)
    intent: Literal['conversation', 'explore', 'program_catalog', 'jobs', 'profile_help'] = 'conversation'
    modality: Literal['', 'virtual', 'presencial'] = ''
    level: Literal['', 'pregrado', 'posgrado'] = ''


class ConversationRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: UUID | None = None


class Reply(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str = Field(min_length=1, max_length=3000)


class ConversationResponse(BaseModel):
    conversation_id: UUID
    text: str
    profile: Profile
    skipped_fields: list[FieldName]
    academic: dict | None
    jobs: list[dict]
    jobs_status: Literal['NOT_LOADED', 'NO_MATCHES', 'AVAILABLE', 'UNAVAILABLE', 'NOT_QUERIED']
    notices: list[str]
