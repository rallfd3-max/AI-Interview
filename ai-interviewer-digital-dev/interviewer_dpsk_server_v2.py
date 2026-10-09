# 导入外部
import json
import os
from dotenv import load_dotenv, find_dotenv
from langchain.agents import create_openai_tools_agent, AgentExecutor, tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.memory import ConversationTokenBufferMemory
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, BackgroundTasks, UploadFile, File, HTTPException, \
    Form
from fastapi.middleware.cors import CORSMiddleware
import uuid
# 添加 tiktoken 用于 token 计数
import asyncio
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Generator, Any
# 导入本地库
from interview_tools import *
from DatabaseTool import *
from starlette.responses import JSONResponse
from vi import *

from models import CustomLangchainVllm

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


# 自定义 Ollama 类添加 token 计数方法


class InterviewServer:

    def __init__(self, session_id: str, info: dict):
        self.llm = CustomLangchainVllm(model=os.getenv("VLLM_NAME"),
                                       base_url=os.getenv("VLLM_URL"),
                                       temperature=0,
                                       streaming=False)

        self.MEMORY_KEY = "chat_history"
        db_tool = DatabaseTool()
        l = 0
        chat_history = db_tool.get_reexamine_info(session_id)
        if not any("error" in item for item in chat_history):
            l = len(chat_history) - 1
        print(f"----------------------------当前轮数:{l}-----------------------------------")
        # print(info)
        self.BASEINFO = f"""
         当前对话轮数:{l}
         # 基本信息
         ##  面试者信息:
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
         ## 岗位需求:
         1. 面试职位的岗位要求:{info['jobDesc']}
         根据岗位要求忽略面试者信息中职业所不需要的能力。
        """
        # 注释: 2. 最后可以询问一些企业相关的问题。 这个技术点暂时不一定会被触发。
        self.SYSTEMPL = f"""
         背景: 你现在要设计面试流程，匹配面试者与岗位是否符合,在面试中通过不断的询问问题来达到考察的目的。
         根据历史对话记录，你需根据已知的面试者水平，设计当前询问内容，规划之后询问技能，获取面试者详尽信息确认是否适合这个岗位。
         你只需要动态更改流程，结合历史对话记录，以及历史的未来流程规划，规划目前和未来询面试流程即可。
         {self.BASEINFO}
         # 内容回复要求
         1. 回复格式为，不能另起一行，注也要写在当前询问内容里面:
            当前询问内容:
            计划之后询问:
         - 当前询问内容为，所有要当前告诉面试者的内容都写在这里:
            如: 当前询问内容内容:结合之前的图书管理系统案例，询问数据库如何规划，同时告诉面试者之后有环节提问员工福利这些信息。
         - 计划之后询问部分，应当尽可能详细能让之后询问达到闭环效果，同时最后附上当前面试环节:
            如 计划之后询问:如回答出数据库规划，可以结合如何优化查询，如不能回答可以确认这项技能欠缺，询问岗位的redis技能，当前面试环节询问垂直问题。
         2. 对于能力的分析信息除非现在是在历史记录总结，不然不能直接说出来。
         3. 输出内容均为面试流程设计
         4. 对于面试者询问的问题你需要给出回答前，查询工具获得准确答案后再作答，如果没有获得答案要告诉面试者不清楚。
         # 你的面试基本流程:
         第一步 自我介绍，收集额外的面试者信息里面没有的内容，如果面试者信息里面已经包含了一个项目经验则跳过这个环节。
         第二步 项目经验介绍，从第一步自我解释或者面试者信息中选择询问。
         第三步 企业关心的垂直经验问题，从面试者的所有项目经验里面选一个与岗位要求最相关的进行询问。此阶段只问一个项目的经历。
         第四步 询问岗位需求要求里面企业要询问的问题，依次询问面试者这些问题，如果面试者的问题涉及公司信息要使用工具查询，每个问题都要用户回复了再进入下一个问题。
         第五步 解答环节，给用户时间提问岗位问题。
         如果用户提前提问岗位相关问题，对其进行忽略继续当前任务安排。
         面试阶段不能跳过，不能提前进行面试者提问环节，如果面试者提前询问要告知之后有环境进行提问。
         # 面试流程时间安排
         1. 如果是基础岗位,自我介绍尽量包含需要包含学校,所属专业,实践经验等
         2. 要预留3轮用于面试者提问环节，此时计划为询问面试者是否有相关问题。
         3. 面试的流程中每一步中，如果对话超过3轮后还没有把内容聊清楚，就可以进入下一个步骤。
         4. 面试者不回答面试官问题，或者一直获得不到有用信息，可以结束面试。
         5. 当超过{os.getenv("end_epoch")}论时，不要再询问更多技能经验等，同时计划格式更改为此格式:计划之后询问:询问完Redis使用技术点后结束
         6. 解答环节要在{os.getenv("end_epoch")}-3轮时候开始，要在此之前结束面试的前3步骤，同时计划之后询问内容改为:解答面试者问题。
         # 复试面试流程设计:
         1. 确认面试者是否符合面试岗位的基本要求。
         2. 问的问题都要符合企业所需要的，只问用户的实现思路，而不具体问如何实现。
         3. 可以结合历史记录进行延续。
         4. 注意轮数不能太久，不能超过{os.getenv("end_epoch")}，合理分配每一个阶段的时间
         # 历史对话
         给出了历史的对话内容，你可以结合历史去调整流程，历史记录里面也有计划之后询问，你可以根据这个作为参考作为回复。
         如果出现结束计划，表示对话太长了，要尽快结束。
         # 特别注意，这点必须严格遵循
         1. 如果面试已经结束并且面试者也告知没有问题了 或者因为突发情况导致的结束，做以下处理
            当前询问内容中 告诉面试者点击上方退出按钮进行退出
            计划之后询问 内容为固定为 面试结束，用户已经退出
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
                MessagesPlaceholder(variable_name="agent_scratchpad", optional=True),  # 后续其他内容占位
            ],
        )

        tools = [test, getCompanyInfo]  # 在interview_tools定义的方法

        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=tools,
            prompt=self.prompt
        )  # 代理与工具进行交互
        self.sessionId = session_id
        self.memory = self.get_memory(self.sessionId)
        memory = ConversationTokenBufferMemory(
            llm=self.llm,
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
             背景:你是一位面试官，性格温和，有更多的耐心，但也能严格的进行筛选公司所需人员，如果面试者的回答不合理，或者说话方式不正式你也会提出来让他进行改正，如果用户一直不进行改进，你会非常生气结束面试。
             你特别不喜欢面试者回复很冗余尤其是列出很多点不能着重讲述的，说得话很长答不到点上，不能简明概括，会提前结束面试。
             现在你有一个面试流程计划，基于用户当前回复给出了面试计划，是对你回答的一个帮助，你可以根据他进行回答也能进行修改后回答。
             用户不想回答直接结束面试，说明其态度有问题。
             如果用户一直回复不知道，可以退出面试
             # 面试计划格式如下
             - 当前询问内容:
             - 计划之后询问:
             其中当前询问内容就是给你回答的推荐，你可以根据修改要求进行修改，但尽量保持原意不能随意添加其他问题。
             计划之后询问表示之后要询问的内容，作为后续面试的流程安排，如突发情况，比如面试计划要继续询问，但是用户回答态度恶劣你出言提醒，可以把当前内容延后放在计划之后询问里面。
             {self.BASEINFO}
             # 修改要求:
             1.回复格式为，不能另起一行，注也要写在当前询问内容里面:
                当前询问内容: 
                计划之后询问:
             2. 你只有这两行需要修改。
             3. 返回内容不能有md格式，同时只能包含utf-8字体。
             4. 你可以根据自己的性格特征去修改回复的内容，语气等。
             5. 去除里面的****加粗部分
             6. 因为一次只能提问一个技能点，所以当前询问内容中不能出现列表格式，把其他内容添加到 计划之后询问 中。
             7. 尽可能保留面试流程计划的愿意，你可以把当前内容推迟，但如果时间过久了，可以强制终止当前问题，保证面试的不应该过长。
             8. 如果轮数超过{os.getenv("end_epoch")}，计划之后询问里面应当改为尽快结束当前技术点询问然后结束面试，面试要快要结束这件事不能告诉面试者。
             9. 对计划内容进行简化，计划不应该超过3条，轮数超过{os.getenv("end_epoch")}则计划里面应当不超过1条甚至没有。
             10. 如果进入{os.getenv("end_epoch")}-3轮了，则计划之后询问改为进入解答环节。
             11. 用户询问问题，可以通过调用本地查询，如果询问企业问题要确认在解答阶段，结合本地查询的答案进行正确回复，。
             12. 面试计划面试者是看不见的，所以当前询问内容里面的内容是你回答的一个格式上的参考，内容不一定正确，需要你本地查询进行验证。
             13. 你不能告诉面试者你的面试流程
             # 特别注意，这点必须严格遵循
             1. 如果面试已经结束并且面试者也告知没有问题了 或者因为突发情况导致的结束，做以下处理
                当前询问内容中 参考面试流程计划结合自身性格回复，并且告诉面试者点击上方退出按钮进行退出
                计划之后询问 内容为固定为 面试结束，用户已经退出
             2. 轮数接近上限进入下一流程这句话，改为面试时间过长告诉面试者。
             3. 输出严格为两行内容，为输出格式里面的填充
             4. 面试流程计划中有一份当前询问内容，根据用户之前对话给出的询问建议，你要在这个基础上根据你的要求去优化这个内容。
             5. 除非用户的回答过于恶劣，否则你就只需要对面试流程计划里面的询问内容进行优化，不能添加其他问题。
             """
        # 暂时删除内容 你不能询问超过一项技能水平，如果面试计划中有多项，你应当就选择其中的一个进行提问，同时剩下没提问的可以放到计划中。
        #
        #
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
                MessagesPlaceholder(variable_name="agent_scratchpad", optional=True),  # 后续其他内容占位
            ],
        )
        rebuildAgent = create_openai_tools_agent(
            llm=self.llm,
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
        print(f"chat_history:{chat_history}")
        l = 0
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
        print(f"epoch:{epoch}")
        store_message = chat_message_history.messages
        if (l + 1) % 5 == 0:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        self.BASEINFO + f"""
                        这是一段你和用户的对话记忆，对其进行总结摘要，摘要使用第一人称‘我’，并且提取其中的用户关键信息。要精简总结内容，压缩在200字其中有计划:的句子代表后续打算的提问，后续可能已经完成了部分。以如下格式返回:
                        历史摘要｜用户关键信息，从这次面试中得到的，如果已经是面试者信息里已经有的内容则不用提及
                        例如 面试者张三通过询问得知其学校为交通大学，在面试者信息之上他还擅长git技能，独自开发上传github
                        计划提问 | 根据计划与后续对话，总结后续还要问什么问题
                        例如 曾提问图书管理系统，已询问sql设计内容，计划提问如何加速sql的搜索速度。
                        结束计划 | 如果历史记录里面的轮数已经快到{os.getenv("end_epoch")}，可以写这个结束计划
                        汇总计划里面的问题，根据剩余轮数选择需要的首要问题。
                        # 特别注意:
                        必须严格按照上述格式进行返回 历史摘要 计划提问 结束计划 只能出现这三个板块
                        你是做面试总结的，不要对用户问题进行回复，你只要总结所有历史内容
                        """
                    ),
                    ("user", "{input}"),
                ]
            )
            chain = prompt | self.llm

            summary = chain.invoke({"input": store_message})
            summary = summary.content
            if summary.find("轮数｜") != -1:
                summary = summary[:summary.find("轮数｜")]
            summary += f"轮数:{epoch - 1}"
            print("总结后:", summary)
            result = db_tool.write_reexamine_summary(sessid, s_ai=summary)
            print(result)
            chat_message_history.clear()
            chat_message_history.add_ai_message(str(summary))
            # print("总结后：", chat_message_history.messages)
        return chat_message_history

    async def stream_response(self, query: str) -> AsyncGenerator[str, None]:
        """流式生成响应"""
        global answer_thread
        result = ""
        try:
            print(f"message:{self.memory.messages}")
            output = await self.agent_executor.ainvoke({"input": query, self.MEMORY_KEY: []})
            if "output" in output:
                print("第一次处理输出:" + output["output"])
                # 使用异步迭代器流式处理响应，会等待他结束
                async for chunk in self.rebuildAgent_executor.astream(
                        {"input": f"""面试者的回复:{query}\n\n当前面试计划{output["output"]}"""}):
                    if "output" in chunk:
                        result = str(chunk["output"])
                        db_tool = DatabaseTool()
                        db_tool.write_reexamine_summary(self.sessionId, end_question=result)
                        # context = result[result.find("内容:") + 3:result.find("计划之后询问:")]
                        # print(context)
                        endIF = result[result.find("计划之后询问:"):]
                        if endIF.find("用户已经退出") != -1:
                            result += '^^'
                        for char in result:
                            yield f"data: {json.dumps(char, ensure_ascii=False)}\n\n"  # yield char
                            await asyncio.sleep(0.06)  # 控制输出速度
        except Exception as e:
            error_msg = f"处理错误: {str(e)}"
            yield error_msg
            # async def stream_response(self, query: str) -> AsyncGenerator[str, None]:
            #     """流式生成响应 - 修复版本"""
            #     try:
            #         # 使用异步迭代器流式处理响应
            #         async for chunk in self.agent_executor.astream({"input": query, "chat_history": self.memory.messages}):
            #             if "output" in chunk:
            #                 # 确保输出是字符串
            #                 output = str(chunk["output"])
            #                 # 发送符合SSE格式的数据
            #                 yield f"data: {output}\n\n"
            #                 await asyncio.sleep(0.06)  # 控制输出速度
            #     except Exception as e:
            #         error_msg = f"data: 处理错误: {str(e)}\n\n"
            #         yield error_msg
            #     finally:
            #         # 发送结束标志
            #         yield "event: end\ndata: [DONE]\n\n"
            # async def stream_response(self, query: str) -> AsyncGenerator[str, None]:
            #     """流式生成响应 - 完全符合SSE规范"""
            #     try:
            #         # 发送初始心跳（保持连接）
            #         yield ": heartbeat\n\n"
            #
            #         # 流式处理响应
            #         buffer = ""
            #         async for chunk in self.agent_executor.astream({"input": query, "chat_history": self.memory.messages}):
            #             if "output" in chunk:
            #                 output = str(chunk["output"])
            #
            #                 # 将输出添加到缓冲区
            #                 buffer += output
            #
            #                 # 寻找自然断点（如句子结束）
            #                 last_punctuation = max(buffer.rfind('。'), buffer.rfind('？'), buffer.rfind('！'), buffer.rfind('.'))
            #                 if last_punctuation != -1 and len(buffer) > 10:
            #                     # 发送到断点处的内容
            #                     to_send = buffer[:last_punctuation + 1]
            #                     buffer = buffer[last_punctuation + 1:]
            #
            #                     # 确保格式符合SSE规范
            #                     yield f"data: {json.dumps(to_send, ensure_ascii=False)}\n\n"
            #
            #                 # 定期发送心跳
            #                 yield ": heartbeat\n\n"
            #                 await asyncio.sleep(0.06)
            #
            #         # 发送剩余内容
            #         if buffer:
            #             yield f"data: {json.dumps(buffer, ensure_ascii=False)}\n\n"
            #
            #     except Exception as e:
            #         error_msg = f"处理错误: {str(e)}"
            #         yield f"data: {json.dumps(error_msg, ensure_ascii=False)}\n\n"
            #     finally:
            #         # 发送结束事件
            #         yield "event: end\ndata: [DONE]\n\n"


