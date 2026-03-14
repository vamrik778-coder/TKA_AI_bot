import aiohttp
import base64
import json
from typing import Optional

class NanoBananaAPI:
    """Клиент для Nano Banana Pro (felo.ai)"""
    
    def __init__(self):
        self.base_url = "https://api.felo.ai/v1"
        self.session = None
    
    async def _get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def generate_image(self, prompt: str) -> Optional[bytes]:
        """
        Генерирует картинку по промпту
        Возвращает байты изображения или None
        """
        try:
            session = await self._get_session()
            
            headers = {
                "Authorization": "Bearer free",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": prompt,
                "model": "gemini-3-pro-image-preview",
                "width": 1024,
                "height": 1024,
                "num_images": 1
            }
            
            print(f"🎨 Отправляю запрос: {prompt[:50]}...")
            
            async with session.post(
                f"{self.base_url}/gemini-image-gen",
                headers=headers,
                json=payload,
                timeout=30
            ) as resp:
                
                if resp.status != 200:
                    error = await resp.text()
                    print(f"❌ Ошибка API: {resp.status} - {error[:100]}")
                    return None
                
                data = await resp.json()
                
                if "images" in data and data["images"]:
                    img_base64 = data["images"][0]
                    img_bytes = base64.b64decode(img_base64)
                    print(f"✅ Готово! Размер: {len(img_bytes)} байт")
                    return img_bytes
                elif "image" in data:
                    img_base64 = data["image"]
                    img_bytes = base64.b64decode(img_base64)
                    print(f"✅ Готово! Размер: {len(img_bytes)} байт")
                    return img_bytes
                else:
                    print(f"❌ Странный ответ: {data.keys()}")
                    return None
                    
        except Exception as e:
            print(f"❌ Ошибка генерации: {e}")
            return None
    
    async def close(self):
        """Закрываем сессию"""
        if self.session:
            await self.session.close()