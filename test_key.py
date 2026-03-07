import requests

# ⚠️ ВСТАВЬ СВОЙ API-КЛЮЧ (тот же, что в vision.py)
API_KEY = "AQVNydFogQDVFrSpTG6jHBxTDn2m4nNYEWwCzbAW"

print("🔍 ТЕСТИРУЕМ API-КЛЮЧ...")
print(f"Ключ (первые 10): {API_KEY[:10]}...")

# Тест 1: Получение IAM-токена
print("\n1️⃣ Пробуем получить IAM-токен...")
response = requests.post(
    "https://iam.api.cloud.yandex.net/iam/v1/tokens",
    json={"yandexPassportOauthToken": API_KEY}
)

print(f"Статус: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print("✅ IAM-токен получен!")
    print(f"Токен (первые 20): {data.get('iamToken', '')[:20]}...")
else:
    print(f"❌ Ошибка: {response.text}")

# Тест 2: Прямой запрос к Vision API
print("\n2️⃣ Пробуем прямой запрос к Vision API...")
vision_url = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"
vision_headers = {
    "Content-Type": "application/json",
    "Authorization": f"Api-Key {API_KEY}"
}
vision_body = {
    "folderId": "b1gv2lll7placgqgcv61",
    "analyze_specs": [{
        "content": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
        "features": [{"type": "TEXT_DETECTION"}]
    }]
}

response = requests.post(vision_url, headers=vision_headers, json=vision_body)
print(f"Статус: {response.status_code}")
print(f"Ответ: {response.text[:200]}")

input("\nНажми Enter для выхода...")