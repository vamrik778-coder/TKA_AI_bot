import asyncio
import base64
import requests
import json

API_KEY = "AQVNya2KqtOWB9v5kLrdtPSFOoTGOiiVm7p7fzOw"
FOLDER_ID = "b1gv2lll7placgqgcv61"

async def test_vision():
    print("🔍 ТЕСТ YANDEX VISION")
    print("="*50)
    
    # Берём последнее фото
    import glob
    files = glob.glob("task_*.jpg")
    if not files:
        print("❌ Нет файлов task_*.jpg")
        return
    
    filename = files[-1]
    print(f"📸 Тестирую файл: {filename}")
    
    with open(filename, "rb") as f:
        photo_bytes = f.read()
    
    print(f"📸 Размер: {len(photo_bytes)} байт")
    
    encoded = base64.b64encode(photo_bytes).decode('utf-8')
    
    body = {
        "folderId": FOLDER_ID,
        "analyze_specs": [{
            "content": encoded,
            "features": [{
                "type": "TEXT_DETECTION",
                "text_detection_config": {
                    "language_codes": ["ru", "en"]
                }
            }]
        }]
    }
    
    url = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {API_KEY}"
    }
    
    print("📤 Отправляю запрос...")
    response = requests.post(url, headers=headers, json=body)
    
    print(f"📥 Статус: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Ошибка: {response.text}")
        return
    
    result = response.json()
    
    # Парсим текст
    try:
        if 'results' in result and result['results']:
            first_result = result['results'][0]
            
            if 'error' in first_result:
                print(f"❌ Ошибка: {first_result['error']}")
                return
            
            if 'textDetection' in first_result:
                text_detection = first_result['textDetection']
                
                # Извлекаем полный текст
                full_text = text_detection.get('fullText', '')
                if full_text:
                    print("\n" + "="*50)
                    print("📝 РАСПОЗНАННЫЙ ТЕКСТ:")
                    print("="*50)
                    print(full_text)
                    print("="*50)
                    print(f"\n✅ Найдено символов: {len(full_text)}")
                else:
                    print("❌ Поле fullText пустое")
                    
                    # Если fullText пустой, пробуем собрать из блоков
                    if 'pages' in text_detection:
                        all_text = []
                        for page in text_detection['pages']:
                            if 'blocks' in page:
                                for block in page['blocks']:
                                    if 'lines' in block:
                                        for line in block['lines']:
                                            if 'words' in line:
                                                line_text = []
                                                for word in line['words']:
                                                    if 'text' in word:
                                                        line_text.append(word['text'])
                                                all_text.append(' '.join(line_text))
                        full_text = '\n'.join(all_text)
                        if full_text:
                            print("\n📝 СОБРАННЫЙ ТЕКСТ:")
                            print(full_text)
    except Exception as e:
        print(f"❌ Ошибка парсинга: {e}")
    
    print("\n📦 Полный ответ для отладки:")
    print(json.dumps(result, indent=2, ensure_ascii=False)[:1000])

asyncio.run(test_vision())