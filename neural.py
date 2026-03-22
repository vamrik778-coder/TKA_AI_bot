import requests
import json
import re

import os
from dotenv import load_dotenv

load_dotenv()

# ===== НАСТРОЙКИ YANDEX GPT =====
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
YANDEX_MODEL = "yandexgpt-lite"

def clean_latex(text: str) -> str:
    """Очистка LaTeX-мусора"""
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
    subject: предмет (mathematics, physics, russian...)
    task: текст задачи
    mode: 'full' — подробно, 'short' — кратко, 'cute' — ласково
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

    # Перевод предмета на русский
    subject_ru = {
        "mathematics": "математика", "physics": "физика", "chemistry": "химия",
        "biology": "биология", "russian": "русский язык", "history": "история",
        "geography": "география", "society": "обществознание",
        "literature": "литература", "music": "музыка"
    }.get(subject, subject)

    # Базовый промпт
    base_prompt = (
        "Ты учитель. Отвечай максимально понятно для школьника. "
        "СТРОГО ЗАПРЕЩЕНО использовать LaTeX-разметку. "
        "Пиши формулы в простом текстовом виде: дроби как 'a/b', степени как 'x^2', корни как '√16', знак ± как '±'.\n"
        "ЗАПРЕЩЕНО добавлять предупреждения о списывании, морализаторство и рассуждения на тему учёбы. "
        "Только решение задачи. Если это геометрия — просто найди угол, сторону, докажи.\n"
    )

    # Промпты для каждого предмета
    subject_prompts = {
        "математика": base_prompt + "Ты учитель математики. Решай уравнения и задачи по шагам.",
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

    # Режимы ответа
    mode_prompts = {
        'full': "Объясняй максимально подробно, с примерами, по шагам.",
        'short': "Отвечай максимально кратко, только суть. Без лишних объяснений.",
        'cute': (
            "Ты очень милый и заботливый учитель. Обращайся ласково: 'зайка', 'солнышко', 'пупсик'. "
            "Добавляй комплименты: 'ты умничка', 'у тебя отлично получается'. "
            "Используй смайлики: 🥰 💕 🌸. Но НЕ выходи за рамки — это учебный бот."
        )
    }

    system_prompt = subject_prompts.get(subject_ru, base_prompt) + " " + mode_prompts.get(mode, mode_prompts['full'])

    # Формируем запрос
    body = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/{YANDEX_MODEL}",
        "completionOptions": {"stream": False, "temperature": 0.2, "maxTokens": 800},
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": task}
        ]
    }

    try:
        response = requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Api-Key {YANDEX_API_KEY}"
            },
            json=body,
            timeout=30
        )
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