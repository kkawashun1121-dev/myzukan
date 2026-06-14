import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key=os.environ["PLANTNET_API_KEY"]

url=f"https://my-api.plantnet.org/v2/identify/all?api-key={api_key}"

files=[
    ("images",("tanpopo.jpg", open("tanpopo.jpg","rb")))
]
data={"organs":["flower"]}


response=requests.post(
    url,
    files=files,
    data=data,
    params={"lang":"ja"}    
)

result=response.json()

best_match=result["bestMatch"]
common_names=result["results"][0]["species"]["commonNames"]
common_name = next(
    (name for name in common_names if any(
        '\u3040' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff' for c in name
    )),
    common_names[0]  # 見つからなければ最初の名前
)

print(f"一般名: {common_name}")
score=result["results"][0]["score"]
print(f"学名:{best_match}")
print(f"一般名:{common_name}")
print(f"信頼度:{score}")

