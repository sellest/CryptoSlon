# -*- coding: utf-8 -*-
"""
Утилита для просмотра коллекций ChromaDB
"""

from VectorDB.base_chroma_db import BaseChromaDB

def main():
    """Показать все коллекции в базе данных"""
    print("📚 КОЛЛЕКЦИИ CHROMADB")
    print("=" * 40)
    
    try:
        # Используем статический метод для получения всех коллекций
        collections = BaseChromaDB.list_all_collections("../chroma_db")
        
        if not collections:
            print("❌ Коллекции не найдены или база данных пуста")
            return
        
        print(f"Найдено коллекций: {len(collections)}\n")
        
        for i, collection in enumerate(collections, 1):
            print(f"{i}. Название: {collection['name']}")
            print(f"   ID: {collection['id']}")
            print(f"   Документов: {collection['total_documents']}")
            
            # Попробуем получить дополнительную информацию
            try:
                # Создаем экземпляр для получения подробной информации
                db = BaseChromaDB(collection['name'])
                info = db.get_collection_info()
                print(f"   Размерность эмбеддингов: {info['embedding_dimension']}")
                print(f"   Модель: {info['model_name']}")
            except Exception as e:
                print(f"   ⚠️  Не удалось получить подробную информацию: {e}")
            
            print()
    
    except Exception as e:
        print(f"❌ Ошибка при получении списка коллекций: {e}")


if __name__ == "__main__":
    main()
