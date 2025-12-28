import re
from pydantic import BaseModel, Field, field_validator

E164_REGEX = re.compile(r"^\+[0-9]+$")
ISO_UTC_REGEX = re.compile(r".+Z$")


class WebhookMessage(BaseModel):
    message_id: str = Field(..., min_length=1)
    from_msisdn: str = Field(..., alias="from")
    to_msisdn: str = Field(..., alias="to")
    ts: str
    text: str | None = Field(default=None, max_length=4096)

    @field_validator("from_msisdn", "to_msisdn")
    @classmethod
    def validate_e164(cls, v: str) -> str:
        if not E164_REGEX.match(v):
            raise ValueError("invalid E.164 format")
        return v

    @field_validator("ts")
    @classmethod
    def validate_ts(cls, v: str) -> str:
        if not ISO_UTC_REGEX.match(v):
            raise ValueError("timestamp must be UTC with Z suffix")
        return v
