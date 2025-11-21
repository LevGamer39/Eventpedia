import gigachat
from gigachat.models import Chat, Messages, MessagesRole
import json
import re
# Заглушка, если конфига нет
try:
    from config import GIGACHAT_API_KEY
except ImportError:
    GIGACHAT_API_KEY = "YOUR_KEY"

class GigaChatService:
    def __init__(self):
        self.api_key = GIGACHAT_API_KEY
        
    def analyze_event(self, text: str, user_criteria: list = None) -> dict:
        try:
            client = gigachat.GigaChat(credentials=self.api_key, verify_ssl_certs=False)
            
            criteria_str = ", ".join(user_criteria) if user_criteria else "IT, Разработка, Менеджмент, AI, Data Science"
            
            prompt = f"""
Ты профессиональный аналитик IT-мероприятий. Твоя задача — извлечь факты из текста и оценить важность события.

ТЕКСТ СОБЫТИЯ:
{text[:2500]}

КРИТЕРИИ ПОЛЬЗОВАТЕЛЯ ДЛЯ ПОИСКА:
[{criteria_str}]

ИНСТРУКЦИЯ:
1. Название: Если нет явного, придумай короткое и понятное.
2. Дата: Приведи к формату "DD.MM.YYYY HH:MM" или напиши "Не указана".
3. Место: Город и локация. Если онлайн — пиши "Онлайн".
4. SCORE (0-100): Оцени релевантность события КРИТЕРИЯМ ПОЛЬЗОВАТЕЛЯ. 
   - Если событие точно совпадает с критериями — ставь > 80.
   - Если событие про IT, но тема косвенная — 50-79.
   - Если мусор или не IT — < 40.
5. Приоритет: "high" если score >= 80, иначе "medium" или "low".

ВЕРНИ СТРОГО JSON (без Markdown):
{{
    "title": "string",
    "description": "string (кратко суть)",
    "date": "string",
    "location": "string",
    "url": "string (если есть в тексте)",
    "score": int,
    "priority": "high/medium/low",
    "target_audience": "string",
    "key_themes": ["theme1", "theme2"]
}}
"""
            messages = [Messages(role=MessagesRole.USER, content=prompt)]
            response = client.chat(Chat(messages=messages, temperature=0.1)) # Низкая температура для точности
            content = response.choices[0].message.content
            
            # Очистка от markdown если модель вернула ```json
            content = re.sub(r"```json|```", "", content).strip()
            
            result = json.loads(content)
            
            # Дополнительная проверка на стороне кода
            result = self._post_process_analysis(result, user_criteria)
            return result
            
        except Exception as e:
            print(f"GigaChat analysis error: {e}")
            return self._get_default_analysis()

    def _post_process_analysis(self, result: dict, criteria: list) -> dict:
        """Дополнительная корректировка оценки"""
        score = result.get('score', 50)
        
        # Если модель ошиблась и не выставила приоритет
        if score >= 80:
            result['priority'] = 'high'
        elif score >= 50:
            result['priority'] = 'medium'
        else:
            result['priority'] = 'low'
            
        return result

    def analyze_file_content(self, text: str) -> list:
        """Анализ загруженного файла (без изменений логики, только промпт)"""
        try:
            client = gigachat.GigaChat(credentials=self.api_key, verify_ssl_certs=False)
            prompt = f"""Найди все мероприятия в тексте и верни список JSON объектов.
Текст: {text[:4000]}
JSON Format: [{{ "title": "...", "date": "...", "location": "...", "description": "..." }}]"""
            
            messages = [Messages(role=MessagesRole.USER, content=prompt)]
            response = client.chat(Chat(messages=messages, temperature=0.1))
            content = re.sub(r"```json|```", "", response.choices[0].message.content).strip()
            return json.loads(content)
        except: return []

    def _get_default_analysis(self):
        return {
            "title": "Неизвестное событие",
            "date": "Не указана",
            "location": "Не определено",
            "score": 0,
            "priority": "low",
            "description": "Ошибка анализа",
            "target_audience": "Все",
            "key_themes": []
        }