from LLMs import get_llm_client


if __name__ == '__main__':
    prompt = "Привет, ты кто?"
    client = get_llm_client("gigachat")
    print(client.chat(prompt))

    client = get_llm_client("google")
    print(client.chat(prompt))

    client = get_llm_client("groq")
    print(client.chat(prompt))

    # client = get_llm_client("openai")
    # print(client.chat("Hello, who are you?"))
