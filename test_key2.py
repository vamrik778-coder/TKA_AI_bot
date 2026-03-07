import requests

# ⚠️ ТВОИ ДАННЫЕ (свежие!)
API_KEY = "AQVNya2KqtOWB9v5kLrdtPSFOoTGOiiVm7p7fzOw"
FOLDER_ID = "b1gv2lll7placgqgcv61"

print("🔍 ТЕСТИРУЕМ API-КЛЮЧ НАПРЯМУЮ...")
print(f"Ключ: {API_KEY}")
print(f"Folder ID: {FOLDER_ID}")

# Пробуем прямой запрос к Vision API
url = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Api-Key {API_KEY}"
}

# Минимальное тестовое изображение (1x1 пиксель, прозрачный)
body = {
    "folderId": FOLDER_ID,
    "analyze_specs": [{
        "content": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
        "features": [{"type": "TEXT_DETECTION"}]
    }]
}

print("\n📤 Отправляю запрос...")
response = requests.post(url, headers=headers, json=body)

print(f"\n📥 Статус ответа: {response.status_code}")

if response.status_code == 200:
    print("✅ УСПЕХ! Ключ работает!")
    print(f"Ответ: {response.text[:200]}")
else:
    print(f"❌ ОШИБКА: {response.status_code}")
    print(f"Текст ошибки: {response.text[:500]}")

input("\nНажми Enter для выхода...")