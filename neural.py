import requests
import json
import asyncio
import math
import re

# ===== НАСТРОЙКИ YANDEX GPT =====
YANDEX_API_KEY = "AQVNya2KqtOWB9v5kLrdtPSFOoTGOiiVm7p7fzOw"
YANDEX_FOLDER_ID = "b1gv2lll7placgqgcv61"
YANDEX_MODEL = "yandexgpt-lite"

def clean_latex(text: str) -> str:
    """Упрощённая зачистка LaTeX-мусора"""
    
    print(f"\n🧹 clean_latex: НАЧАЛО ОБРАБОТКИ")
    print(f"🧹 Входной текст, длина: {len(text)}")
    print(f"🧹 Первые 50 символов: {text[:50]}")
    
    if not text:
        print("🧹 Текст пустой, возвращаем как есть")
        return ""
    
    original = text
    
    try:
        # Шаг 1: Убираем доллары
        text = text.replace('$', '')
        
        # Шаг 2: Убираем обратные слеши
        text = text.replace('\\', '')
        
        # Шаг 3: Заменяем точки умножения
        text = text.replace('·', '*')
        
        # Шаг 4: Заменяем frac{}{} на дроби
        text = re.sub(r'frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', text)
        
        # Шаг 5: Убираем оставшиеся фигурные скобки
        text = re.sub(r'\{([^}]+)\}', r'\1', text)
        
        # Шаг 6: Заменяем команды
        text = text.replace('pm', '±')
        text = text.replace('cdot', '*')
        text = text.replace('sqrt', '√')
        text = text.replace('frac', '')
        
        # Шаг 7: Убираем множественные пробелы
        text = re.sub(r'\s+', ' ', text)
        
        # Шаг 8: Исправляем дроби вида (число)/(число) -> число/число
        text = re.sub(r'\((\d+)\)/\((\d+)\)', r'\1/\2', text)
        text = re.sub(r'\((-?\d+)\)/\((-?\d+)\)', r'\1/\2', text)
        
        # Шаг 9: Убираем лишние скобки вокруг выражений
        text = re.sub(r'\(([^)]+)\)', r'\1', text)
        
        print(f"🧹 clean_latex: ИТОГО")
        print(f"🧹 Было символов: {len(original)}, стало: {len(text)}")
        print(f"🧹 Первые 50 символов результата: {text[:50]}")
        print(f"🧹 clean_latex: КОНЕЦ ОБРАБОТКИ\n")
        
        return text.strip()
        
    except Exception as e:
        print(f"❌ ОШИБКА В clean_latex: {e}")
        return original


async def get_neural_response(subject: str, task: str) -> str:
    """
    Отправляет запрос в YandexGPT и получает ответ
    subject: предмет на английском (mathematics, physics, russian, history...)
    task: текст задачи
    """
    
    # Простые вычисления делаем сами (только для математики)
    if subject == "mathematics":
        try:
            expr = task.lower()
            expr = expr.replace('умножить', '*')
            expr = expr.replace('на', '')
            expr = expr.replace(' ', '')
            expr = expr.replace(',', '.')
            
            if re.match(r'^[0-9+\-*/().]+$', expr):
                result = eval(expr)
                return f"📐 Решение:\n{task} = {result}"
        except Exception as e:
            print(f"Ошибка вычисления: {e}")
    
    # Переводим предмет на русский
    subject_ru = {
        "mathematics": "математика",
        "physics": "физика",
        "chemistry": "химия",
        "biology": "биология",
        "russian": "русский язык",
        "history": "история",
        "geography": "география",
        "society": "обществознание",
        "literature": "литература",
        "music": "музыка"
    }.get(subject, subject)
    
    # Базовый промпт (без привязки к предмету)
    base_prompt = (
        "Ты учитель. Отвечай максимально понятно для школьника. "
        "СТРОГО ЗАПРЕЩЕНО использовать LaTeX-разметку: никаких frac, cdot, pm, обратных слешей. "
        "Пиши все формулы в простом текстовом виде:\n"
        "- Дроби пиши ТОЛЬКО через слеш: (-b ± √D)/(2a) или (35 + √1261)/2\n"
        "- Умножение обозначай звёздочкой * или просто пиши слитно: 4ac или 4*a*c\n"
        "- Степени пиши как x^2\n"
        "- Корни пиши как √1261\n"
        "- Знак плюс-минус как ±\n\n"
        "Каждый шаг решения ОБЯЗАТЕЛЬНО начинай с новой строки с отступом в 2 пробела.\n\n"
    )
    
    # Промпты для каждого предмета
    subject_prompts = {
    "математика": base_prompt + "Ты учитель математики. Решай уравнения по шагам. Каждый шаг объясняй словами. Используй формулы, корни, степени.",
    "физика": base_prompt + "Ты учитель физики. Оформляй решение с Дано, Найти, Решение, Ответ. Объясняй физический смысл, законы, формулы.",
    "химия": base_prompt + "Ты учитель химии. Уравнивай реакции, объясняй процессы. Используй химические формулы (H2O, CO2, NaCl).",
    "биология": base_prompt + "Ты учитель биологии. Объясняй биологические процессы простым языком, приводи примеры. Рассказывай о клетках, организмах, эволюции.",
    "русский язык": base_prompt + "Ты учитель русского языка. Объясняй правила орфографии, пунктуации, грамматики. Делай разбор слов и предложений.",
    "история": base_prompt + "Ты учитель истории. Рассказывай об исторических событиях, личностях, датах. Объясняй причины и следствия. Отвечай на вопросы по истории.",
    "география": base_prompt + "Ты учитель географии. Рассказывай о странах, континентах, реках, горах, климате, населении. Используй факты и цифры.",
    "обществознание": base_prompt + "Ты учитель обществознания. Объясняй темы по праву, экономике, политике, социальным отношениям. Приводи примеры из жизни.",
    "литература": base_prompt + "Ты учитель литературы. Рассказывай о писателях, поэтах, произведениях. Анализируй тексты, объясняй сюжет, героев, идеи.",
    "музыка": base_prompt + "Ты учитель музыки. Рассказывай о композиторах, произведениях, музыкальной теории. Объясняй ноты, аккорды, жанры."
}
    
    system_prompt = subject_prompts.get(subject_ru, base_prompt + f"Ты учитель {subject_ru}. Отвечай на вопросы по предмету.")
    
    return await call_yandexgpt(system_prompt, task, subject_ru)


