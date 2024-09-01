from ..interfaces.notification_channel import INotificationChannel
from ..properties.properties import TelegramNotificationProperties
import telegram
import asyncio


class TelegramNotificationChannel(INotificationChannel):

    def __init__(self, properties:TelegramNotificationProperties) -> None:
        self._chat_id = properties.chat_id
        self._token = properties.token
        self._bot = telegram.Bot(self._token)

    async def async_send_message(self, title:str,message:str):
        
        async with self._bot:
            await self._bot.send_message(text=f'{title}\n{message}',chat_id=self._chat_id)

    def send_message(self, title: str, message: str):
        asyncio.run(self.async_send_message(title,message))