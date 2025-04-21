from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List


class User(SQLModel, table=True):
    __tablename__ = 'users'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str = Field(max_length=100)
    cpf: str = Field(max_length=14)
    phone: str = Field(max_length=14)
    email: str = Field(max_length=50)
    password: str
    user_role: str = Field(max_length=100, default="Comum")
    created_at: datetime = Field(default_factory=datetime.now)
    status: bool = Field(default=True)
    secret_key: Optional[str] = None
    qrcode: Optional[str] = None
    first_login: bool = Field(default=True)
    refresh_token: Optional[str] = None

    password_recovery: List["PasswordRecovery"] = Relationship(
        back_populates="users",
        sa_relationship=relationship("PasswordRecovery", back_populates="users", cascade="all, delete-orphan")
    )

    restaurants: List["Restaurant"] = Relationship(
        back_populates="users",
        sa_relationship=relationship("restaurants",back_populates="users", cascade="all, delete-orphan")
    )


class PasswordRecovery(SQLModel, table=True):
    __tablename__ = 'password_recovery'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id")
    user: Optional[User] = Relationship(back_populates="password_recovery")
    token: str
    created_at: datetime = Field(default_factory=datetime.now)

class Restaurant(SQLModel, table=True):
    __tablename__ = 'restaurants'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id")
    user: Optional[User] = Relationship(back_populates="restaurants")
    name: str = Field(max_length=200)
    address: str = Field(max_length=300)
    phone: str = Field(max_length=14)
    category: str = Field(max_length=100)
    created_at: datetime = Field(default_factory=datetime.now)

    menus: List["Menu"] = Relationship(
        back_populates="restaurants",
        sa_relationship=relationship("menus",back_populates="restaurants", cascade="all, delete-orphan")
    )

    tables: List["Table"] = Relationship(
        back_populates="restaurants",
        sa_relationship=relationship("tables",back_populates="restaurants", cascade="all, delete-orphan")
    )

    orders: List["Order"] = Relationship(
        back_populates="restaurants",
        sa_relationship=relationship("orders",back_populates="restaurants", cascade="all, delete-orphan")
    )

class Menu(SQLModel, table=True):
    __tablename__ = 'menus'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    restaurant_id: int = Field(foreign_key="restaurants.id")
    restaurant: Optional[Restaurant] = Relationship(back_populates="menus")
    name: str = Field(max_length=100)
    description: str = Field(max_length=300)
    price: int = Field()
    category: str = Field(max_length=100)
    status: bool = Field(default=True)

class Table(SQLModel, table=True):
    __tablename__ = 'tables'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    restaurant_id: int = Field(foreign_key="restaurants.id")
    restaurant: Optional[Restaurant] = Relationship(back_populates="tables")
    number: int = Field()
    capacity: int = Field()
    status: bool = Field(default=True)

    orders: List["Order"] = Relationship(
        back_populates="tables",
        sa_relationship=relationship("orders",back_populates="tables", cascade="all, delete-orphan")
    )

class Order(SQLModel, table=True):
    __tablename__ = 'orders'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    restaurant_id: int = Field(foreign_key="restaurants.id")
    restaurant: Optional[Restaurant] = Relationship(back_populates="orders")
    table_id: int = Field(foreign_key="tables.id")
    table: Optional[Table] = Relationship(back_populates="orders")
    name: str = Field(max_length=100)
    description: str = Field(max_length=300)
    price: int = Field()
    category: str = Field(max_length=100)
    status: bool = Field(default=True)






