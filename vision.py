import base64
import requests
import json
import sys
import time

# ============================================
# ⚠️ ТВОИ КЛЮЧИ (РАБОЧИЕ!)
# ============================================
YANDEX_API_KEY = "AQVNya2KqtOWB9v5kLrdtPSFOoTGOiiVm7p7fzOw"
YANDEX_FOLDER_ID = "b1gv2lll7placgqgcv61"

async def recognize_text_from_photo(photo_bytes: bytes) -> str:
    """
    Распознаёт текст на фото через Yandex Vision OCR
    Возвращает распознанный текст или None
    """
    print("\n" + "="*70)
    print("🔍 НАЧАЛО РАСПОЗНАВАНИЯ ТЕКСТА")
    print("="*70)
    
    print(f"📸 Размер фото: {len(photo_bytes)} байт")
    sys.stdout.flush()
    
    # Кодируем фото в base64
    try:
        print("🔄 Кодирую фото в base64...")
        encoded_image = base64.b64encode(photo_bytes).decode('utf-8')
        print(f"✅ Успешно закодировано: {len(encoded_image)} символов")
        sys.stdout.flush()
    except Exception as e:
        print(f"❌ Ошибка кодирования: {e}")
        return None
    
    # Формируем запрос к Yandex Vision
    body = {
        "folderId": YANDEX_FOLDER_ID,
        "analyze_specs": [{
            "content": encoded_image,
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
        "Authorization": f"Api-Key {YANDEX_API_KEY}"
    }
    
    print("📤 Отправляю запрос в Yandex Vision...")
    sys.stdout.flush()
    
    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
        print(f"📥 Статус ответа: {response.status_code}")
        sys.stdout.flush()
        
        if response.status_code != 200:
            error_text = response.text[:500]
            print(f"❌ Ошибка HTTP {response.status_code}: {error_text}")
            sys.stdout.flush()
            return None
        
        print("✅ Запрос успешен, парсим JSON...")
        result = response.json()
        print("✅ JSON получен")
        sys.stdout.flush()
        
        # ===== АНАЛИЗ СТРУКТУРЫ ОТВЕТА =====
        print("\n📊 АНАЛИЗ ОТВЕТА:")
        print(f"Ключи верхнего уровня: {list(result.keys())}")
        sys.stdout.flush()
        
        # Проверяем наличие results
        if 'results' not in result:
            print("❌ Нет поля 'results' в ответе")
            return None
        
        if not result['results']:
            print("❌ Пустой список results")
            return None
        
        print(f"✅ Найдено results: {len(result['results'])}")
        
        # Первый уровень results
        first_level = result['results'][0]
        print(f"Ключи в первом уровне: {list(first_level.keys())}")
        sys.stdout.flush()
        
        # Проверяем наличие второго уровня results
        if 'results' not in first_level:
            print("❌ Нет поля 'results' в первом уровне")
            return None
        
        if not first_level['results']:
            print("❌ Пустой список во втором уровне")
            return None
        
        second_level = first_level['results'][0]
        print(f"Ключи во втором уровне: {list(second_level.keys())}")
        sys.stdout.flush()
        
        # Проверяем на ошибки
        if 'error' in second_level:
            print(f"❌ Ошибка Vision: {second_level['error']}")
            return None
        
        # Проверяем наличие textDetection
        if 'textDetection' not in second_level:
            print("❌ Нет поля 'textDetection' в ответе")
            return None
        
        text_detection = second_level['textDetection']
        print(f"✅ Найден textDetection!")
        print(f"Ключи в textDetection: {list(text_detection.keys())}")
        sys.stdout.flush()
        
        # ===== ИЗВЛЕКАЕМ ТЕКСТ =====
        
        # Способ 1: Пробуем получить полный текст
        full_text = text_detection.get('fullText', '')
        if full_text:
            print(f"✅ Найден полный текст: {len(full_text)} символов")
            print(f"📝 Первые 200 символов: {full_text[:200]}")
            sys.stdout.flush()
            return full_text
        
        print("⚠️ fullText пуст, пробую собрать из блоков...")
        
        # Способ 2: Собираем текст из блоков
        if 'pages' in text_detection:
            all_text = []
            for page_idx, page in enumerate(text_detection['pages']):
                print(f"📄 Обрабатываю страницу {page_idx + 1}")
                sys.stdout.flush()
                
                if 'blocks' not in page:
                    print("  ⚠️ Нет блоков на странице")
                    continue
                
                for block in page['blocks']:
                    if 'lines' not in block:
                        continue
                    
                    for line in block['lines']:
                        if 'words' in line:
                            line_text = []
                            for word in line['words']:
                                if 'text' in word:
                                    line_text.append(word['text'])
                            if line_text:
                                all_text.append(' '.join(line_text))
            
            if all_text:
                result_text = '\n'.join(all_text)
                print(f"✅ Собрано из блоков: {len(result_text)} символов")
                print(f"📝 Первые 200 символов: {result_text[:200]}")
                sys.stdout.flush()
                return result_text
            else:
                print("❌ Не удалось собрать текст из блоков")
                return None
        
        print("❌ Текст не найден в ответе")
        return None
        
    except requests.exceptions.Timeout:
        print("❌ Таймаут при запросе к Vision API")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка соединения с Vision API")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        return None
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None