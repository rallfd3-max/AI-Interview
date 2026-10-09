import datetime
import os
from typing import Tuple
from DatabaseTool import DatabaseTool
from langchain_core.prompts import ChatPromptTemplate
# from langchain_deepseek import ChatDeepSeek
import dotenv
import asyncio
# from langchain_ollama.chat_models import ChatOllama
from models import CustomLangchainVllm
import io
from minio import Minio
from minio.error import S3Error
from urllib.parse import quote_plus
dotenv.load_dotenv()  # 环境


class CapabilityEvaluation:
    def __init__(self, session_id: str,candidateId:str):
        self.session_id = session_id
        self.candidateId=candidateId
        self.db_tool = DatabaseTool()
        # self.chat_model = ChatDeepSeek(
        #     api_key=os.getenv("DEEPSEEK_API_KEY"),
        #     base_url=os.getenv("DEEPSEEK_URL"),
        #     model="deepseek-chat",
        #     temperature=0
        # )
        self.minio_client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT"),  # 使用您提供的IP和端口
            access_key=os.getenv("MINIO_ACCESS_KEY"),  # 从环境变量获取
            secret_key=os.getenv("MINIO_SECRET_KEY"),  # 从环境变量获取
            secure=False  # 内部IP地址，通常使用HTTP
        )
        self.bucket_name =os.getenv("MINIO_BUCKET_NAME")  # 您的桶名称
        self.llm = CustomLangchainVllm(model=os.getenv("VLLM_NAME"),
                                       base_url=os.getenv("VLLM_URL"),
                                       temperature=0,
                                       streaming=False,
                                       think=True)
        self.evaluation_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "你是一位专业的技术招聘顾问，擅长分析面试者的技术能力和综合素质。"
                "根据提供的面试记录，客观评估面试者的优点和不足，重点关注岗位需求匹配度。"
                "评价应基于事实，避免主观臆断，每条评价都要有面试内容作为支撑。"
                """
                结构如下
                ### 各环节表现概述：
                初试：简述面试者在行业相关内容提问环节中的回答要点、对行业知识的掌握程度、回答的准确性和深度等情况。
                复试 - 自我介绍：说明面试者自我介绍的内容重点等表现。
                复试 - 项目经历：阐述面试者所讲项目的核心内容、自身角色、解决的关键问题及成果展示等方面的情况。
                复试 - 企业垂直问题：记录面试者对企业垂直问题的回答要点、回答的针对性和合理性等。
                ### 能力分析：
                专业能力：结合初试中对行业知识的掌握，以及复试项目经历和企业垂直问题回答中体现的与岗位相关的知识、技能，分析其专业能力水平。
                沟通表达能力：依据面试者在初试回答行业问题、复试各环节中的语言清晰度、表达连贯性、信息传递有效性等进行评估。
                逻辑思维能力：分析面试者在初试和复试各环节表述的条理性、逻辑性，以及对问题的理解和分析能力。
                应变能力：观察面试者在初试面对行业相关问题以及复试回答较难的企业垂直问题时的反应速度、应对方式和解决问题的思路。
                使用雷达图表现，组成多边形，它以一个中心点为起点，从中心点向外延伸出多条射线，每条射线代表一个特定的变量或指标。每条射线上的点或线段表示该变量在不同维度上的取值或得分，在射线终点写上对应技能。
                ### 综合能力：
                总结面试者在初试和复试中展现出的主要优势和存在的不足之处。
                给出总体的能力评估结论，说明其是否适合该岗位以及适合的程度。用数据表示
                """
                """
                返回格式要求：
                1.不要出现markdown标记，内容尽量通俗易懂。
                2.最后返回的内容为html文件形式的代码，要根据评估的内容来
                3.生成的代码所呈现的页面要美观，布局要合理
                4.不要导入其他网络资源，雷达图使用Js实现，不要使用外部的库，用数据表示
                """
            ),
            (
                "user",
                "请根据以下面试记录，分析面试者的技术能力和综合素质:\n{interview_content}\n"
                "岗位需求: {job_requirements}\n"
                """
                返回格式要求：
                1.不要出现markdown标记，内容尽量通俗易懂。
                2.最后返回的内容为html文件形式的代码，要根据评估的内容来
                3.生成的代码所呈现的页面要美观，布局要合理
                5.最后不要讲解评估结果，只返回html代码
                """
            )
        ])

    def extract_interview_data(self) -> Tuple[str, str]:
        """
        从数据库提取初试和复试内容
        返回格式: (面试内容文本, 岗位需求)
        """
        # 获取面试者信息
        initial_info = self.db_tool.get_initial_interview_info(self.session_id)
        reexamine_info = self.db_tool.get_reexamine_info(self.session_id)

        # 检查错误
        if "error" in initial_info:
            raise Exception(f"获取初试信息失败: {initial_info}")
        if any("error" in item for item in reexamine_info):
            raise Exception(f"获取复试信息失败: {reexamine_info}")

        # 获取岗位需求
        job_info = self.db_tool.get_job_requirements(self.session_id)
        job_requirements = job_info["job_desc"]

        # 构建面试内容文本# 构建面试内容文本 PS:这里可能出现文本太多导致出bug，可以用获取summary来进行总结
        interview_content = []
        if initial_info is not None:
            interview_content.append("=== 初试内容 ===\n")
            interview_content.append(initial_info[0]['answer_content'])

        if reexamine_info:
            interview_content.append("\n=== 复试内容 ===\n")
            for item in reexamine_info:
                if "question" in item and "answer" in item:
                    interview_content.append(f"面试官问题: {item['question']}\n面试者回答: {item['answer']}\n")

        interview_content = "".join(interview_content)
        return interview_content, job_requirements

    async def evaluate_capabilities(self) -> str:
        """
        分析面试内容，返回 AI 评估结果
        """
        try:
            # 提取面试数据
            interview_content, job_requirements = self.extract_interview_data()
            if not interview_content:
                return "没有找到有效的面试记录"

            evaluation_chain = self.evaluation_prompt | self.llm

            # 获取评估结果
            result = await evaluation_chain.ainvoke({
                "interview_content": interview_content,
                "job_requirements": job_requirements
            })

            return result.content

        except Exception as e:
            return f"评估过程出错: {str(e)}"

    async def generate_evaluation_report(self, file_path) -> str:
        """
        返回 AI 原始回答
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name=f"{self.session_id}_{timestamp}.html"
        file = os.path.join(file_path, file_name)
        print(f"""正在往{file}写入内容""")
        result = await self.evaluate_capabilities()
        try:
            with open(file, "w", encoding="utf-8") as f:
                f.write(result)
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            print(f"保存报告失败: {e}")
        print(f"{file}已经写入完成 exit{os.path.exists(file)}")
        minio_name=f"interviewresult/{file_name}"
        client = self.minio_client
        try:
            file=r"C:\Users\34562\Desktop\aimian2\ai-interviewer-digital-dev\12345678901.html"
            # 上传文件
            client.fput_object(
                bucket_name=self.bucket_name,
                object_name=minio_name,
                file_path=file
            )
            print(f"文件已成功上传至 {minio_name}")

        except S3Error as e:
            print(f"上传失败: {e}")
        url=os.getenv("MINIO_ENDPOINT")
        print(url)
        minio_url = f"http://{url}/{self.bucket_name}/{minio_name}"
        self.save_result_url(minio_url)
        return minio_url

    def save_result_url(self, url: str):
        """
        将结果URL保存到interview_record表中的interviewresult字段
        """
        try:
            # 执行更新
            print("开始保存到数据库")
            result = self.db_tool.execute_update(url, self.candidateId)
            if result:
                print(f"成功将URL保存到数据库: {url}")
                return True
            else:
                print(f"数据库更新失败: {result}")
                return False

        except Exception as e:
            print(f"保存URL到数据库时出错: {str(e)}")
            return False


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    evaluator = CapabilityEvaluation(session_id="12345678901", candidateId="1961719081678761985")
    minio_url = loop.run_until_complete(evaluator.generate_evaluation_report(os.getenv("html_path")))
    print(f"评估报告已生成并上传: {minio_url}")