# 配置常量
UPLOAD_DIR = r"uploads\voice"  # 音频文件存储目录
ALLOWED_AUDIO_TYPES = [
    "audio/wav", "audio/x-wav", "audio/wave", "audio/x-pn-wav",
    "audio/mpeg", "audio/mp3", "audio/ogg", "audio/webm"
]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB最大文件大小限制

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)


url=os.getenv("funasr_url")
@app.post("/uploadVoice", summary="语音文件上传接口")
async def upload_voice(file: UploadFile = File(...)):
    """
    接收语音文件并转发到识别服务
    """
    try:
        # 1. 验证文件类型和大小
        if file.content_type not in ALLOWED_AUDIO_TYPES:
            raise HTTPException(400, detail=f"不支持的文件类型: {file.content_type}")

        # 2. 创建临时文件路径
        file_ext = os.path.splitext(file.filename)[1] or ".wav"
        temp_filename = f"temp_{uuid.uuid4().hex}{file_ext}"
        temp_path = os.path.join(UPLOAD_DIR, temp_filename)

        # 3. 保存临时文件
        with open(temp_path, "wb") as f:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(400, detail="文件超过大小限制")
            f.write(content)

        # 4. 转发到识别服务 [1,6](@ref)
        with open(temp_path, "rb") as audio_file:
            files = {"audio": (file.filename, audio_file, file.content_type)}
            response = requests.post(
                url,
                files=files,
                timeout=30  # 增加超时时间
            )
            text=response.text
            text=json.loads(text)
            text = text["text"]
            print(text)
        # 6. 返回识别结果
        return JSONResponse({
            "status": 200,
            "text": text,
        })

    except requests.exceptions.Timeout:
        raise HTTPException(504, detail="识别服务响应超时")



