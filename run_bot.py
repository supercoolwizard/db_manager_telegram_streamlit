from bot_handler import BotHandler
from settings_reader import read_settings

API_TOKEN = read_settings('settings.txt')['TELEGRAM_API_TOKEN']
ADMIN_PASSWORD = read_settings('settings.txt')['ADMIN_PASSWORD']
MONGOSH_ALLOWED_COMMANDS = read_settings('settings.txt')['MONGOSH_ALLOWED_COMMANDS']


def run_bot():
    handler = BotHandler(api_token=API_TOKEN, admin_password=ADMIN_PASSWORD,
                         mongosh_allowed_commands=MONGOSH_ALLOWED_COMMANDS)
    handler.run()


if __name__ == '__main__':
    run_bot()
