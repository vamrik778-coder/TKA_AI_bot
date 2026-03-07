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
    """Зачистка LaTeX-мусора"""
    if not text:
        return ""
    
    text = text.replace('\\', '')
    text = re.sub(r'frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', text)
    text = re.sub(r'\{([^}]+)\}', r'\1', text)
    text = text.replace('pm', '±').replace('cdot', '*').replace('sqrt', '√')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

async def get_neural_response(subject: str, task: str, mode: str = 'full') -> str:
    """
    Отправляет запрос в YandexGPT и получает ответ
    mode: 'full' — подробно, 'short' — кратко, 'cute' — пупсик
    """
    
    # Простые вычисления для математики
    if subject == "mathematics":
        try:
            expr = task.lower().replace(' ', '').replace(',', '.')
            expr = expr.replace('умножить', '*').replace('на', '')
            if re.match(r'^[0-9+\-*/().]+$', expr):
                result = eval(expr)
                return f"📐 Решение:\n{task} = {result}"
        except:
            pass

    subject_ru = {
        "mathematics": "математика", "physics": "физика", "chemistry": "химия",
        "biology": "биология", "russian": "русский язык", "history": "история",
        "geography": "география", "society": "обществознание",
        "literature": "литература", "music": "музыка"
    }.get(subject, subject)

    base_prompt = (
        "Ты учитель. Отвечай максимально понятно для школьника. "
        "ЗАПРЕЩЕНО использовать LaTeX-разметку. "
        "Пиши формулы в простом текстовом виде:\n"
        "- Дроби как 'a/b' или '(x+1)/(x-2)'\n"
        "- Степени как 'x^2'\n"
        "- Корни как '√16'\n"
        "- Знак плюс-минус как '±'\n\n"
    )

    subject_prompts = {
        "математика": base_prompt + "Ты учитель математики. Решай уравнения по шагам.",
        "физика": base_prompt + "Ты учитель физики. Оформляй решение с Дано, Найти, Решение, Ответ.",
        "химия": base_prompt + "Ты учитель химии. Уравнивай реакции, объясняй процессы.",
        "биология": base_prompt + "Ты учитель биологии. Объясняй биологические процессы простым языком.",
        "русский язык": base_prompt + "Ты учитель русского языка. Объясняй правила, делай разбор.",
        "история": base_prompt + "Ты учитель истории. Рассказывай об исторических событиях и личностях.",
        "география": base_prompt + "Ты учитель географии. Рассказывай о странах, реках, горах.",
        "обществознание": base_prompt + "Ты учитель обществознания. Объясняй темы по праву, экономике, политике.",
        "литература": base_prompt + "Ты учитель литературы. Рассказывай о писателях и произведениях.",
        "музыка": base_prompt + "Ты учитель музыки. Рассказывай о композиторах и произведениях."
    }

    # Выбор режима
    mode_prompts = {
        'full': "Объясняй максимально подробно, с примерами, по шагам. Пиши как учитель для ученика.",
        'short': "Отвечай максимально кратко, только суть. Без лишних объяснений. Если задача — дай ответ и краткое решение в 1-2 строки.",
        'cute': (
            "Ты очень милый и заботливый учитель. "
            "Обращайся к ученику ласково: 'зайка', 'солнышко', 'пупсик', 'милый', 'родной'. "
            "Добавляй комплименты: 'ты такой умничка', 'у тебя отлично получается', 'я в тебя верю'. "
            "Используй много смайликов: 🥰 💕 🌸 🌟 💖 🥺 💞. "
            "Но при этом НЕ выходи за рамки — это учебный бот. Решай задачи правильно, но с любовью."
        )
    }
    mode_instruction = mode_prompts.get(mode, mode_prompts['full'])

    system_prompt = subject_prompts.get(subject_ru, base_prompt) + " " + mode_instruction

    # Вызов API (без изменений, как у тебя было)
    body = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/{YANDEX_MODEL}",
        "completionOptions": {"stream": False, "temperature": 0.2, "maxTokens": 800},
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": task}
        ]
    }
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {"Content-Type": "application/json; charset=utf-8", "Authorization": f"Api-Key {YANDEX_API_KEY}"}

    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
        if response.status_code != 200:
            return "❌ Ошибка API."
        result = response.json()
        answer = result['result']['alternatives'][0]['message']['text']
        cleaned = clean_latex(answer)

        emoji = {
            "математика": "📐", "физика": "⚡", "химия": "🧪", "биология": "🧬",
            "русский язык": "📖", "история": "📜", "география": "🌍",
            "обществознание": "⚖️", "литература": "📚", "музыка": "🎵"
        }.get(subject_ru, "🤖")
        return f"{emoji} {subject_ru.title()}:\n\n{cleaned}"
    except Exception as e:
        return f"❌ Ошибка: {e}"