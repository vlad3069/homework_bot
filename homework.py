import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (DataTypeError, EndpointError, MessageSendingError,
                        ResponseFormatError, ServiceError, TokensError)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в Telegram."""
    logging.debug('Начата отправка сообщения в Telegram')
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.info('Сообщение отправлено')
    except Exception as err:
        raise MessageSendingError(err, message)


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    all_params = dict(url=ENDPOINT, headers=HEADERS, params=params)
    logging.debug('Начат запрос к API')
    try:
        homework_statuses = requests.get(**all_params)
        ENDPOINT_status_code = homework_statuses.status_code
    except requests.exceptions.RequestException as err:
        raise telegram.TelegramError(f'{err}, {ENDPOINT}, {HEADERS}, {params}')
    if ENDPOINT_status_code != HTTPStatus.OK:
        raise EndpointError(ENDPOINT_status_code, **all_params)
    try:
        return homework_statuses.json()
    except Exception as err:
        raise ResponseFormatError(err)


def check_response(response):
    """Проверяет ответ API на корректность."""
    logging.debug('Начало проверки ответа API')
    if not isinstance(response, dict):
        raise DataTypeError(type(response), dict)
    if not ('homeworks' and 'current_date') in response:
        raise ServiceError('Список пустой')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise DataTypeError(type(homeworks), list)
    if homeworks:
        return homeworks[0]
    else:
        return homeworks


def parse_status(homework):
    """Извлекает из информации статус домашней работы."""
    if not isinstance(homework, dict):
        raise DataTypeError(type(homework), dict)
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if not homework_name:
        raise NameError(f'{homework_status}')
    if homework_status not in dict.keys(HOMEWORK_STATUSES):
        raise NameError(f'{homework_status}')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    logging.debug('Начало проверки токенов')
    tokens = PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    if all(tokens):
        return True
    else:
        TokensError()


def main():
    """Основная логика работы бота."""
    logging.debug('Запуск Telegram бота')
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    current_timestamp = 15000000
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework:
                message = parse_status(homework)
            else:
                logging.info('Домашек нет')
                break
            send_message(bot, message)
            current_timestamp = response.get('current_date')
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
