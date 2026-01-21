import redis
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query

# --- Configurações ---
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
INDEX_NAME = "idx:curriculos"
VECTOR_DIM = 384  # Dimensão do modelo 'all-MiniLM-L6-v2'
DISTANCE_METRIC = "COSINE" # Métrica de similaridade

# --- Modelo de Embedding Local (GRÁTIS) ---
# Carrega na primeira execução (pode demorar alguns segundos na inicialização)
print("Carregando modelo de embedding local...")
model = SentenceTransformer('all-MiniLM-L6-v2') 

def conectar_redis():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def criar_indice_se_nao_existir(client):
    try:
        client.ft(INDEX_NAME).info()
    except:
        # Cria o índice para busca vetorial
        schema = (
            TextField("$.html_content", as_name="html"),
            VectorField(
                "$.vector",
                "FLAT", # ou HNSW para grandes volumes
                {
                    "TYPE": "FLOAT32",
                    "DIM": VECTOR_DIM,
                    "DISTANCE_METRIC": DISTANCE_METRIC,
                },
                as_name="vector",
            ),
        )
        definition = IndexDefinition(prefix=["doc:"], index_type=IndexType.JSON)
        client.ft(INDEX_NAME).create_index(schema, definition=definition)
        print("Índice Redis criado com sucesso.")

def gerar_embedding_local(texto):
    """Gera vetor usando CPU local (Custo $0 de token)"""
    return model.encode(texto).astype(np.float32).tolist()

def buscar_cache(input_text, threshold=0.1):
    """
    Busca semanticamente. Threshold 0.1 significa 'muito parecido'.
    Quanto menor o threshold no COSINE distance, mais similar.
    """
    client = conectar_redis()
    criar_indice_se_nao_existir(client)

    vector = gerar_embedding_local(input_text)
    
    # Query KNN (Vizinhos mais próximos)
    q = Query(f"*=>[KNN 1 @vector $query_vector AS vector_score]")\
        .sort_by("vector_score")\
        .return_fields("vector_score", "html")\
        .dialect(2)
    
    params = {"query_vector": np.array(vector, dtype=np.float32).tobytes()}
    
    results = client.ft(INDEX_NAME).search(q, query_params=params)
    
    if results.docs:
        doc = results.docs[0]
        score = float(doc.vector_score)
        # Se a distância for menor que o limite, consideramos que é a mesma requisição
        if score < threshold:
            return doc.html
            
    return None

def salvar_cache(input_text, html_content):
    client = conectar_redis()
    vector = gerar_embedding_local(input_text)
    
    # Cria uma chave única baseada em hash simples para o ID do documento
    doc_id = f"doc:{hash(input_text)}"
    
    data = {
        "html_content": html_content,
        "vector": vector
    }
    
    # Salva como JSON no Redis
    client.json().set(doc_id, "$", data)
    # Define TTL (Tempo de vida) para expirar cache após 7 dias (opcional)
    client.expire(doc_id, 604800)