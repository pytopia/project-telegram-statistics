import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Union

import arabic_reshaper
import demoji
from bidi.algorithm import get_display
from hazm import Normalizer, sent_tokenize, word_tokenize
from loguru import logger
from src.data import DATA_DIR
from wordcloud import WordCloud


class ChatStatistics:
    """Generates chat statistics from a telegram chat json file
    """

    def __init__(self, chat_json: Union[str, Path]):
        """
        :param chat_json: path to telegram export json file
        """
        # load chat data
        logger.info(f"Loading chat data from {chat_json}")
        with open(chat_json) as f:
            self.chat_data = json.load(f)

        self.normalizer = Normalizer()

        # load stopwords
        logger.info(f"Loading stopwords from {DATA_DIR / 'stopwords.txt'}")
        stop_words = open(DATA_DIR / 'stopwords.txt').readlines()
        stop_words = map(str.strip, stop_words)
        self.stop_words = set(map(self.normalizer.normalize, stop_words))

    @staticmethod
    def rebuild_msg(sub_messages):
        msg_text = ''
        for sub_msg in sub_messages:
            if isinstance(sub_msg, str):
                msg_text += sub_msg
            elif 'text' in sub_msg:
                msg_text += sub_msg['text']

        return msg_text

    def msg_has_question(self, msg):
        """Checks if a message has a question

        :param msg: message to check
        """
        if not isinstance(msg['text'], str):
            msg['text'] = self.rebuild_msg(msg['text'])

        sentences = sent_tokenize(msg['text'])
        for sentence in sentences:
            if ('?' not in sentence) and ('؟' not in sentence):
                continue

            return True

    def get_top_users(self, top_n: int = 10) -> dict:
        """Gets the top n users from the chat.

        :param top_n: number of users to get, default to 10
        :return: dict of top users
        """
        # check messages for questions
        is_question = defaultdict(bool)
        for msg in self.chat_data['messages']:
            if not isinstance(msg['text'], str):
                msg['text'] = self.rebuild_msg(msg['text'])

            sentences = sent_tokenize(msg['text'])
            for sentence in sentences:
                if ('?' not in sentence) and ('؟' not in sentence):
                    continue
                is_question[msg['id']] = True
                break

        # get top users based on replying to questions from others
        logger.info("Getting top users...")
        users = []
        for msg in self.chat_data['messages']:
            if not msg.get('reply_to_message_id'):
                continue
            if is_question[msg['reply_to_message_id']] is False:
                continue

            users.append(msg['from'])

        return dict(Counter(users).most_common(top_n))

    def remove_stopwords(self, text):
        """Removes stop-words from the text.

        :param text: Text that may contain stop-words.
        """
        tokens = word_tokenize(self.normalizer.normalize(text))
        tokens = list(filter(lambda item: item not in self.stop_words, tokens))
        return ' '.join(tokens)

    def de_emojify(self, text):
        """Removes emojis and some special characters from the text.

        :param text: Text that contains emoji
        """
        regrex_pattern = re.compile(pattern="[\u2069\u2066]+", flags=re.UNICODE)
        text = regrex_pattern.sub('', text)
        return demoji.replace(text, " ")

    def generate_word_cloud(
        self,
        output_dir: Union[str, Path],
        width: int = 800, height: int = 600,
        max_font_size: int = 250,
        background_color: str = 'white',
    ):
        """Generates a word cloud from the chat data

        :param output_dir: path to output directory for word cloud image
        """
        logger.info("Loading text content...")
        text_content = ''
        messages = iter(self.chat_data['messages'])
        for message in messages:
            msg = message['text']
            if isinstance(msg, list):
                for sub_msg in msg:
                    if isinstance(sub_msg, str):
                        text_content += f" {self.remove_stopwords(sub_msg)}"
                    elif isinstance(sub_msg, dict) and sub_msg['type'] in {
                        'text_link', 'bold', 'italic',
                        'hashtag', 'mention', 'pre'
                    }:
                        text_ = self.remove_stopwords(sub_msg['text'])
                        text_content += f" {text_}"
            else:
                text_content += f" {self.remove_stopwords(msg)}"

        # reshape for final word cloud
        text_content = arabic_reshaper.reshape(self.de_emojify(text_content))
        text_content = get_display(text_content)

        logger.info("Generating word cloud...")
        # generate word cloud
        wordcloud = WordCloud(
            width=1200, height=1200,
            font_path=str(DATA_DIR / 'Vazir.ttf'),
            background_color=background_color,
            max_font_size=250
        ).generate(text_content)

        logger.info(f"Saving word cloud to {output_dir}")
        wordcloud.to_file(str(Path(output_dir) / 'wordcloud.png'))


if __name__ == "__main__":
    chat_stats = ChatStatistics(chat_json=DATA_DIR / 'online.json')
    top_users = chat_stats.get_top_users(top_n=10)
    print(top_users)

    chat_stats.generate_word_cloud(output_dir=DATA_DIR)
    print('Done!')
