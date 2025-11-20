import gigachat
from gigachat.models import Chat, Messages, MessagesRole
import json
import re
from config import GIGACHAT_API_KEY, EVENT_CRITERIA

class GigaChatService:
    def __init__(self):
        self.api_key = GIGACHAT_API_KEY
        
    def analyze_event(self, text: str) -> dict:
        try:
            client = gigachat.GigaChat(credentials=self.api_key, verify_ssl_certs=False)
            
            prompt = f"""Ты AI-аналитик Центра исследований и разработки Сбера в Санкт-Петербурге.
Проанализируй описание мероприятия по критериям релевантности для IT-специалистов Сбера.

КРИТЕРИИ ЦЕНТРА СБЕРА:
- Целевая аудитория: {', '.join(EVENT_CRITERIA['target_audience'])}
- Приоритетные темы: {', '.join(EVENT_CRITERIA['themes'])}
- География: Санкт-Петербург и ЛО
- Масштаб: от 50+ участников
- Уровень: экспертные сессии, конференции, стратегические встречи
- Приоритетные организаторы: {', '.join(EVENT_CRITERIA['premium_organizers'])}

ИНСТРУКЦИЯ:
1. Извлеки: название, дату, место, целевую аудиторию, количество участников, а также ключевых спикеров
2. Определи формат регистрации, условия участия, порядок оплаты
3. Оцени релевантность (0-100) для IT-специалистов Сбера
4. Определи IT-тематику (true/false)
5. Проанализируй уровень мероприятия и приоритет
6. Определи ключевые темы и организаторов

ВЕРНИ ТОЛЬКО JSON БЕЗ ФОРМАТИРОВАНИЯ:
{{
    "title": "Короткое ясное название",
    "date": "Дата или 'Не указана'",
    "location": "Место проведения",
    "score": 85,
    "is_it_related": true,
    "summary": "Краткая суть (1-2 предложения)",
    "target_audience": "Конкретная аудитория",
    "level": "экспертный/отраслевой/региональный/международный",
    "expected_participants": "количество участников",
    "registration_format": "онлайн/офлайн/гибрид",
    "participation_conditions": "открытое/по приглашению/платное",
    "payment_info": "бесплатно/платно/сумма",
    "organizers": ["организатор1", "организатор2"],
    "key_themes": ["AI", "Data Science", "Разработка"],
    "key_speakers": ["спикер1", "спикер2"],
    "priority": "high/medium/low",
    "recommendation": "рекомендовать/рассмотреть/пропустить"
}}

Текст для анализа: {text[:2000]}"""

            messages = [Messages(role=MessagesRole.USER, content=prompt)]
            response = client.chat(Chat(messages=messages, temperature=0.3))
            content = response.choices[0].message.content
            
            content = re.sub(r"```json|```", "", content).strip()
            
            result = json.loads(content)
            
            result = self._apply_scoring_rules(result, text)
                
            return result
            
        except Exception as e:
            print(f"GigaChat analysis error: {e}")
            return self._get_default_analysis()

    def _apply_scoring_rules(self, result: dict, text: str) -> dict:
        score = result.get('score', 0)
        
        if any(theme.lower() in text.lower() for theme in ['AI', 'искусственный интеллект', 'нейросети', 'машинное обучение']):
            score = min(score + 15, 100)
            
        if any(org in text for org in EVENT_CRITERIA['premium_organizers']):
            score = min(score + 20, 100)
            result['priority'] = 'high'
            
        if any(keyword in text for keyword in ['стратегическая сессия', 'вице-губернатор', 'правительство']):
            score = min(score + 25, 100)
            result['priority'] = 'high'
            
        if '100+' in text or '500+' in text or '1000+' in text:
            score = min(score + 10, 100)
            
        if 'СПб' in text or 'Санкт-Петербург' in text:
            score = min(score + 5, 100)
            
        result['score'] = score
        return result

    def _get_default_analysis(self):
        return {
            "title": "Не удалось распознать",
            "date": "Не указана",
            "location": "СПб",
            "score": 0,
            "is_it_related": False,
            "summary": "Ошибка анализа",
            "target_audience": "Не определена",
            "level": "неизвестно",
            "expected_participants": "неизвестно",
            "registration_format": "не указан",
            "participation_conditions": "не указаны",
            "payment_info": "не указано",
            "organizers": [],
            "key_themes": [],
            "key_speakers": [],
            "priority": "low",
            "recommendation": "пропустить"
        }

    def analyze_file_content(self, text: str) -> list:
        try:
            client = gigachat.GigaChat(credentials=self.api_key, verify_ssl_certs=False)
            
            prompt = f"""Ты AI-аналитик Центра исследований и разработки Сбера. 
Из текста документа извлеки все упоминания о мероприятиях, событиях, конференциях, встречах.

Для каждого мероприятия верни JSON массив с объектами:
[
    {{
        "title": "Название мероприятия",
        "date": "Дата проведения",
        "location": "Место проведения", 
        "description": "Полное описание",
        "organizer": "Организатор",
        "participants": "Количество участников",
        "themes": ["тема1", "тема2"],
        "registration_info": "Информация о регистрации",
        "payment_info": "Информация об оплате",
        "conditions": "Условия участия"
    }}
]

Текст документа: {text[:4000]}"""

            messages = [Messages(role=MessagesRole.USER, content=prompt)]
            response = client.chat(Chat(messages=messages, temperature=0.3))
            content = response.choices[0].message.content
            
            content = re.sub(r"```json|```", "", content).strip()
            
            events = json.loads(content)
            return events if isinstance(events, list) else []
            
        except Exception as e:
            print(f"GigaChat file analysis error: {e}")
            return []