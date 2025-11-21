import requests
import re
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class ParserService:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Cache-Control': 'no-cache'
        }

    def _get_soup(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            if response.status_code == 200:
                if response.encoding == 'ISO-8859-1':
                    response.encoding = response.apparent_encoding
                return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"Ошибка доступа к {url}: {e}")
        return None

    def _clean_text(self, text):
        if not text: return ""
        return re.sub(r'\s+', ' ', text).strip()

    def _filter_by_keywords(self, text, keywords):
        if not keywords: return True
        text_lower = text.lower()
        for kw in keywords:
            if kw.lower() in text_lower: return True
        return False

    def _heuristic_parse(self, soup, source_config, keywords):
        events = []
        seen_links = set()
        base_url = source_config.get('base_url', source_config['url'])

        potential_blocks = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'event|card|item|post', re.I))
        if not potential_blocks: potential_blocks = soup.find_all('a')

        for block in potential_blocks:
            if block.find_parent(['nav', 'footer', 'header']): continue

            link_elem = block if block.name == 'a' else block.find('a', href=True)
            if not link_elem: continue

            link = link_elem['href']
            if not link.startswith('http'): link = urljoin(base_url, link)

            title_elem = block.find(['h2', 'h3', 'h4', 'div'], class_=re.compile(r'title|name', re.I))
            raw_text = block.get_text(" ", strip=True)
            title = title_elem.get_text(" ", strip=True) if title_elem else link_elem.get_text(" ", strip=True)
            
            full_text = f"{title} {raw_text}"
            clean_text = self._clean_text(full_text)

            if len(clean_text) < 15: continue
            if link in seen_links: continue
            if not self._filter_by_keywords(clean_text, keywords): continue

            is_event = any(w in clean_text.lower() for w in ['регистрац', 'участие', 'conf', 'meetup', 'хакатон', 'форум', 'спб', 'онлайн', '2024', '2025'])
            
            if is_event:
                events.append({
                    "text": clean_text[:1000],
                    "url": link,
                    "source": source_config['name']
                })
                seen_links.add(link)

        return events[:10]

    def get_events(self, db_sources: list, keywords: list = None):
        all_events = []
        logger.info(f"🔄 Запуск парсера. Источников: {len(db_sources)}")
        
        for source in db_sources:
            try:
                soup = self._get_soup(source['url'])
                if soup:
                    events = self._heuristic_parse(soup, source, keywords)
                    logger.info(f"✅ {source['name']}: найдено {len(events)}")
                    all_events.extend(events)
                else:
                    logger.warning(f"⚠️ {source['name']}: нет ответа")
            except Exception as e:
                logger.error(f"❌ Ошибка обработки {source['name']}: {e}")
            time.sleep(1.5)
            
        return all_events