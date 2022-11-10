import os
import logging
import time

import requests
import telegram
from dotenv import load_dotenv

from exceptions import MessageSendingError, EndpointError, ResponseFormatError, ServiceError, TokensError, DataTypeError

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
homework_status_0 = 'start'

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат, определяемый переменной окружения TELEGRAM_CHAT_ID."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.info('Сообщение отправлено')
    except Exception as err:
        raise MessageSendingError(err, message)


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса. """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    all_params = dict(url=ENDPOINT, headers=HEADERS, params=params)
    try:
        homework_statuses = requests.get(**all_params)
        ENDPOINT_status_code = homework_statuses.status_code
    except requests.exceptions.RequestException as err:
        logging.error(f'Сбой в работе программы: '
                      f'Эндпоинт {ENDPOINT} недоступен. Код ответа API: {ENDPOINT_status_code}')
        raise telegram.TelegramError(f'{err}, {ENDPOINT}, {HEADERS}, {params}')
    if ENDPOINT_status_code != 200:
        raise EndpointError(ENDPOINT_status_code, **all_params)
    try:
        return homework_statuses.json()
    except Exception as err:
        raise ResponseFormatError(err)


def check_response(response):
    """Проверяет ответ API на корректность."""
    if response['homeworks']:
        return response['homeworks'][0]
    else:
        logging.error('Отсутствуют ожидаемые ключи в ответе API')
        raise ServiceError('Список пустой')


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус этой работы."""
    if not isinstance(homework, dict):
        logging.error('Неверный тип данных домашней работы')
        raise DataTypeError(type(homework))
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in dict.keys(HOMEWORK_STATUSES):
        logging.debug('Недокументированный статус домашней работы')
        raise NameError(f'{homework_status}')
    elif homework_status in dict.keys(HOMEWORK_STATUSES):
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения, которые необходимы для работы программы."""
    tokens = PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    names = 'PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID'
    for token, val in enumerate(tokens):
        if val is None:
            logging.critical(
                f'Отсутствует обязательная переменная окружения:{(names[token])} Программа принудительно остановлена.')
            Flag = False
        elif val is not None:
            Flag = True
    return Flag


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        raise TokensError()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)
            current_timestamp = response.get('current_date')
        except IndexError:
            pass
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s, %(message)s, %(lineno)d, %(name)s',
        filemode='w',
        filename='program.log',
        level=logging.DEBUG,
    )
    main()
