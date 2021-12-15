import argparse
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
from wordcloud import WordCloud

from src.data import DATA_DIR
from tqdm import tqdm


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
            if not msg.get('text'):
                continue

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
        wordcloud_image_path: Union[str, Path],
        generate_from_frequencies: bool = False,
        width: int = 800, height: int = 600,
        max_font_size: int = 250,
        background_color: str = 'white',
    ):
        """Generates a word cloud from the chat data

        :param wordcloud_image_path: path to output directory for word cloud image
        """
        logger.info("Loading text content...")
        text_content = ''
        for message in tqdm(self.chat_data['messages'], 'Processing messages...'):
            if not message.get('text'):
                continue

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

        wordcloud = WordCloud(
            width=width, height=height,
            font_path=str(DATA_DIR / 'Vazir.ttf'),
            background_color=background_color,
            max_font_size=max_font_size
        )

        if generate_from_frequencies:
            tokens = list(word_tokenize(self.normalizer.normalize(text_content)))
            top_n_words = dict(Counter(tokens).most_common(100))

            reshaped_tokens_count = defaultdict(int)
            for token, count in top_n_words.items():
                token = arabic_reshaper.reshape(self.de_emojify(token))
                token = get_display(token)
                reshaped_tokens_count[token] = reshaped_tokens_count.get(token, 0) + count

            logger.info("Generating word cloud...")
            wordcloud.generate_from_frequencies(top_n_words)
        else:
            text_content = arabic_reshaper.reshape(self.de_emojify(text_content))
            text_content = get_display(text_content)

            logger.info("Generating word cloud...")
            wordcloud.generate(text_content)

        logger.info(f"Saving word cloud to {wordcloud_image_path}")
        wordcloud.to_file(str(Path(wordcloud_image_path)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chat_json", help="Path to telegram export json file")
    parser.add_argument("--wordcloud_image_path", help="Path to output directory for graph image")
    parser.add_argument("--top_n", help="Number of top users to get", type=int, default=10)
    parser.add_argument("--generate_from_frequencies", action='store_true', help="Generate word cloud from frequencies")
    args = parser.parse_args()

    chat_stats = ChatStatistics(chat_json=args.chat_json)
    top_users = chat_stats.get_top_users(top_n=args.top_n)
    print(top_users)

    chat_stats.generate_word_cloud(
        wordcloud_image_path=args.wordcloud_image_path,
        generate_from_frequencies=args.generate_from_frequencies
    )
    print('Done!')
