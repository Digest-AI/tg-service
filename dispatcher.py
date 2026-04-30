from aiogram import Dispatcher

from handlers import help, start, subscription
from middlewares.check_linked import CheckLinkedMiddleware

dp = Dispatcher()

dp.message.outer_middleware(CheckLinkedMiddleware())

dp.include_router(start.router)
dp.include_router(subscription.router)
dp.include_router(help.router)
