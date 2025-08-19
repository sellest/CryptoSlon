def analyze_password(password: str) -> str:
    """
    Оценивает надежность пароля по методологии команды dropbox. Подробности - https://pypi.org/project/zxcvbn/
    :param password: пароль для оценки
    :return: возвращает отчет о надежности пароля в формате текста, готовый к инъекции в LLM
    """
    import zxcvbn

    result = zxcvbn.zxcvbn(password)
    score_text = {
        0: "Очень слабый",
        1: "Слабый",
        2: "Средний",
        3: "Хороший",
        4: "Очень хороший"
    }

    suggestions = result["feedback"]["suggestions"]
    formatted_suggestions = "Нет конкретных советов"
    if suggestions:
        formatted_suggestions = "- " + "\n- ".join(suggestions)

    return (
        f"Пароль: {password}\n"
        f"Оценка надёжности: {score_text.get(result['score'], 'Неизвестно')} (score={result['score']})\n"
        f"Время взлома online (без ограничений): {result['crack_times_display']['online_no_throttling_10_per_second']}\n"
        f"Время взлома offline (hash): {result['crack_times_display']['offline_fast_hashing_1e10_per_second']}\n"
        f"Советы по улучшению:\n{formatted_suggestions}"
    )

def is_password_pwned(password: str) -> bool:
    """Проверяет пароль в базе утечек https://haveibeenpwned.com/"""
    import hashlib
    import requests
    sha1 = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix = sha1[:5]
    suffix = sha1[5:]
    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    response = requests.get(url)
    hashes = (line.split(":")[0] for line in response.text.splitlines())
    return suffix in hashes

def direct_password_checks(password: str) -> list[str]:
    import re
    violations = []
    if len(password) < 8:
        violations.append("Длина пароля должна быть не меньше 8 символов")
    if not re.search(r"[A-Z]", password):
        violations.append("Пароль должен содержать хотя бы одну заглавную букву.")
    if not re.search(r"\d", password):
        violations.append("Пароль должен содержать хотя бы одну цифру.")
    if not re.search(r"[^\w\s]", password):
        violations.append("Пароль должен содержать хотя бы один спецсимвол.")

    return violations

def generate_strong_password(length: int = 16) -> str:
    """Генерирует надёжный пароль, содержащий заглавные, строчные буквы, цифры и спецсимволы."""
    import random
    import string

    if length < 12:
        raise ValueError("Минимальная длина безопасного пароля — 12 символов.")

    # Гарантированное включение всех групп
    upper = random.choice(string.ascii_uppercase)
    lower = random.choice(string.ascii_lowercase)
    digit = random.choice(string.digits)
    symbol = random.choice("!@#$%^&*()-_=+[]{}<>?")

    # Остальные символы случайно
    remaining_length = length - 4
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}<>?"
    remaining = random.choices(all_chars, k=remaining_length)

    # Соберём и перемешаем
    password_chars = list(upper + lower + digit + symbol + "".join(remaining))
    random.shuffle(password_chars)

    return "".join(password_chars)
