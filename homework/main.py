from datetime import date, datetime
from typing import List

import databases
import sqlalchemy
from fastapi import FastAPI
from pydantic import BaseModel, Field, EmailStr

DATABASE_URL = "sqlite:///users_database.db"

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String(32)),
    sqlalchemy.Column("second_name", sqlalchemy.String(32)),
    sqlalchemy.Column("birthday", sqlalchemy.Date()),
    sqlalchemy.Column("email", sqlalchemy.String(128)),
    sqlalchemy.Column("address", sqlalchemy.String(128))
)

engine = sqlalchemy.create_engine(
    DATABASE_URL)
metadata.create_all(engine)

app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


class UserIn(BaseModel):
    name: str = Field(min_length=2, max_length=32)
    second_name: str = Field(min_length=2, max_length=32)
    birthday: date
    email: EmailStr
    address: str = Field(min_length=5, max_length=128)


class User(BaseModel):
    id: int
    name: str = Field(min_length=2, max_length=32)
    second_name: str = Field(min_length=2, max_length=32)
    birthday: date
    email: EmailStr
    address: str = Field(min_length=5, max_length=128)


@app.get("/fake_users/{count}")
async def create_note(count: int):
    for i in range(1, count+1):
        query = users.insert().values(name=f'user{i}', second_name=f'Suserov{i}',
                                      birthday=datetime.strptime(f'{1950+i}-{i%12+1}-{i%30+1}', '%Y-%m-%d'),
                                      email=f'user{i}@mail.ru',
                                      address=f"road{i} house{i*2}")
        await database.execute(query)
    return {'mesage': f'{count} fake users create'}


@app.post("/users/", response_model=User)
async def create_user(user: UserIn):
    query = users.insert().values(**user.dict())
    last_record_id = await database.execute(query)
    return {**user.dict(), "id": last_record_id}


@app.get("/users/", response_model=List[User])
async def read_users():
    query = users.select()
    return await database.fetch_all(query)


@app.get("/users/{user_id}", response_model=User)
async def read_user(user_id: int):
    query = users.select().where(users.c.id == user_id)
    return await database.fetch_one(query)


@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, new_user: UserIn):
    query = users.update().where(users.c.id == user_id).values(**new_user.dict())
    await database.execute(query)
    return {**new_user.dict(), "id": user_id}


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    query = users.delete().where(users.c.id == user_id)
    await database.execute(query)
    return {'message': 'User deleted'}
