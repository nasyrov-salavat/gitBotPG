from aiogram.utils import executor
import handlers.client as client
import handlers.other as other
from handlers.client import dp, on_startup




client.register_handlers_client(dp)
client.register_handlers_callback(dp)
other.register_handlers_other(dp)

executor.start_polling(dp, skip_updates=True, on_startup=on_startup)