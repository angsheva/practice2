from flask import Flask, jsonify, request
import redis
from qdrant_client import QdrantClient
import json

app = Flask(__name__)

redis_client = redis.Redis(host='localhost', port=6379, db=0)
qdrant_client = QdrantClient(host="localhost", port=6333)

print("Подключение к Redis и Qdrant установлено")

@app.route('/')
def home():
    return '''
    <h1>Приложение с AI-инфраструктурой</h1>
    
    <h2>Чек системы:</h2>
    <a href="/health">/health</a> - статус всех сервисов<br><br>
    
    <h2>Тестовые endpoints:</h2>
    <a href="/test/redis">/test/redis</a> - тест Redis<br>
    <a href="/test/qdrant">/test/qdrant</a> - тест Qdrant<br>
    <a href="/cache/data">/cache/data</a> - посмотреть кеш<br><br>
    
    <h2>Работа с векторами:</h2>
    <a href="/vectors">/vectors</a> - список векторных коллекций<br>
    <a href="/search?query=hello">/search?query=hello</a> - поиск векторов
    '''

@app.route('/health')
def health_check():
    """Чек всех сервисов"""
    status = {
        "app": "Работает",
        "redis": "Не доступен", 
        "qdrant": "Не доступен"
    }
    
    # Проверяем Redis
    try:
        redis_client.ping()
        status["redis"] = "Работает"
    except:
        pass
        
    # Проверяем Qdrant  
    try:
        qdrant_client.get_collections()
        status["qdrant"] = "Работает"
    except:
        pass
        
    return jsonify(status)

@app.route('/test/redis')
def test_redis():
    """Тестируем Redis"""
    try:
        redis_client.set("message", "Redis")
        redis_client.set("counter", 42)
        
        message = redis_client.get("message").decode()
        counter = redis_client.get("counter").decode()
        
        return jsonify({
            "status": "success", 
            "message": message,
            "counter": counter
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/test/qdrant')  
def test_qdrant():
    try:
        collections = qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if "test_vectors" not in collection_names:
            qdrant_client.create_collection(
                collection_name="test_vectors",
                vectors_config={"size": 4, "distance": "Cosine"}
            )
        
        vectors = [
            {"id": 1, "vector": [0.1, 0.2, 0.3, 0.4], "payload": {"text": "Привет мир", "type": "greeting"}},
            {"id": 2, "vector": [0.5, 0.6, 0.7, 0.8], "payload": {"text": "Тестовый вектор", "type": "test"}},
            {"id": 3, "vector": [0.9, 0.1, 0.2, 0.3], "payload": {"text": "Векторный поиск", "type": "search"}}
        ]
        
        qdrant_client.upsert(
            collection_name="test_vectors",
            points=vectors
        )
        
        return jsonify({
            "status": "success",
            "message": "Добавлено 3 тестовых вектора в Qdrant",
            "collections": collection_names
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/cache/data')
def show_cache():
    try:
        keys = redis_client.keys("*")
        data = {}
        for key in keys:
            value = redis_client.get(key)
            data[key.decode()] = value.decode()
            
        return jsonify({
            "status": "success", 
            "cache_data": data
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/vectors')
def list_collections():
    try:
        collections = qdrant_client.get_collections()
        collections_info = []
        
        for collection in collections.collections:
            info = qdrant_client.get_collection(collection_name=collection.name)
            collections_info.append({
                "name": collection.name,
                "vectors_count": info.vectors_count
            })
            
        return jsonify({
            "status": "success",
            "collections": collections_info
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/search')
def search_vectors():
    """Поиск по векторам"""
    try:
        query_vector = [0.2, 0.3, 0.4, 0.5]  
        
        results = qdrant_client.search(
            collection_name="test_vectors",
            query_vector=query_vector,
            limit=3
        )
        
        search_results = []
        for result in results:
            search_results.append({
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            })
            
        return jsonify({
            "status": "success", 
            "query_vector": query_vector,
            "results": search_results
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("Запускаем Flask приложение...")
    print("Доступно по адресу: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)