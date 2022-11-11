class ServiceError(Exception):
    """Ошибка отсутствия доступа по заданному эндпойнту."""
    def __init__(self, *args):
        super().__init__(*args)
        self.msg = args[1] if args else None

    def __str__(self):
        return f'{self.msg}'


class EndpointError(Exception):
    """Ошибка, если эндпойнт не корректен."""
    def __init__(self, *args):
        super().__init__(*args)
        self.status_code = args[0] if args else None
        self.url = args[1] if args else None

    def __str__(self):
        return f'Эндпоинт {self.url} недоступен. Код ответа API: {self.status_code}'


class MessageSendingError(Exception):
    """Ошибка отправки сообщения."""
    def __init__(self, *args):
        super().__init__(*args)
        self.err = args[0] if args else None
        self.msg = args[1] if args else None

    def __str__(self):
        return f'{self.err}, {self.msg}'


class TokensError(Exception):
    """Ошибка, если есть пустые глобальные переменные."""

    def __str__(self):
        return f'Отсутствует обязательная переменная окружения.'


class DataTypeError(TypeError,KeyError):
    """Ошибка, если тип данных не dict."""
    def __init__(self, *args):
        super().__init__(*args)
        self.type = args[0] if args else None
        self.type_dop = args[1] if args else None

    def __str__(self):
        return f'Неверный тип данных {self.type}, вместо {self.type_dop}'


class ResponseFormatError(Exception):
    """Ошибка, если формат response не json."""
    def __init__(self, *args):
        super().__init__(*args)
        self.err = args[0] if args else None

    def __str__(self):
        return f'Формат не json {self.err}'