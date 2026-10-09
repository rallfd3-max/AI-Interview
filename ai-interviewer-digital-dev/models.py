from langchain_openai import ChatOpenAI
import tiktoken
from typing import List, Union
from langchain_core.messages import BaseMessage


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
        num_tokens = 0
        for msg in messages:
            if isinstance(msg, dict):
                content = msg.get("content", "")
            else:
                content = msg.content
            num_tokens += 4
            if isinstance(content, str):
                num_tokens += len(self.encoding.encode(content))
        num_tokens += 2
        return num_tokens
