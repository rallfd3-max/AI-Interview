import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.callbacks import CallbackManager
from langchain.agents import AgentExecutor, create_react_agent, create_openai_tools_agent
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
import tiktoken
from langchain_core.messages import BaseMessage
from typing import List, Union


class CustomLangchainVllm(ChatOpenAI):
    def __init__(self, think=False, *args, **kwargs):

        if "base_url" not in kwargs:
            kwargs["base_url"] = "http://192.168.98.3:9997/v1/"
        if "api_key" not in kwargs:
            kwargs["api_key"] = "EMPTY"
        chat_template_kwargs = kwargs.pop("chat_template_kwargs", {})
        chat_template_kwargs.setdefault("enable_thinking", think)
        super().__init__(*args, **kwargs,
                         extra_body={
                             "chat_template_kwargs": chat_template_kwargs
                         }
        )


        self._encoding = None

    def get_num_tokens_from_messages(self, messages: List[Union[dict, BaseMessage]]) -> int:
        """
        计算输入消息的 token 数。
        """
        num_tokens = 0
        for msg in messages:
            if isinstance(msg, dict):
                content = msg.get("content", "")
            else:
                content = msg.content
            num_tokens += 4  # role + content 开销
            if isinstance(content, str):
                num_tokens += len(self.encoding.encode(content))
        num_tokens += 2  # assistant 起始符
        return num_tokens


class AddInput(BaseModel):
    x: int = Field(..., description="第一个数")
    y: int = Field(..., description="第二个数")


@tool(args_schema=AddInput)
def add(x: int, y: int) -> int:
    """将两个整数相加"""
    return x + y


tools = [add]
from dotenv import load_dotenv, find_dotenv

load_dotenv()
llm = CustomLangchainVllm(model="Qwen3-32B",
                          base_url="http://10.10.10.1:9997/v1/",
                          temperature=0)

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个ai助手",
        ),
        (
            "user",
            "{input}"
        ),
        MessagesPlaceholder(variable_name="agent_scratchpad"),  # 后续其他内容占位
    ],
)

# 采用 ReAct Agent 的提示模板：让模型在 Thought / Action / Observation 模式下调用工具
agent = create_openai_tools_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

executor = AgentExecutor(agent=agent,
                         tools=tools,
                         verbose=True,
                         handle_parsing_errors=True)
question = "你好"

result = executor.invoke({"input": question})

print("最终 Agent 回复:", result)
