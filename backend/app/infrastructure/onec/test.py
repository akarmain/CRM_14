import requests
import json

#base_url = "http://localhost/test/hs/http_methods/"
base_url =  "https://yeqhfy-109-72-246-145.ru.tuna.am/test/hs/http_methods/"
new_lead = [
  { "lead_id": "101", "source": "advertising", "stage": "new", "owner_fio": "Иванов И.И.", "created_at": "2026-02-26", "title": "К.А. ТимЛидович" , "notes": "test note 1"},
  { "lead_id": "102", "source": "advertising", "stage": "qualified", "owner_fio": "Иванов И.И.", "created_at": "2026-03-26", "title": "К.А. ТимЛидович" , "notes": "test note 2"},
  { "lead_id": "103", "source": "advertising", "stage": "proposal", "owner_fio": "Иванов И.И.", "created_at": "2026-04-26", "title": "К.А. ТимЛидович" , "notes": "test note 3"},
  { "lead_id": "101", "source": "advertising", "stage": "won", "owner_fio": "Иванов И.И.", "created_at": "2026-05-26", "title": "К.А. ТимЛидович" , "notes": "test note 4" }
]


while True:
    try:
        r = int(input("1 - get all 2 - post 3 - get one "))
        if r == 1:
            try:
                url = f"{base_url}/leads"
                response = requests.get(url)
                print(f"Статус: {response.status_code}")
                if response.status_code == 200:
                    print(response.text)
                else:
                    print("Ошибка:", response.reason)
            except Exception as e:
                print(f"Ошибка соединения: {e}")
                print(response.text)
        elif r == 2:
            try:
                url = f"{base_url}/leads"
                response = requests.post(url, json=new_lead)
                print(f"Статус: {response.status_code}")
                if response.status_code == 200 or response.status_code == 201:
                    print("Ответ от 1С:", response.text)
                else:
                    print("Ошибка:", response.reason)
                    print(response.text)
            except Exception as e:
                print(f"Ошибка соединения: {e}")
        elif r == 3:
            url = f"{base_url}/lead"
            lead_id = int(input("введите номер лида: "))
            try:
                response = requests.post(url, json=lead_id)
                print(f"Статус: {response.status_code}")
                if response.status_code == 200 or response.status_code == 201:
                    print("Ответ от 1С:", response.text)
                else:
                    print("Ошибка:", response.reason)
                    print(response.text)
            except Exception as e:
                print(f"Ошибка соединения: {e}")
    except Exception as e:
        print(e)
