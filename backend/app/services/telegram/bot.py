"""
Telegram бот для управления панелью (опциональный)
"""
import asyncio
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from app.core.config import settings
from sqlalchemy import select
from app.db.base import async_session_maker
from app.models.user import User
from app.models.node import Node


class TelegramBot:
    """Telegram бот для управления панелью"""
    
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.admin_ids = settings.TELEGRAM_ADMIN_IDS
        self.enabled = bool(self.token)
        self.app: Optional[Application] = None
    
    def is_admin(self, user_id: int) -> bool:
        """Проверка что пользователь является админом"""
        return user_id in self.admin_ids
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user = update.effective_user
        
        if not self.is_admin(user.id):
            await update.message.reply_text(
                "⛔ Доступ запрещён. Этот бот только для администраторов."
            )
            return
        
        keyboard = [
            [
                InlineKeyboardButton("👥 Пользователи", callback_data="users"),
                InlineKeyboardButton("🖥 Ноды", callback_data="nodes")
            ],
            [
                InlineKeyboardButton("📊 Статистика", callback_data="stats"),
                InlineKeyboardButton("ℹ️ Справка", callback_data="help")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"👋 Добро пожаловать, {user.first_name}!\n\n"
            f"🎛 Панель управления Xray\n\n"
            f"Выберите действие:",
            reply_markup=reply_markup
        )
    
    async def users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /users - список пользователей"""
        query = update.callback_query
        
        if query:
            await query.answer()
            message = query.message
        else:
            message = update.message
        
        if not self.is_admin(update.effective_user.id):
            await message.reply_text("⛔ Доступ запрещён")
            return
        
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).limit(10)
            )
            users = result.scalars().all()
            
            if not users:
                await message.reply_text("📭 Пользователи не найдены")
                return
            
            text = "👥 Пользователи:\n\n"
            for user in users:
                status_emoji = {
                    "ACTIVE": "✅",
                    "DISABLED": "⛔",
                    "LIMITED": "⚠️",
                    "EXPIRED": "❌"
                }.get(user.status, "❓")
                
                traffic_gb = user.traffic_used_bytes / 1024 / 1024 / 1024
                text += f"{status_emoji} {user.username}\n"
                text += f"   Трафик: {traffic_gb:.2f} GB\n\n"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data="users")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.reply_text(text, reply_markup=reply_markup)
    
    async def nodes_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /nodes - список нод"""
        query = update.callback_query
        
        if query:
            await query.answer()
            message = query.message
        else:
            message = update.message
        
        if not self.is_admin(update.effective_user.id):
            await message.reply_text("⛔ Доступ запрещён")
            return
        
        async with async_session_maker() as session:
            result = await session.execute(select(Node))
            nodes = result.scalars().all()
            
            if not nodes:
                await message.reply_text("📭 Ноды не найдены")
                return
            
            text = "🖥 Ноды:\n\n"
            for node in nodes:
                status_emoji = "✅" if node.is_connected else "❌"
                xray_emoji = "🟢" if node.xray_running else "🔴"
                
                text += f"{status_emoji} {node.name}\n"
                text += f"   Адрес: {node.address}:{node.api_port}\n"
                text += f"   Xray: {xray_emoji}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data="nodes")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.reply_text(text, reply_markup=reply_markup)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /stats - статистика"""
        query = update.callback_query
        
        if query:
            await query.answer()
            message = query.message
        else:
            message = update.message
        
        if not self.is_admin(update.effective_user.id):
            await message.reply_text("⛔ Доступ запрещён")
            return
        
        async with async_session_maker() as session:
            # Подсчёт пользователей
            result = await session.execute(select(User))
            users = result.scalars().all()
            
            total_users = len(users)
            active_users = len([u for u in users if u.status == "ACTIVE"])
            
            # Подсчёт нод
            result = await session.execute(select(Node))
            nodes = result.scalars().all()
            
            total_nodes = len(nodes)
            active_nodes = len([n for n in nodes if n.is_connected])
            
            # Подсчёт трафика
            total_traffic = sum(u.traffic_used_bytes for u in users)
            total_traffic_gb = total_traffic / 1024 / 1024 / 1024
            
            text = "📊 Статистика:\n\n"
            text += f"👥 Пользователи: {active_users}/{total_users}\n"
            text += f"🖥 Ноды: {active_nodes}/{total_nodes}\n"
            text += f"📶 Трафик: {total_traffic_gb:.2f} GB\n"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data="stats")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.reply_text(text, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help - справка"""
        query = update.callback_query
        
        if query:
            await query.answer()
            message = query.message
        else:
            message = update.message
        
        text = (
            "ℹ️ Справка по командам:\n\n"
            "/start - Главное меню\n"
            "/users - Список пользователей\n"
            "/nodes - Список нод\n"
            "/stats - Статистика\n"
            "/help - Эта справка\n"
        )
        
        await message.reply_text(text)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на кнопки"""
        query = update.callback_query
        
        callbacks = {
            "users": self.users_command,
            "nodes": self.nodes_command,
            "stats": self.stats_command,
            "help": self.help_command
        }
        
        handler = callbacks.get(query.data)
        if handler:
            await handler(update, context)
    
    async def setup(self):
        """Настройка бота"""
        if not self.enabled:
            return None
        
        self.app = Application.builder().token(self.token).build()
        
        # Регистрация обработчиков
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("users", self.users_command))
        self.app.add_handler(CommandHandler("nodes", self.nodes_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
        
        return self.app
    
    async def start_polling(self):
        """Запуск бота"""
        if not self.enabled:
            print("Telegram бот отключён (TELEGRAM_BOT_TOKEN не указан)")
            return
        
        await self.setup()
        print(f"Telegram бот запущен")
        await self.app.run_polling()
    
    async def stop(self):
        """Остановка бота"""
        if self.app:
            await self.app.stop()


# Глобальный экземпляр бота
telegram_bot = TelegramBot()


async def send_notification(message: str, user_id: Optional[int] = None):
    """Отправка уведомления в Telegram"""
    if not telegram_bot.enabled:
        return
    
    try:
        if user_id:
            recipients = [user_id]
        else:
            recipients = telegram_bot.admin_ids
        
        if telegram_bot.app:
            for recipient in recipients:
                await telegram_bot.app.bot.send_message(
                    chat_id=recipient,
                    text=message,
                    parse_mode="HTML"
                )
    except Exception as e:
        print(f"Ошибка отправки Telegram уведомления: {e}")