import requests


def str_to_hex(str):
    ans = "A"
    for c in str:
        ans += hex(ord(c))[2:]
    return ans


@app.post("/info")
async def create_db(id: str = Form(...), info: str=Form(...), model: str = None):
    print("hello")
    db_tool = DatabaseTool()
    job_name = db_tool.get_job_name(id)['job_name']  # mobile
    if any("error" in item for item in job_name):
        return json.dumps({"error": "id未找到对应job"})
    job_name = str_to_hex(job_name)
    payload = {"db": job_name, "content": info}
    if model:
        payload["model"] = model
    r = requests.post(f"{os.getenv('EMBEDDING_URL')}/create_db", json=payload, timeout=30)
    if r.status_code >= 200 and r.status_code < 300:
        print(f"---------------{job_name} db created successfully---------------")
    return r.json()


# 单向连接
@app.get("/chat")
async def chat(query: str, context: str, question: str):
    # context:是id,query:是答案,question:考官之前的问题
    # 初始化数据参数
    db_tool = DatabaseTool()
    info = db_tool.get_candidate_info(context)  # mobile
    # 对话存储
    print(f"question:{question}\nanswer:{query}")
    db_tool.write_reexamine_info(context, answer=query, question=question)

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
    # return f"data: {json.dumps('12345678901234213', ensure_ascii=False)}\n\n"


