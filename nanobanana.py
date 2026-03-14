import aiohttp
from typing import Optional

class PollinationsAPI:
    """Клиент для Pollinations AI — работает без ключей и заморочек"""
    
    def __init__(self):
        self.base_url = "https://image.pollinations.ai/prompt"
    
    async def generate_image(self, prompt: str) -> Optional[bytes]:
        """
        Генерирует картинку по промпту через простой GET-запрос
        """
        # Заменяем пробелы на %20 для URL
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"{self.base_url}/{encoded_prompt}"
        
        print(f"🎨 Запрос к Pollinations: {prompt[:50]}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as resp:
                    if resp.status != 200:
                        print(f"❌ Ошибка HTTP: {resp.status}")
                        return None
                    
                    image_bytes = await resp.read()
                    print(f"✅ Готово! Размер: {len(image_bytes)} байт")
                    return image_bytes
                    
        except Exception as e:
            print(f"❌ Ошибка генерации: {e}")
            return None