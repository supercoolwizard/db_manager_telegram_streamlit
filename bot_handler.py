import telebot
import os
import re
import pexpect
from sqlite_handler import SQLViewer
from bot_keyboard_handler import KeyboardMaster


class BotHandler:
    def __init__(self, api_token, admin_password, mongosh_allowed_commands):
        self.keyboard = None
        self.bot = telebot.TeleBot(api_token)
        self.admin_password = admin_password
        self.global_status = None
        self.mongosh_sessions = {}
        self.setup_keyboard()
        self.mongosh_allowed_commands = mongosh_allowed_commands

    def user_handler(self, message):
        self.global_status = 'user'
        self.bot.send_message(message.chat.id, "User mode selected.")

    def admin_handler(self, message):
        """Handle admin password input."""
        self.global_status = 'admin'
        self.bot.send_message(message.chat.id, "Admin mode selected.")

    def list_databases_mongodb(self, message):
        self.bot.send_message(message.chat.id, "Enter mongosh command or type $$back to exit:")
        if self.global_status == 'admin':
            self.bot.register_next_step_handler(message, lambda m: self.send_mongosh_command(m))
        else:
            self.bot.register_next_step_handler(message, lambda m: self.send_mongosh_command(m, simplified=True))

    def start_mongosh_session(self, chat_id):
        if chat_id not in self.mongosh_sessions:
            self.mongosh_sessions[chat_id] = pexpect.spawn('mongosh', encoding='utf-8')
            self.mongosh_sessions[chat_id].expect('>')  # Wait for the prompt

    def send_mongosh_command(self, message, simplified=False):
        """Send mongosh commands and return output."""
        chat_id = message.chat.id
        if message.text == "$$back":
            self.clean_exit_mongosh(chat_id)
            self.go_back_to_user_or_admin(message)
            return

        self.start_mongosh_session(chat_id)
        session = self.mongosh_sessions[chat_id]

        # Handle simplified user commands
        if simplified and not self.is_command_allowed_for_user(message.text):
            self.bot.send_message(chat_id, "Only read-only commands are allowed (e.g., show dbs).")
            self.request_next_mongosh_command(message, simplified)
            return

        session.sendline(message.text)
        session.expect('>')  # Wait for the prompt

        output = self.clean_output(session.before)

        # Split the output into chunks if it exceeds Telegram's message limit
        max_message_length = 4096
        for i in range(0, len(output), max_message_length):
            self.bot.send_message(chat_id, output[i:i + max_message_length])

        self.request_next_mongosh_command(message, simplified)

    def clean_exit_mongosh(self, chat_id):
        if chat_id in self.mongosh_sessions:
            session = self.mongosh_sessions[chat_id]
            session.sendline('exit')
            session.close()
            del self.mongosh_sessions[chat_id]

    def clean_output(self, output):
        """Remove escape characters and format output."""
        cleaned_output = re.sub(r'\x1B[@-_][0-?]*[ -/]*[@-~]', '', output)
        cleaned_output_lines = cleaned_output.splitlines()
        if cleaned_output_lines:
            cleaned_output_lines[-1] += ' >'
        return '\n'.join(cleaned_output_lines)

    def is_command_allowed_for_user(self, command):
        allowed_commands = self.mongosh_allowed_commands

        return any(command.startswith(cmd) for cmd in allowed_commands)

    def request_next_mongosh_command(self, message, simplified):
        self.bot.send_message(message.chat.id, "Enter another mongosh command or type $$back to exit:")
        next_step = lambda m: self.send_mongosh_command(m, simplified=simplified)
        self.bot.register_next_step_handler(message, next_step)

    def list_databases_sqlite(self, message):
        dbs_list = os.listdir("SQLite_databases")
        dbs_list_str = '\n'.join(dbs_list)
        self.bot.send_message(message.chat.id, f"Available databases:\n{dbs_list_str}")
        self.bot.send_message(message.chat.id, "Enter the database name (or type $$back):")
        self.bot.register_next_step_handler(message, self.process_database_choice)

    def process_database_choice(self, message):
        db_name = message.text
        if db_name == "$$back":
            self.go_back_to_user_or_admin(message)
        elif db_name in os.listdir("SQLite_databases"):
            self.handle_db_choice(message, db_name)
        else:
            self.bot.send_message(message.chat.id, "Invalid database name.")
            self.bot.register_next_step_handler(message, self.process_database_choice)

    def handle_db_choice(self, message, db_name):
        sv = SQLViewer(f"SQLite_databases/{db_name}")
        tables_in_db = sv.simple_view("SELECT name FROM sqlite_master WHERE type='table';")
        tables_str = '\n'.join([item[0] for item in tables_in_db])
        self.bot.send_message(message.chat.id, f"{db_name} has tables:\n{tables_str}")
        self.bot.send_message(message.chat.id, "Enter SQL query (or type $$back):")
        next_step = lambda m: self.process_query(m, db_name)
        self.bot.register_next_step_handler(message, next_step)

    def process_query(self, message, db_name):
        query = message.text
        if query == "$$back":
            self.list_databases_sqlite(message)
        else:
            sv = SQLViewer(f"SQLite_databases/{db_name}")
            self.execute_sql_query(sv, message, query, db_name)

    def execute_sql_query(self, sv, message, query, db_name):
        query_lower = query.strip().lower()
        if query_lower.startswith(("insert", "update", "delete", "drop", "create", "alter")):
            if self.global_status=='admin':
                # Process modification queries (INSERT, UPDATE, DELETE, DROP, CREATE, ALTER)
                try:
                    sv.executor(message.text)
                    self.bot.send_message(message.chat.id, "Query processed successfully.")
                except Exception as e:
                    self.bot.send_message(message.chat.id, f"Error processing query: {str(e)}")
            else:
                self.bot.send_message(message.chat.id, "Modification queries are not allowed.")
        else:
            try:
                csv_file = sv.export_query_to_csv(query)
                self.bot.send_document(message.chat.id, csv_file, visible_file_name="query_result.csv")
            except Exception as e:
                self.bot.send_message(message.chat.id, f"Error: {str(e)}")
        self.bot.send_message(message.chat.id, "Enter another query or type $$back.")
        self.bot.register_next_step_handler(message, lambda m: self.process_query(m, db_name))

    def go_back_to_user_or_admin(self, message):
        if self.global_status == 'user':
            self.user_handler(message)
        elif self.global_status == 'admin':
            self.admin_handler(message)

    def setup_keyboard(self):
        initial_buttons = [
            ("Continue as User", self.user_handler, [
                ("Choose SQLite Database", self.list_databases_sqlite, None, False, None),
                ("Enter mongosh Command Line", self.list_databases_mongodb, None, False, None)
            ], False, None),
            ("Continue as Admin", self.admin_handler, [
                ("Choose SQLite Database", self.list_databases_sqlite, None, False, None),
                ("Enter mongosh Command Line", self.list_databases_mongodb, None, False, None)
            ], True, self.admin_password)
        ]

        keyboard = KeyboardMaster(
            bot=self.bot,
            command='start',
            initial_buttons=initial_buttons,
        )
        keyboard.setup_button_handler()

    def run(self):
        self.bot.polling()