from fastapi import Request
import multiprocessing
from capability_evaluation import CapabilityEvaluation


@app.get('/history-message')
def get_history_message(id):
    db_tool = DatabaseTool()
    answers = []
    # 添加历史记录总结
    chat_history = db_tool.get_reexamine_info(id)
    if not any("error" in item for item in chat_history):
        for chat in chat_history:
            answers.append(chat['question'])
            answers.append(chat['answer'])
    end_question = db_tool.get_reexamine_summary(id)
    if not any("error" in item for item in end_question):
        answers.append(end_question["enq"])
    for i in range(len(answers)):
        answer = answers[i]
        where = answer.find("当前询问内容:")
        if where != -1:
            answer = answer[where + 7:]
        where = answer.find("计划之后询问:")
        if where != -1:
            answer = answer[:where]
        answer = answer.replace(r'\\n', '').replace(r'\n','')
        answers[i] = answer
    print(answers)
    return f'{json.dumps({"flag": False, "message": json.dumps(answers, ensure_ascii=False)}, ensure_ascii=False)}\n\n'


def run_report_generation(session_id:str,candidateId: str):
    evaluator = CapabilityEvaluation(session_id,candidateId)
    print("生成中")
    import asyncio
    asyncio.run(evaluator.generate_evaluation_report(os.getenv("html_path")))


@app.post("/exit")
async def exit(mobile:str=Form(...),candidateId: str = Form(...), candidateName: str = Form(...)):
    print("exit")
    # 启动一个后台进程
    p = multiprocessing.Process(target=run_report_generation, args=(mobile,candidateId))
    p.start()

    # 立即返回前端响应
    return {"msg": f"{candidateName} 正在退出，报告将稍后生成"}



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


@app.get("/")
def test_demo():
    return {"Hello": "World11"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


