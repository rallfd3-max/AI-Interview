import requests
import json

BASE = "http://10.10.10.1:8889"

from DatabaseTool import DatabaseTool


def create_db(id: str, info: str, model: str = None):
    print(id)
    payload = {"db": id, "content": info}
    if model:
        payload["model"] = model
    r = requests.post(f"{BASE}/create_db", json=payload, timeout=30)
    if r.status_code >= 200 and r.status_code < 300:
        print(f"---------------{id} db created successfully---------------")
    return r.json()


def query_db(db_name: str, query: str, k: int = 5, model: str = None):
    payload = {"db": db_name, "query": query, "k": k}
    if model:
        payload["model"] = model
    r = requests.post(f"{BASE}/query", json=payload, timeout=30)
    # r.raise_for_status()
    return r.json()


def str_to_hex(str):
    ans = "A"
    for c in str:
        ans += hex(ord(c))[2:]
    return ans


if __name__ == "__main__":

    db = "测试"
    content = """
年薪:无
作息:007
    """
    print("Creating DB...")
    print(json.dumps(create_db(db, content), ensure_ascii=False, indent=2))

    print("\nQuerying...")
    res = query_db(db, "年薪", k=2)
    res = res["results"]["documents"][0]
    print(res)
