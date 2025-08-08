from langchain.tools import tool

@tool
def search_web(query: str) -> str:
    """Осуществляет поиск в Google"""
    from internet_search import InternetSearchTool
    searcher = InternetSearchTool()
    return searcher.search(query)
