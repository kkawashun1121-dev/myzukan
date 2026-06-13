import requests

url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 35.68,
    "longitude": 139.69,
    "current": "temperature_2m,relative_humidity_2m,weather_code"
}

response = requests.get(url, params=params)
data = response.json()

def get_weather_description(code:int)-> str:
    table =[
        (0,"快晴"),
        (3,"晴れ～曇り"),
        (48,"霧"),
        (67,"雨"),
        (77,"雪"),
        (99,"雷雨,にわか雨"),
    ]

    return next(desc for limit, desc in table if code<=limit)

print(get_weather_description(data["current"]["weather_code"]))
print(f"気温:{data["current"]["temperature_2m"]}℃ 湿度:{data["current"]["relative_humidity_2m"]}%")