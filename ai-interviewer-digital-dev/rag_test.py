import requests
from dotenv import load_dotenv
import os

load_dotenv()
def query_db(db_name: str, query: str, k: int = 5):
    payload = {"db": db_name, "query": query, "k": k}
    r = requests.post(f"{os.getenv('EMBEDDING_URL')}/query", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def str_to_hex(str):
    ans = "A"
    for c in str:
        ans += hex(ord(c))[2:]
    return ans

if __name__ == "__main__":
    job = "算法工程师"
    db = str_to_hex(job)
    result = query_db(db,"年薪",2)
    print(result)
