# 导入外部
import threading

from langchain_core.prompts import PromptTemplate
from langchain_deepseek import ChatDeepSeek
import os
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor, tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.memory import ConversationTokenBufferMemory
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uuid
import tiktoken  # 添加 tiktoken 用于 token 计数
import asyncio
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Generator, Any
# 导入本地库
from interview_tools import *
from DatabaseTool import *
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory

mobile_phone = "13812345678"

# 1、使用.env 存储api_key
load_dotenv()

# os.getenv("REDIS_URL")

app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)


# 自定义 DeepSeek 类添加 token 计数方法
class CustomChatDeepSeek(ChatOpenAI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 使用类变量而不是实例变量
        self._encoding = None

    @property
    def encoding(self):
        """延迟加载编码器"""
        if self._encoding is None:
            self._encoding = tiktoken.get_encoding("cl100k_base")
        return self._encoding

    def get_num_tokens_from_messages(self, messages):
        """计算消息的 token 数量（兼容 OpenAI 格式）"""
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # 每条消息的开销

            # 处理不同类型的消息内容
            content = message.content
            if isinstance(content, list):
                # 处理多模态内容
                for item in content:
                    if item["type"] == "text":
                        num_tokens += len(self.encoding.encode(item["text"]))
            else:
                num_tokens += len(self.encoding.encode(str(content)))

            if hasattr(message, "name") and message.name:  # 检查是否存在name属性
                num_tokens += -1  # 名字字段减少一个额外开销
        num_tokens += 2  # 回复的开销
        return num_tokens


class InterviewServer:

    def __init__(self, session_id: str, info: dict):
        self.chatmodel = CustomChatDeepSeek(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_URL"),  # 注意 /v1 路径
            model="deepseek-chat",
            temperature=0,  # 准确输出，过高会更创意
            streaming=True,  # 确保启用流式输出
        )

        self.MEMORY_KEY = "chat_history"
        # print(info)
        # 注释: 2. 最后可以询问一些企业相关的问题。 这个技术点暂时不一定会被触发。
        self.SYSTEMPL = f"""
         背景: 你现在要设计面试流程，匹配面试者与岗位是否符合,在面试中通过不断的询问问题来达到考察的目的。
         根据历史对话记录，你需根据已知的面试者水平，设计当前询问内容，规划之后询问技能，获取面试者详尽信息确认是否适合这个岗位。
         你只需要动态更改流程，结合历史对话记录，以及历史的未来流程规划，规划目前和未来询面试流程即可。
         你的公司是上海第二工业大学。
         # 面试者信息:
         1. 姓名:{info['name']}
         2. 面试的岗位:{info['job']}
         4. 毕业学校:{info['school']}
         5. 专业:{info['major']}
         6. 获得的证书:{info['certificate']}
         7. 获得的奖项:{info['awards']}
         8. 实习经验:{info['experiment']}
         9. 个人简介:{info['introduce']}
         10. 面试者的性别:{info['sex']}
         面试者信息是基于求职信和初试的内容，如果有需要的能力或经验这里没有可以询问面试者，这里不代表面试者所有的能力。
         # 岗位需求:
         1. 面试职位的岗位要求:{info['jobDesc']}
         根据岗位要求忽略面试者信息中职业所不需要的能力。
         # 你的面试基本流程:
         第一步自我介绍，收集额外的面试者信息里面没有的内容，如果面试者信息里面已经包含了全部岗位所需技能与经验可以直接提问。
         第二步项目经验介绍，从第一步自我解释或者面试者信息中选择询问。
         第三步企业关心的垂直经验问题。
         # 判断面试面试流程每一个步骤结束标准
         1. 如果是基础岗位,自我介绍尽量包含需要包含学校,所属专业,实践经验等
         2. 如果是技术岗,尽可能询问2个项目经验作为计划。
         3. 企业关心的垂直领域的问题，尽可能询问到位。
         # 面试结束信号:
         1. 问答轮数达到{os.getenv("end_epoch")}轮,也就是提问和回答算1次，有{os.getenv("end_epoch")}次提问和回答,则需要终止面试。
         2. 面试的第一步，第二步，第三步完成达到面试流程结束标准后，整个面试则可以结束。
         3. 面试的流程中每一步中，如果对话超过10轮后还没有把内容聊清楚，就可以进入下一个步骤。
         4. 面试者不回答面试官问题，或者一直获得不到有用信息。
         # 复试面试要求:
         1. 首先确认面试者是否符合面试岗位的基本要求。
         2. 如果岗位所需技能都已提问完毕，而且面试者表现较好能力，可以计划提问更深入技能水平。
         3. 可以在历史对话上进行额外询问。
         # 内容回复要求
         1. 对于能力的分析信息除非现在是在历史记录总结，不然不能直接说出来。
         2. 输出格式:内容: 计划: 轮数:，计划如果目前没有可以写无
         3. 输出内容均为面试流程设计，具体为: 内容: 表示当前询问技术点，计划:接下来打算询问的技术点，如果历史记录中有结束计划，用结束计划的内容替换 轮数:轮数是历史记录最后一条加1
         4. 内容为当前计划如 内容:结合之前的图书管理系统案例，询问数据库如何规划。计划应当尽可能详细能让之后询问达到闭环效果，如 计划:如回答出数据库规划，可以结合如何优化查询，如不能回答可以确认这项技能欠缺，询问岗位的redis技能。
         5. 当超过{os.getenv("end_epoch")}论时，回答完面试者的问题或完成技术点询问后就结束面试，不要再询问更多技能经验等，同时计划格式更改为此格式:计划回复完Redis使用技术点后结束
         """

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.SYSTEMPL,
                ),
                MessagesPlaceholder(variable_name=self.MEMORY_KEY),
                (
                    "user",
                    "{input}"
                ),
                MessagesPlaceholder(variable_name="agent_scratchpad"),  # 后续其他内容占位
            ],
        )

        tools = [test, getnowtime]  # 在interview_tools定义的方法
        agent = create_openai_tools_agent(
            llm=self.chatmodel,
            tools=tools,
            prompt=self.prompt
        )  # 代理与工具进行交互
        self.sessionId = session_id
        self.memory = self.get_memory(self.sessionId)
        memory = ConversationTokenBufferMemory(
            llm=self.chatmodel,
            human_prefix="用户",
            ai_prefix="ergongda",
            memory_key=self.MEMORY_KEY,
            output_key="output",
            return_messages=True,
            max_token_limit=4000,
            chat_memory=self.memory,
        )
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True  # 添加错误处理
        )
        self.rebuildSystem = f"""
             背景:你是一位面试官，性格温和，但也能严格的进行筛选公司所需人员，如果面试者的回答不合理，或者说话方式不正式你也会提出来让他进行改正，如果用户一直不进行改进，你会非常生气结束面试。
             你特别不喜欢面试者回复很冗余尤其是列出很多点不能着重讲述的，说得话很长答不到点上，不能简明概括。
             如果面试者辱骂你你会直接退出面试。
             现在你有一个面试流程计划，表示你目前和未来所要询问的内容。
             你需要根据计划对面试者进行提问，同时也要确认他回答的正确性，最后针对你的问题对计划进行更新。
             你的面试流程计划格式为 内容:表示当前要询问的技能，计划:表示未来计划打算
             # 面试者信息:
             1. 姓名:{info['name']}
             2. 面试的岗位:{info['job']}
             4. 毕业学校:{info['school']}
             5. 专业:{info['major']}
             6. 获得的证书:{info['certificate']}
             7. 获得的奖项:{info['awards']}
             8. 实习经验:{info['experiment']}
             9. 个人简介:{info['introduce']}
             10. 面试者的性别:{info['sex']}
             面试者信息是基于求职信和初试的内容，如果有需要的能力或经验这里没有可以询问面试者，这里不代表面试者所有的能力。
             # 岗位需求:
             1. 面试职位的岗位要求:{info['jobDesc']}
             根据岗位要求忽略面试者信息中职业所不需要的能力。
             要求:
             1. 返回格式为：内容: 计划:
             2. 返回内容不能有md格式。
             3. 去除里面的****加粗部分
             # 内容部分要求:
             1. 询问的问题与计划优先以结束计划里面的为准，不能突然结束要先结束当前技术点询问。
             2. 你不能询问超过一项技能水平，如果面试计划中有多项，你应当就选择其中的一个进行提问，同时剩下没提问的可以放到计划中。
             3. 因为一次只能提问一个技能点，所以内容中不能出现列表格式。
             4. 你需要根据你的性格去更改最后的回复，大部分情况是让回复风格更符合你的性格，如果必要情况下可以修改计划。如:用户回复与你询问的无关同时你性格温和，你的返回可以改为内容:请问你是不清楚我的问题吗，需要我像你具体解释吗?计划:用户可能对这方面不了解，需要更改询问技术。
             5. 如果要问一些前沿的问题的时候，需要考虑面试者的项目经验与能力能否听懂，如果不能需要对概念进行解释后提问。
             6. 如果轮数超过{os.getenv("end_epoch")}，计划里面应当改为尽快结束当前技术点询问然后结束面试，将要结束面试这件事不能告诉面试者。
             7. 对计划内容进行简化，计划不应该超过3条，轮数超过{os.getenv("end_epoch")}则计划里面应当不超过1条甚至没有。
             8. 计划中如果出现完成什么知识点后面试结束，那么计划不进行修改。
             9. 不应该自行添加计划与内容中没有出现的询问点。
             10. 要保证人品没有问题，如果认为有这方面问题也可以结束面试。
             """
        # 修改执行器
        self.rebuildPrompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.rebuildSystem,
                ),
                (
                    "user",
                    "{input}"
                ),
                MessagesPlaceholder(variable_name="agent_scratchpad"),  # 后续其他内容占位
            ],
        )
        rebuildAgent = create_openai_tools_agent(
            llm=self.chatmodel,
            tools=tools,
            prompt=self.rebuildPrompt
        )
        self.rebuildAgent_executor = AgentExecutor(
            agent=rebuildAgent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True
        )

    def get_memory(self, sessid: str):
        chat_message_history = InMemoryChatMessageHistory()
        db_tool = DatabaseTool()
        epoch = 1
        # 添加历史记录总结
        chat_history = db_tool.get_reexamine_summary(sessid)
        if not any("error" in item for item in chat_history) and chat_history["s_it"]:
            chat_message_history.add_ai_message(chat_history["s_it"])
        # 添加最近10条对话，只有30~40这种区间的才会添加
        chat_history = db_tool.get_reexamine_info(sessid)
        if not any("error" in item for item in chat_history):
            l = len(chat_history) - 1
            chat_history = chat_history[l - l % 5:]
            if chat_history:
                epoch = chat_history[0]["index"]
            for message in chat_history:
                chat_message_history.add_ai_message(f'内容:{message["question"]},轮数:{epoch}')
                chat_message_history.add_user_message(f'内容:{message["answer"]},轮数:{epoch}')
                epoch = epoch + 1
        # [HumanMessage(content='你好', additional_kwargs={}, response_metadata={}), AIMessage(content='你好',
        # additional_kwargs={}, response_metadata={})] chat_message_history.clear()#清空历史记录
        print("chat_message_history:", chat_message_history.messages)
        store_message = chat_message_history.messages
        if len(store_message) >= 10:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        self.SYSTEMPL + f"""
                        这是一段你和用户的对话记忆，对其进行总结摘要，摘要使用第一人称‘我’，并且提取其中的用户关键信息。要精简总结内容，只需记录哪些技术点已经询问以及水平如何，压缩在200字其中有计划:的句子代表后续打算的提问，后续可能已经完成了部分。以如下格式返回:
                        总结摘要内容｜用户关键信息，从这次面试中得到的，如果已经是面试者信息里已经有的内容则不用提及
                        例如 面试者张三通过询问得知其学校为交通大学，在面试者信息之上他还擅长git技能，独自开发上传github
                        计划提问 | 根据计划与后续对话判断，总结后续还要问什么问题
                        例如 曾提问图书管理系统，已询问sql设计内容，计划提问如何加速sql的搜索速度。
                        结束计划 | 如果历史记录里面的轮数已经快到{os.getenv("end_epoch")}，可以写这个结束计划
                        汇总计划里面的问题，根据剩余轮数选择需要的首要问题。
                        """
                    ),
                    ("user", "{input}"),
                ]
            )
            chain = prompt | self.chatmodel
            summary = chain.invoke({"input": store_message})
            summary += f" 轮数:{epoch}"
            result = db_tool.write_reexamine_summary(sessid, s_ai=summary)
            print(result)
            chat_message_history.clear()
            chat_message_history.add_ai_message(str(summary))
            print("总结后：", chat_message_history.messages)
        return chat_message_history

    async def stream_response(self, query: str) -> AsyncGenerator[str, None]:
        """流式生成响应"""
        global answer_thread
        result = ""
        try:
            output = await self.agent_executor.ainvoke({"input": query, self.MEMORY_KEY: self.memory.messages})
            if "output" in output:
                print("第一次处理输出:" + output["output"])
                # 使用异步迭代器流式处理响应，会等待他结束
                async for chunk in self.rebuildAgent_executor.astream({"input": output["output"]}):
                    if "output" in chunk:
                        result = str(chunk["output"])
                        context = result[result.find("内容:") + 3:result.find("计划:")]
                        for char in context:
                            yield f"data: {json.dumps(char, ensure_ascii=False)}\n\n"  # yield char
                            await asyncio.sleep(0.06)  # 控制输出速度
        except Exception as e:
            error_msg = f"处理错误: {str(e)}"
            yield error_msg
        else:
            print("切换回答者")
            if not answer_thread or not answer_thread.is_alive():
                answer_thread = threading.Thread(target=ai_answer, args=(result,))
                answer_thread.start()


