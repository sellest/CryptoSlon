from langchain.tools import tool

@tool
def check_password(password: str):
    description = "Этот метод проверяет пароль на уязвимость"
    from _password_utilities import analyze_password
    return analyze_password(password)