async def call_yandexgpt(system_prompt: str, user_task: str, subject: str) -> str:
    """Вызов YandexGPT API с правильной кодировкой"""
    
    body = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/{YANDEX_MODEL}",
        "completionOptions": {
            "stream": False,
            "temperature": 0.2,
            "maxTokens": 800
        },
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": user_task}
        ]
    }
    
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Api-Key {YANDEX_API_KEY}"
    }
    
    try:
        print("=" * 50)
        print("🔍 НАЧАЛО ЗАПРОСА К YANDEXGPT")
        print(f"📌 Subject: {subject}")
        print(f"📌 Task: {user_task[:100]}...")
        print(f"📌 Model: {YANDEX_MODEL}")
        print(f"📌 Folder ID: {YANDEX_FOLDER_ID[:10]}...")
        print(f"📌 API Key: {YANDEX_API_KEY[:10]}...")
        
        json_str = json.dumps(body, ensure_ascii=False).encode('utf-8')
        print(f"📦 Размер запроса: {len(json_str)} байт")
        
        print("📤 Отправляю запрос...")
        response = requests.post(url, headers=headers, data=json_str, timeout=30)
        
        print(f"📥 Статус ответа: {response.status_code}")
        
        if response.status_code != 200:
            error_text = response.text
            print(f"❌ Ошибка HTTP: {error_text[:500]}")
            return f"❌ Ошибка HTTP {response.status_code}. Проверь ключи."
        
        try:
            result = response.json()
            print("✅ JSON успешно распарсен")
        except Exception as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            return f"❌ Ошибка: ответ не в формате JSON"
        
        if 'result' in result:
            print("✅ Найден ключ 'result'")
            alternatives = result['result'].get('alternatives', [])
            if alternatives:
                answer = alternatives[0]['message']['text']
                
                print("\n" + "="*50)
                print("🔍 ОТВЕТ ОТ YANDEXGPT:")
                print("="*50)
                print(answer[:300] + "..." if len(answer) > 300 else answer)
                print("="*50 + "\n")
                
                print(f"✅ Получен ответ, длина: {len(answer)} символов")
                
                if not answer:
                    return "❌ Получен пустой ответ от нейросети."
                
                cleaned_answer = clean_latex(answer)
                print(f"✅ Ответ после clean_latex, длина: {len(cleaned_answer)} символов")
                
                emoji = {
                    "математика": "📐",
                    "физика": "⚡",
                    "химия": "🧪",
                    "биология": "🧬",
                    "русский язык": "📖",
                    "история": "📜",
                    "география": "🌍",
                    "обществознание": "⚖️",
                    "литература": "📚",
                    "музыка": "🎵"
                }.get(subject, "🤖")
                
                return f"{emoji} {subject.title()}:\n\n{cleaned_answer}"
            else:
                return "❌ Ошибка: пустой ответ от нейросети"
        else:
            error_msg = result.get('error', {}).get('message', 'Неизвестная ошибка')
            return f"❌ Ошибка YandexGPT: {error_msg}"
            
    except requests.exceptions.Timeout:
        return "❌ Превышено время ожидания ответа от нейросети. Попробуй ещё раз."
    except requests.exceptions.ConnectionError:
        return "❌ Ошибка соединения с YandexGPT. Проверь интернет."
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return f"❌ Ошибка подключения: {e}"
    finally:
        print("=" * 50)