import threading
import telebot
import subprocess
from threading import Timer
import os
from dotenv import load_dotenv
load_dotenv()

class RemoteLogBot:

    def __init__(self, interval=2.0):

        self.bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))
        self.admin_id = int(os.getenv("ADMIN_USER"))
        self.interval = interval
        self.buffer = []
        self.timer = None

        self.polling_thread = threading.Thread(target=self._start_polling, daemon=True)
        self.polling_thread.start()

    def debouncer(self, text):

        self.buffer.append(text)
        
        if self.timer:
            self.timer.cancel()
        
        self.timer = Timer(self.interval, self.send_log)
        self.timer.start()

    def send_log(self):

        if self.buffer:

            current_log = "\n".join(self.buffer)
            if len(current_log) > 4000:
                current_log = current_log[:4000] + "\n... (Too long output)" 
                
            try:

                self.bot.send_message(self.admin_id, f"**New Log:**\n```\n{current_log}\n```", parse_mode='Markdown')
                self.buffer = []

            except telebot.apihelper.ApiTelegramError as e:

                if e.error_code == 403 or e.error_code == 400:
                    print(" 🟡 Connection not established!")

                else:
                    print(f"🔴 Error sending log via bot: {e}")
            
            self.timer = None
        
    def _start_polling(self):

        @self.bot.message_handler(func=lambda m: m.chat.id == self.admin_id)
        def handle_command(message):
            command = message.text
            self.bot.send_chat_action(message.chat.id, 'typing')
            try:

                result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
                
                if not result:
                    result = "OK, no output."
                    
                if len(result) > 4000:
                    result = result[:4000] + "\n... (Too long output)"
                    
                self.bot.reply_to(message, f"```\n{result}\n```", parse_mode='Markdown')
    
            except subprocess.CalledProcessError as e:
                self.bot.reply_to(message, f"**Error in terminal execution:**\n```\n{e.output}\n```", parse_mode='Markdown')
            except Exception as e:
                self.bot.reply_to(message, f"**Server error:** {str(e)}")
                self.bot.infinity_polling()
        
        @self.bot.message_handler(func=lambda message: message.chat.id != self.admin_id)
        def negado(message):
            self.bot.reply_to(message, "Access denied. Your ID has been registered.")
            print(f"🔴 Attempted break-in: ID {message.chat.id}")
        
        self.bot.infinity_polling(skip_pending=True)             
