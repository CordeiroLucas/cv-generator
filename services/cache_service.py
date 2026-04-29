import redis
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
INDEX_NAME = "idx:curriculos"
VECTOR_DIM = 384
DISTANCE_METRIC = "COSINE"

model = SentenceTransformer('all-MiniLM-L6-v2') 

def conectar_redis():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def criar_indice_se_nao_existir(client):
    try:
        client.ft(INDEX_NAME).info()
    except:
        schema = (
            TextField("$.html_content", as_name="html"),
            VectorField(
                "$.vector",
                "FLAT",
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

def gerar_embedding_local(texto):
    return model.encode(texto).astype(np.float32).tolist()

def buscar_cache(input_text, threshold=0.1):
    client = conectar_redis()
    criar_indice_se_nao_existir(client)
    vector = gerar_embedding_local(input_text)
    
    q = Query(f"*=>[KNN 1 @vector $query_vector AS vector_score]")\
        .sort_by("vector_score")\
        .return_fields("vector_score", "html")\
        .dialect(2)
    
    params = {"query_vector": np.array(vector, dtype=np.float32).tobytes()}
    results = client.ft(INDEX_NAME).search(q, query_params=params)
    
    if results.docs:
        doc = results.docs[0]
        if float(doc.vector_score) < threshold:
            return doc.html
    return None

def salvar_cache(input_text, html_content):
    client = conectar_redis()
    vector = gerar_embedding_local(input_text)
    doc_id = f"doc:{hash(input_text)}"
    data = {
        "html_content": html_content,
        "vector": vector
    }
    client.json().set(doc_id, "$", data)
    client.expire(doc_id, 604800)