class IntervieweeServer:
    def __init__(self, session_id: str, info: dict):
        self.chatmodel = CustomChatDeepSeek(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_URL"),  # 注意 /v1 路径
            model="deepseek-chat",
            temperature=0,  # 准确输出，过高会更创意
            streaming=True,  # 确保启用流式输出
        )

        self.MEMORY_KEY = "chat_history"
        # print(info)
        # 注释: 2. 最后可以询问一些企业相关的问题。 这个技术点暂时不一定会被触发。
        self.SYSTEMPL = f"""
        背景: 你是一个求职者，{info['sex']}，性格内向、不善表达，行动偏拖延，但在感兴趣的事上能短暂专注。
        曾参加校园歌唱比赛和简单电商项目，团队协作经验缺乏。
        除Java外，略会C/C++控制台编程，但对系统技术和高级知识无深入涉猎。
        # 现阶段情况:
        1. 在你的姓名:{info['name']}
        2. 在你面试的岗位:{info['job']}
        4. 在你的毕业学校:{info['school']}
        5. 在你的专业:{info['major']}
        6. 在你写在求职信上的证书:{info['certificate']}
        7. 在你写在求职信上的奖项:{info['awards']}
        8. 在你写在求职信上的实习经验:{info['experiment']}
        9. 面试职位的岗位要求:{info['jobDesc']}
        # 回答要求
        1. 回复不能超过100字要尽可能精简
        2. 回答要符合背景里面设置的性格特征与技能水平
        3. 按照技能水平说相关的名词解释，不能说出与背景不符合的话
        4. 如果有问题按照背景来自己应该不知道，那么可以回答自己不知道
        5. 如果问题有名词是背景中不了解的，要询问这个名词的含义，如果接下来的解释按照背景来依然不清楚要承认自己不了解。
        6. 如果问题的答案涉及的专业你没有学过，你要说你不知道，或者按照自己所学内容提出另一个符合自身背景的答案。
        7. 问题要求名词解释的时候，要结合背景进行回复，如果按照背景你不会就回答不知道。
        8. 除了完全不知道回答不了一点以外，不能主动暴露自己缺点，比如主动说出自己不会高级语言，可以结合性格说出会加以学习等。
        9. 无论如何，都要按照背景里面的个人性格与能力来回答。
        """

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.SYSTEMPL,
                ),
                MessagesPlaceholder(variable_name=self.MEMORY_KEY),
                (
                    "user",
                    "{input}"
                ),
                MessagesPlaceholder(variable_name="agent_scratchpad"),  # 后续其他内容占位
            ],
        )

        tools = [test, getnowtime]  # 在interview_tools定义的方法
        agent = create_openai_tools_agent(
            llm=self.chatmodel,
            tools=tools,
            prompt=self.prompt
        )  # 代理与工具进行交互
        self.sessionId = session_id
        self.memory = self.get_memory(self.sessionId)
        memory = ConversationTokenBufferMemory(
            llm=self.chatmodel,
            human_prefix="用户",
            ai_prefix="ergongda",
            memory_key=self.MEMORY_KEY,
            output_key="output",
            return_messages=True,
            max_token_limit=4000,
            chat_memory=self.memory,
        )
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True  # 添加错误处理
        )

    def get_memory(self, sessid: str):
        chat_message_history = InMemoryChatMessageHistory()
        db_tool = DatabaseTool()
        # 添加历史记录总结
        chat_history = db_tool.get_reexamine_summary(sessid)
        if not any("error" in item for item in chat_history) and chat_history["s_a"]:
            chat_message_history.add_ai_message(chat_history["s_a"])
        # 添加最近10条对话，只有30~40这种区间的才会添加
        chat_history = db_tool.get_reexamine_info(sessid)
        if not any("error" in item for item in chat_history):
            l = len(chat_history) - 1
            chat_history = chat_history[l - l % 5:]
            for message in chat_history:
                chat_message_history.add_user_message(message["question"])
                chat_message_history.add_ai_message(message["answer"])
        print("chat_message_history:", chat_message_history.messages)
        store_message = chat_message_history.messages
        if len(store_message) >= 10:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        self.SYSTEMPL + """
                            这是一段你和用户的对话记忆，对其进行总结摘要，摘要使用第一人称‘我’。主要记录面试官的问题和自己的总结，让自己能对前面问题进行继续补充。
                            记忆中面试官的回复带有计划的部分请忽略，例如:内容: 你好 计划:询问java相关知识。忽略掉计划后面的询问java相关知识。
                        """
                    ),
                    ("user", "{input}"),
                ]
            )
            chain = prompt | self.chatmodel
            summary = chain.invoke({"input": store_message})
            print("summary:", summary)
            result = db_tool.write_reexamine_summary(sessid, s_p=summary)
            print(result)
            chat_message_history.clear()
            chat_message_history.add_message(summary)
            print("总结后：", chat_message_history.messages)
        return chat_message_history

    async def get_complete_response(self, query: str) -> str:
        print("Ask AI")
        try:
            # 通过 agent_executor 获取完整的响应（这里假设 astream 可以修改为非流式版本）
            output = await self.agent_executor.ainvoke({"input": query, self.MEMORY_KEY: self.memory.messages})
            if "output" in output:
                return output["output"]
        except Exception as e:
            error_msg = f"处理错误: {str(e)}"
            return error_msg


