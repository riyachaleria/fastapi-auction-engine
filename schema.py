"""
Pydantic schemas for data validation.
Ensures incoming request payloads are strictly typed and sanitized before processing.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class Usercreate(BaseModel):
    """
    Schema for validating user registration payload.
    Ensures passwords meet security requirements.
    """
    username: str = Field(json_schema_extra={"strip_whitespace": True})
    email: EmailStr
    password: str = Field(json_schema_extra={"strip_whitespace": True})

    @field_validator("password")
    @classmethod
    def valid_password(cls, value: str) -> str:
        if not re.match(r"^(?=.*[0-9])(?=.*[!@#$%^&*]).{8,}$", value):
            raise ValueError("Password must have at least 8 characters, one number, and one special character.")
        
        return value
    
class ItemData(BaseModel):
    """
    Schema for validating a new auction item creation payload.
    Duration is automatically converted to an expiration datetime in the service layer.
    """
    title: str = Field(json_schema_extra={"strip_whitespace": True})
    description: str = Field(json_schema_extra={"strip_whitespace": True})
    starting_price: float
    duration_minutes: int = Field(gt=0, description="Duration of the auction in minutes")