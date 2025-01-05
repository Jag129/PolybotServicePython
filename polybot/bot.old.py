import telebot
from loguru import logger
import os
import time
from telebot.types import InputFile
#from polybot.img_proc import Img


class Bot:

    def __init__(self, token, bot_app_url):
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        self.telegram_bot_client.set_webhook(url=f'{bot_app_url}/{token}/', timeout=60)

        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)

    def is_current_msg_photo(self, msg):
        return 'photo' in msg

    def download_user_photo(self, msg):
        """
        Downloads the photos that sent to the Bot to `photos` directory (should be existed)
        :return:
        """
        if not self.is_current_msg_photo(msg):
            raise RuntimeError(f'Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        return file_info.file_path

    def send_photo(self, chat_id, img_path):
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(
            chat_id,
            InputFile(img_path)
        )

    def handle_message(self, msg):
        """Bot Main message handler"""
        logger.info(f'Incoming message: {msg}')
        chat_id = msg['chat']['id']

        # Check if it's a /start command
        if 'text' in msg and msg['text'] == '/start':
            self.User_Greeting(chat_id)
        elif 'text' in msg and msg['text'] == '/help':
            self.send_help_message(chat_id)
        else:
            self.send_text(chat_id, f'Your original message: {msg["text"]}')


    def User_Greeting(self, chat_id):
        """Greet user when they are sending a message"""
        greeting_message = "Hey, welcome to Jarvis!"  # Updated greeting message
        self.send_text(chat_id, greeting_message)

    def send_help_message(self, chat_id):
        """Send a help message with available commands"""
        help_text = """
    Available commands:
    /start - Start the bot
    /help - Show this help message
    /quote - Quote your message
    Send a photo - I'll process it for you
        """
        self.send_text(chat_id, help_text)


class QuoteBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')
        chat_id = msg['chat']['id']
        #return 'OK', 200
        # Check if it's a /start command
        if 'text' in msg and msg['text'] == '/start':
            self.User_Greeting(chat_id)
        elif 'רשל' in msg.get('text', ''):
            self.send_text(chat_id, 'אותך אני הכי אוהב!')
        elif 'יוני' in msg.get('text', ''):
            self.send_text(chat_id, 'יוני יא תותח תחת')
        elif 'ישי' in msg.get('text', ''):
            self.send_text(chat_id, 'איזה באסה שאני לא ישי')
        elif 'שיראל' in msg.get('text', ''):
            self.send_text(chat_id, 'בהצלחה בלימודים, תעשי חיל!')
        elif 'אדיר' in msg.get('text', ''):
            self.send_text(chat_id, 'תתחדש על האייפון אח שלי')
        elif msg.get("text") != 'Please don\'t quote me':
            # Default behavior for quoting messages
            self.send_text_with_quote(chat_id, msg["text"], quoted_msg_id=msg["message_id"])
        else:
            # Handle any other text without quoting
            self.send_text(chat_id, f'Your original message: {msg["text"]}')


class ImageProcessingBot(Bot):
    pass

#img = /home/jess/Downloads/image.png