# 单向连接
@app.get("/chat")
async def chat(query: str, context: str):
    print("------------------------------Intervier--------------------------------------")
    # 初始化数据参数
    db_tool = DatabaseTool()
    info = db_tool.get_candidate_info(context)  # mobile

    master = InterviewServer(session_id=context, info=info)
    # 创建流式响应 - 添加SSE所需的headers
    response = StreamingResponse(
        master.stream_response(query),
        media_type="text/event-stream"
    )
    # response.headers["Cache-Control"] = "no-cache" # 防止缓存
    # response.headers["Connection"] = "keep-alive" # 保持连接的持续性
    # response.headers["X-Accel-Buffering"] = "no" # 控制响应流的缓冲行为
    return response


# WebSocket 流式接口
# 长期双向连接
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            query = data.get("query", "")
            context = data.get("context", "default_session")

            master = InterviewServer(session_id=context)

            # 流式处理并发送响应
            async for chunk in master.stream_response(query):
                await websocket.send_text(chunk)

    except WebSocketDisconnect:
        print("客户端断开连接")
    except Exception as e:
        error_msg = f"错误: {str(e)}"
        await websocket.send_text(error_msg)


'''
测试fastapi启动后是否能正常工作
'''
# 1.导入selenium中webdriver
from selenium import webdriver
# 选择查找方式
from selenium.webdriver.common.by import By
# 导入keys模块，完成键盘操作
from selenium.webdriver.common.keys import Keys
import time

