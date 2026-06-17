from fastapi import FastAPI, HTTPException, Depends , Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Creature, User,Cage,Base

from fastapi.security import OAuth2PasswordRequestForm
from auth import hash_password, verify_password, create_access_token,get_current_user

from groq import Groq
import os
from dotenv import load_dotenv

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

load_dotenv()

app = FastAPI()
app.mount("/static",StaticFiles(directory="static"),name="static")
templates=Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CreatureCreate(BaseModel):
    name:str
    image_url:str|None=None
    care_guide:str|None=None

class UserCreate(BaseModel):
    username: str
    password: str

class CageCreate(BaseModel):
    name:str

@app.post('/register')
def register(user:UserCreate,db:Session= Depends(get_db)):
    existing=db.query(User).filter(User.username==user.username).first()
    if existing:
        raise HTTPException(status_code=400,detail="このユーザー名は既に使われています")
    
    new_user=User(
        username=user.username,
        hashed_password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message":"登録完了","username":new_user.username}

@app.post("/login")
def login(form_data:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
    db_user=db.query(User).filter(User.username==form_data.username).first()
    if not db_user or not verify_password(form_data.password,db_user.hashed_password):
        raise HTTPException(status_code=401,detail="ユーザー名またはパスワードが間違っています")
    
    token=create_access_token({"sub":db_user.username})
    return {"access_token":token,"token_type":"bearer"}



def get_current_db_user(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_user = db.query(User).filter(User.username==current_user).first()
    return db_user


@app.post('/creatures')
def create_creature(zukan:CreatureCreate,
                    db:Session = Depends(get_db),
                    db_user=Depends(get_current_db_user)
                    ):
    new_creature=Creature(
        name=zukan.name,
        image_url=zukan.image_url,
        care_guide=zukan.care_guide,
        owner_id = db_user.id)
    
    db.add(new_creature)
    db.commit()
    db.refresh(new_creature)
    return new_creature

@app.get("/creatures")
def get_creatures(db: Session = Depends(get_db), db_user=Depends(get_current_db_user)):
    return db.query(Creature).filter(Creature.owner_id == db_user.id).all()

@app.put("/creatures/{creature_id}")
def update_creature(creature_id:int,
                    zukan:CreatureCreate,
                    db:Session=Depends(get_db),
                    db_user=Depends(get_current_db_user)
                    ):
    creature=db.query(Creature).filter(Creature.id==creature_id,Creature.owner_id==db_user.id).first()
    if not creature:
        raise HTTPException(status_code=404,detail=f"生物{creature_id}が見つかりません")
    creature.name=zukan.name
    creature.image_url=zukan.image_url
    creature.care_guide=zukan.care_guide
    db.commit()
    db.refresh(creature)
    return creature

@app.delete("/creatures/{creature_id}")
def delete_creature(creature_id:int,db:Session=Depends(get_db),db_user=Depends(get_current_db_user)):
    creature=db.query(Creature).filter(Creature.id==creature_id,Creature.owner_id==db_user.id).first()
    if not creature:
        raise HTTPException(status_code=404,detail=f"生物{creature_id}が見つかりません")
    db.delete(creature)
    db.commit()
    return f'{creature_id}が削除されました。'



@app.post("/cages")
def post_cage(cage:CageCreate,
                    db:Session = Depends(get_db),
                    db_user=Depends(get_current_db_user)
                    ):
    new_cage=Cage(name=cage.name,owner_id=db_user.id)
    
    db.add(new_cage)
    db.commit()
    db.refresh(new_cage)
    return new_cage

@app.get("/cages")
def get_cages(db:Session=Depends(get_db),db_user=Depends(get_current_db_user)):
    return db.query(Cage).filter(Cage.owner_id==db_user.id).all()

@app.get("/creatures")
def get_creatures(db: Session = Depends(get_db), db_user=Depends(get_current_db_user)):
    return db.query(Creature).filter(Creature.owner_id == db_user.id).all()


@app.put("/cages/{cage_id}")
def update_creature(cage_id:int,
                    cage:CageCreate,
                    db:Session=Depends(get_db),
                    db_user=Depends(get_current_db_user)
                    ):
    cage_name=db.query(Cage).filter(Cage.id==cage_id,Cage.owner_id==db_user.id).first()
    if not cage_name:
        raise HTTPException(status_code=404,detail=f"カゴ{cage_id}が見つかりません")
    cage_name.name=cage.name

    db.commit()
    db.refresh(cage_name)
    return cage_name

@app.delete("/cages/{cage_id}")
def delete_cage(cage_id:int,db:Session=Depends(get_db),db_user=Depends(get_current_db_user)):
    cage_name=db.query(Cage).filter(Cage.id==cage_id,Cage.owner_id==db_user.id).first()
    if not cage_name:
        raise HTTPException(status_code=404,detail=f"カゴ{cage_id}が見つかりません")
    db.delete(cage_name)
    db.commit()
    return f'{cage_id}が削除されました。'

@app.post("/creatures/{creature_id}/care-guide")
def post_care_guide(creature_id:int,db:Session=Depends(get_db),db_user=Depends(get_current_db_user)):
    
    creature=db.query(Creature).filter(Creature.id==creature_id,Creature.owner_id==db_user.id).first()
    if not creature:
        raise HTTPException(status_code=404, detail="見つかりません")
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {"role": "user", "content": f"""あなたは生物の飼育専門家です。
「{creature.name}」の飼育方法を以下の形式で教えてください。

- 必要な環境（温度・湿度・住む場所）
- 食べ物
- 注意点

各項目1〜2文で、合計100字以内でまとめてください。"""}]
    )
    creature_care_guide = response.choices[0].message.content

    creature.care_guide = creature_care_guide
    db.commit()
    db.refresh(creature)
    return creature


@app.put("/creatures/{creature_id}/cage/{cage_id}")
def put_creature_in_cage(creature_id:int,cage_id:int,db:Session=Depends(get_db),db_user=Depends(get_current_db_user)):
    creature=db.query(Creature).filter(Creature.id==creature_id,Creature.owner_id==db_user.id).first()
    if not creature:
        raise HTTPException(status_code=404,detail="生物が見つかりません")
    cage=db.query(Cage).filter(Cage.id==cage_id,Cage.owner_id==db_user.id).first()
    if not cage:
        raise HTTPException(status_code=404,detail="カゴが見つかりません")
    creature.cage_id=cage_id
    db.commit()
    db.refresh(creature)
    return creature

@app.get("/cages/{cage_id}/creatures")
def get_creatures_in_cage(cage_id: int ,db:Session=Depends(get_db),db_user=Depends(get_current_db_user)):
    cage=db.query(Cage).filter(Cage.id==cage_id,Cage.owner_id==db_user.id).first()
    if not cage:
        raise HTTPException(status_code=404,detail="カゴが見つかりません")
    return db.query(Creature).filter(Creature.cage_id==cage_id).all()