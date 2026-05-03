import requests
import json
import csv
import time
import os

# ユーザー指定のエリア設定
AREA_SETTINGS = [
    {"area_code": "130000", "office_code": "130000", "area_name": "首都圏", "prefecture": "東京", "location": "東京"},
    {"area_code": "2710000", "office_code": "270000", "area_name": "近畿", "prefecture": "大阪", "location": "大阪"},
    {"area_code": "400000", "office_code": "400000", "area_name": "九州", "prefecture": "福岡", "location": "福岡"},
    {"area_code": "370000", "office_code": "370000", "area_name": "四国", "prefecture": "香川", "location": "高松"},
    {"area_code": "340000", "office_code": "340000", "area_name": "中国", "prefecture": "広島", "location": "広島"},
    {"area_code": "2310000", "office_code": "230000", "area_name": "東海", "prefecture": "愛知", "location": "名古屋"},
    {"area_code": "0410001", "office_code": "040000", "area_name": "東北", "prefecture": "宮城", "location": "仙台"},
    {"area_code": "0110000", "office_code": "016000", "area_name": "北海道", "prefecture": "石狩", "location": "札幌"},
    {"area_code": "0920100", "office_code": "090000", "area_name": "北関東", "prefecture": "栃木", "location": "宇都宮"},
    {"area_code": "1720100", "office_code": "170000", "area_name": "北陸", "prefecture": "石川", "location": "金沢"},
]

def get_weekly_forecast_json(office_code):
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{office_code}.json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    res = requests.get(url, headers=headers, timeout=10)
    res.raise_for_status()
    return res.json()[1]

def process_all_areas():
    all_forecasts = []
    
    for setting in AREA_SETTINGS:
        print(f"Fetching: {setting['location']} ({setting['area_code']})...")
        try:
            weekly_data = get_weekly_forecast_json(setting["office_code"])
            
            ts0 = weekly_data["timeSeries"][0]
            dates = ts0["timeDefines"]
            target_area_code = setting["area_code"][:5]
            
            area0 = next((a for a in ts0["areas"] if target_area_code in a["area"]["code"]), ts0["areas"][0])
            weather_codes = area0.get("weatherCodes", [])
            pops = area0.get("pops", [])
            reliabilities = area0.get("reliabilities", [])
            
            ts1 = weekly_data["timeSeries"][1]
            area1 = next((a for a in ts1["areas"] if target_area_code in a["area"]["code"]), ts1["areas"][0])
            temps_min = area1.get("tempsMin", [])
            temps_max = area1.get("tempsMax", [])
            
            for i in range(len(dates)):
                forecast = {
                    "date": dates[i].split("T")[0],
                    "area_group": setting["area_name"],
                    "prefecture": setting["prefecture"],
                    "location": setting["location"],
                    "weather_code": weather_codes[i] if i < len(weather_codes) else "",
                    "pop": pops[i] if i < len(pops) else "",
                    "temp_min": temps_min[i] if i < len(temps_min) else "",
                    "temp_max": temps_max[i] if i < len(temps_max) else "",
                    "reliability": reliabilities[i] if i < len(reliabilities) else "",
                }
                all_forecasts.append(forecast)
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error fetching {setting['location']}: {e}")
            
    return all_forecasts

def save_data(forecasts):
    # data/ ディレクトリの確認
    os.makedirs("data", exist_ok=True)
    
    # JSON 保存
    json_path = os.path.join("data", "all_forecasts.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(forecasts, f, ensure_ascii=False, indent=4)
    
    # CSV 保存
    csv_path = os.path.join("data", "all_forecasts.csv")
    if forecasts:
        headers = ["date", "area_group", "prefecture", "location", "weather_code", "pop", "temp_min", "temp_max", "reliability"]
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(forecasts)
        print(f"\nSuccessfully saved {len(forecasts)} rows to {json_path} and {csv_path}")
    else:
        print(f"\nNo forecasts to save. JSON saved to {json_path}")

if __name__ == "__main__":
    results = process_all_areas()
    save_data(results)
