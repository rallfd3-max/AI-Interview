from langchain.agents import create_openai_tools_agent, AgentExecutor, tool
import datetime
import json
import requests
from dotenv import load_dotenv
import os

load_dotenv()


@tool
def test():
    """Test tool"""
    return "test"


@tool
def getnowtime():
    """获取当前时间"""
    return datetime.datetime.now()


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


@tool(description="询问公司相关问题；job_name:填写基本信息里面的面试的岗位，query:询问公司哪方面内容")
def getCompanyInfo(job_name: str, query: str) -> str:
    """询问公司相关问题，返回字符串或 JSON 字符串结果。"""
    db = str_to_hex(job_name)
    result = query_db(db, query, k=3)["results"]["documents"][0]

    # 确保返回值是可序列化、简单类型（字符串或 JSON 字符串）
    return result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
