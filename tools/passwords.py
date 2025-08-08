from langchain.tools import tool

@tool
def check_password(password: str):
    from _password_utilities import analyze_password
    return analyze_password(password)
