from sqlalchemy import Column, Integer, String, Boolean,ForeignKey
from database import Base

class Creature(Base):
    __tablename__="zukan"

    id=Column(Integer, primary_key=True,index=True)
    owner_id=Column(Integer,ForeignKey("users.id"))
    name=Column(String,nullable=False)
    image_url=Column(String,nullable=True)
    care_guide=Column(String,nullable=True)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer,primary_key=True,index=True)
    username=Column(String,unique=True,nullable=False)
    hashed_password=Column(String,nullable=False)

class Cage(Base):
    __tablename__="cages"

    id=Column(Integer,primary_key=True,index=True)
    owner_id=Column(Integer,ForeignKey("users.id"))
    name=Column(String,nullable=False)
    
