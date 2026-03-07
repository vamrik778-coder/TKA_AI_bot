import requests

API_KEY = "AQVNydFogQDVFrSpTG6jHBxTDn2m4nNYEWwCzbAW"

# Тест IAM токена
response = requests.post(
    "https://iam.api.cloud.yandex.net/iam/v1/tokens",
    json={"yandexPassportOauthToken": API_KEY}
)

print(f"Статус: {response.status_code}")
print(f"Ответ: {response.text}")