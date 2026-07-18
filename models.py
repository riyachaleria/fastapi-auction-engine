"""
SQLModel database models.
Defines the tables and relationships for Users, Items, and Bids in the PostgreSQL database.
"""
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    """
    Represents a registered user on the BidBazaar platform.
    Can both create auctions (items) and place bids on other auctions.
    """
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    email: str = Field(unique=True)
    hashed_password: str
    bids: list["Bid"] = Relationship(back_populates="bidder")
    items: list["Item"] = Relationship(
        back_populates="owner", 
        sa_relationship_kwargs={"foreign_keys": "Item.owner_id"}
    )
    stripe_account_id: str | None = Field(default=None)
    refresh_tokens: list["RefreshToken"] = Relationship(back_populates="user")

class Item(SQLModel, table=True):
    """
    Represents an auction item listed by a User.
    Tracks the current highest bid and expiration time.
    """
    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = Field(default=None)
    starting_price: float
    current_price: float = Field(default=0.0)
    end_time: datetime
    is_active: bool = Field(default=True)
    higher_bidder_id: int | None = Field(default=None, foreign_key="user.id")
    owner_id: int | None = Field(default=None, foreign_key="user.id")
    owner: User | None = Relationship(
        back_populates="items",
        sa_relationship_kwargs={"foreign_keys": "Item.owner_id"}
    )
    payment_status: str | None = Field(default="pending")
    checkout_token: str | None = Field(default=None)
    stripe_payment_id: str | None = Field(default=None)

class Bid(SQLModel, table=True):
    """
    Represents a single monetary bid placed by a User on an Item.
    """
    id: int | None = Field(default=None, primary_key=True)
    amount: float
    item_id: int | None = Field(default=None, foreign_key="item.id")
    bidder_id: int | None = Field(default=None, foreign_key="user.id")
    bidder: User | None = Relationship(back_populates="bids")

class RefreshToken(SQLModel, table=True):
    """
    Represents a long-lived JWT refresh token stored for session tracking and rotation.
    Allows revoking individual sessions or triggering multi-device logout across all user devices.
    """
    jti: str = Field(primary_key=True)
    user_id: int = Field(default=None,foreign_key="user.id")
    is_revoked: bool = Field(default=False)
    expires_at: datetime
    user: User | None = Relationship(back_populates="refresh_tokens")

class OTP_Table(SQLModel,table=True):
    """
    Represents a short-lived one-time verification code (OTP) for secure password recovery.
    Enforces expiration time windows and single-use validation mechanisms.
    """
    id: int | None = Field(default=None,primary_key=True)
    email: str
    otp_code: str
    is_used: bool = Field(default=False)
    purpose: str = Field(default="password_reset")
    expires_at: datetime