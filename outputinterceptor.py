import sys

class StdOutMirror:
    def __init__(self, bot_instance, original_stdout):
        self.bot = bot_instance
        self.terminal = original_stdout

    def write(self, message):
        self.terminal.write(message)
        
        clean_msg = message.strip()
        if clean_msg:
            self.bot.debouncer(clean_msg)

    def flush(self):
        self.terminal.flush()