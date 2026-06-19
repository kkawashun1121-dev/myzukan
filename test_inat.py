import os
import requests
from dotenv import load_dotenv
load_dotenv()

token = os.environ["INATURALIST_API_TOKEN"]
url = "https://api.inaturalist.org/v1/computervision/score_image"
files = [("image", ("test1.jpeg", open("test1.jpeg", "rb")))]
headers = {"Authorization": token}

response = requests.post(url, files=files, headers=headers)
result = response.json()

top = result["results"][0]
name = top["taxon"].get("preferred_common_name", top["taxon"]["name"])
scientific = top["taxon"]["name"]
score = top["combined_score"]

print(f"一般名: {name}")
print(f"学名: {scientific}")
print(f"信頼度: {score:.1f}")