options = webdriver.ChromeOptions()
options.add_argument("--incognito")
options.add_argument("--no-sandbox")
options.add_argument("--disable-extensions")


# 处理你提取到的中间内容


@app.get("/")
def test_demo():
    return {"Hello": "World11"}


import asyncio

driver = webdriver.Chrome(options=options)
driver.get('http://127.0.0.1:5500/interview.html')


def ai_answer(context):
    print("--------------------------answer-------------------------------")
    # 获取信息
    db_tool = DatabaseTool()
    info = db_tool.get_candidate_info(mobile_phone)  # mobile
    # 提问
    question = context[context.find("内容:") + 3:context.find("计划:")]
    with open('last_question.txt', 'w',encoding='utf-8') as f:
        f.write(question)
    print("回复问题:" + question)
    master = IntervieweeServer(session_id=mobile_phone, info=info)
    result = asyncio.run(master.get_complete_response(question))
    # 存储答案,替换换行防止直接提交
    result = result.replace('\n', '')
    db_tool.write_reexamine_info(mobile_phone, context, result)

    print(result)
    driver.find_element(value='//*[@id="user-input"]', by=By.XPATH).send_keys(result)
    time.sleep(1)
    driver.find_element(value='//button', by=By.XPATH).click()


answer_thread = None


def run_server():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    print("*****************记得改电话**********************")
    print("*****************记得改电话**********************")
    print("*****************记得改电话**********************")
    print("*****************记得改电话**********************")
    print("*****************记得改电话**********************")
    print("*****************记得改电话**********************")
    print("*****************记得改电话**********************")
    print("*****************记得改电话**********************")
    print("*****************记得改电话**********************")
    print("*****************记得改电话**********************")
    print("*****************记得改电话**********************")
    print("*****************记得改电话**********************")
    # output = '"您好！我是上海第二工业大学的AI面试官，负责今天的复试环节。请确保您处于安静的环境，准备好后点击下方输入框开始面试"'
    db_tool = DatabaseTool()
    info = db_tool.get_reexamine_info(mobile_phone)
    output = ""
    print(info)
    if not any("error" in item for item in info):
        with open('last_question.txt', 'r',encoding='utf-8') as f:
            output = f.read()
    else:
        output = '您好！我是上海第二工业大学的AI面试官，负责今天的复试环节。请确保您处于安静的环境，准备好后点击下方输入框开始面试。'
    answer_thread = threading.Thread(target=ai_answer, args=(output,))
    answer_thread.start()
    input()
