import telebot
from loguru import logger
import os
import time
from telebot.types import InputFile
from polybot.img_proc import Img


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
        self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')


class QuoteBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if msg["text"] != 'Please don\'t quote me':
            self.send_text_with_quote(msg['chat']['id'], msg["text"], quoted_msg_id=msg["message_id"])


class ImageProcessingBot(Bot):
    last_caption_concat = False
    first_img_path = "/"

    def greet_user(self, msg):
        logger.info(f'Incoming message: {msg}')
        if 'text' in msg:
            msg_text = msg['text'].lower()
            if 'hi' in msg_text or 'hello' in msg_text:
                self.send_text(msg['chat']['id'], "Hello from your image processing bot !")
                self.send_text(msg['chat']['id'],
                               """
                                  Upon incoming photo messages, I will download the photos and process them according to the caption field provided with the message.\nI will then send the processed image back to you, the user !
                                    """)
                return True
        return False

    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')
        # Ensure the receipt of photo messages
        try:
            # Attempt greeting the user, in case of contact
            user_greeted = self.greet_user(msg)
            if not user_greeted:
                # Handle image processing
                photo_path = self.download_user_photo(msg)
                logger.info(f'Downloaded user photo to: {photo_path}')
                photo_as_img = Img(photo_path)

                function_mapping = {"blur": photo_as_img.blur,
                                    "contour": photo_as_img.contour,
                                    #"rotate": photo_as_img.rotate,
                                    "segment": photo_as_img.segment,
                                    "salt and pepper": photo_as_img.salt_n_pepper,
                                    }
                # Specifically handle image concatenation or rotation
                if 'caption' in msg and ('concat' in msg['caption'].lower() or 'rotate' in msg['caption'].lower() ):
                    if msg['caption'].lower() == "concat":
                        logger.info(f'Applying the following filter on image(s): {msg["caption"].lower()}')
                        self.last_caption_concat = True
                        self.first_img_path = photo_path
                    else:
                        separated_caption = msg['caption'].lower().split(' ')
                        if separated_caption[0] == 'rotate':
                            if len(separated_caption) == 2:
                                photo_as_img.rotate(int(separated_caption[1]))
                            elif len(separated_caption) == 1:
                                photo_as_img.rotate()
                            else:
                                # Invalid number of arguments to the rotate method
                                raise RuntimeError("Received invalid number of rotations. Input doesn't match syntax.")
                            filtered_photo_path = photo_as_img.save_img()
                            self.send_photo(msg['chat']['id'], filtered_photo_path)
                else:
                    if self.last_caption_concat:
                        # This is the second image for concatenation
                        photo_as_img.concat(Img(self.first_img_path))
                        self.last_caption_concat = False
                    else:
                        # Requested filter is different from concat
                        logger.info(f'Applying the following filter on image(s): {msg["caption"].lower()}')
                        function_mapping[msg['caption'].lower()]()
                    # Save the filtered image and resend to user
                    filtered_photo_path = photo_as_img.save_img()
                    self.send_photo(msg['chat']['id'], filtered_photo_path)
        except KeyError as ke:
            logger.error(f'Encountered an error while trying to process the following message: {msg}\nError relates '
                         f'to the following data: {str(ke)}')
            self.send_text(msg['chat']['id'],
                           f'Error encountered while trying to activate unknown filter on image:\n{str(ke)}\n'
                           f'Please make sure your selected filter is in this list:\n{list(function_mapping.keys())}')
        except RuntimeError as re:
            logger.error(f'Encountered an error while trying to process the following message: {msg}\nError relates '
                         f'to the following data: {str(re)}')
            self.send_text(msg['chat']['id'], f'Error encountered while trying to process image:\n{str(re)}\n'
                                              f'Please make sure you added an image from your desktop...')
        except Exception as e:
            logger.error(f'Encountered an error while trying to process the following message: {msg}\nError relates '
                         f'to the following data: {str(e)}')
            self.send_text(msg['chat']['id'], 'General exception occurred. Please try again...')