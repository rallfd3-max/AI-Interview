import os
import json
import pymysql
from dotenv import load_dotenv
from typing import Dict, Optional
from datetime import date, datetime

# 加载环境变量
load_dotenv()


class DatabaseTool:
    """数据库查询工具类 - PyMySQL 实现（修复日期序列化问题）"""

    def __init__(self):
        # 从环境变量获取数据库配置
        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", 3306)),
            "database": os.getenv("DB_NAME", "aiinterviewerdb"),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", "123123"),
            "charset": "utf8mb4",
            "cursorclass": pymysql.cursors.DictCursor  # 返回字典格式结果
        }

    def get_connection(self):
        """创建并返回数据库连接"""
        return pymysql.connect(**self.db_config)

    def query_db(self, sql, *args):
        try:
            connection = self.get_connection()
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql, args)
                    result = cursor.fetchall()  # 返回查询
                    return result

        except pymysql.Error as e:
            return {"error": f"数据库查询失败: {str(e)}"}
        except Exception as e:
            return {"error": f"未知错误: {str(e)}"}

    def insert_db(self, sql, *args):
        try:
            connection = self.get_connection()
            with connection:
                with connection.cursor() as cursor:
                    affected = cursor.execute(sql, args)
                connection.commit()  # 提交事务
            return affected > 0
        except pymysql.Error as e:
            return {"error": f"数据库查询失败: {str(e)}"}
        except Exception as e:
            return {"error": f"未知错误: {str(e)}"}
    def update_db(self, sql, *args):
        try:
            connection = self.get_connection()
            with connection:
                with connection.cursor() as cursor:
                    affected = cursor.execute(sql, args)
                connection.commit()  # 提交事务
            return affected > 0
        except pymysql.Error as e:
            return {"error": f"数据库查询失败: {str(e)}"}
        except Exception as e:
            return {"error": f"未知错误: {str(e)}"}

    def execute_update(self, url: str, candidateId: str):
        sql = """
               UPDATE interview_record
               SET interviewresult = %s
               WHERE candidate_id = %s
           """
        result = self.update_db(sql, url, candidateId)
        if result:
            return result
        else:
            return {"error": "未找到初试候选人信息"}
    # 获取对应mobile的用户在interview_record中的内容
    # 如果没有参加初试则返回None
    def get_candidate_info(self, mobile: str) -> Dict:
        """获取候选人信息"""
        sql = """
            SELECT c.real_name name,IF(c.sex=1, '男', '女') AS sex,c.job,j.job_desc as jobDesc,
            c.school,c.major,c.certificate,c.awards,c.experiment,c.introduce
            FROM candidate c
            JOIN job j on c.job_id = j.id
            WHERE c.mobile = %s;
        """
        result = self.query_db(sql, mobile)
        if result:
            # 转换日期对象为字符串
            return self.convert_dates_to_strings(result[0])
        else:
            return {"error": "未找到候选人信息"}

    def write_reexamine_info(self, mobile: str, question: str, answer: str):
        """往复试记录表中插入数据"""
        sql = """
            SELECT c.id,COUNT(re.id) cnt
            FROM candidate c
            LEFT JOIN reexamine_record re ON c.id = re.id
            WHERE c.mobile = %s
            GROUP BY c.id;
        """
        info = self.query_db(sql, mobile)
        sql = """
            INSERT INTO reexamine_record (id,`index`,question,answer) VALUES (%s, %s, %s,%s)
        """
        if info:
            info = info[0]
            return self.insert_db(sql, info["id"], info["cnt"], question, answer)
        else:
            return {"error": "未找到候选人信息"}

    def get_reexamine_info(self, mobile: str):
        """获取复试对话"""
        sql = """
            SELECT re.`index`,re.question,re.answer
            FROM candidate c
            JOIN reexamine_record re ON c.id = re.id
            WHERE c.mobile = %s
            ORDER BY re.`index`;
        """
        result = self.query_db(sql, mobile)
        if result:
            return result
        else:
            return {"error": "未找到候选人信息"}

    def convert_dates_to_strings(self, data: dict) -> dict:
        """将字典中的日期对象转换为字符串"""
        converted = {}
        for key, value in data.items():
            if isinstance(value, (date, datetime)):
                converted[key] = value.isoformat()
            else:
                converted[key] = value
        return converted

    def format_candidate_info(self, candidate_info: Dict) -> str:
        """格式化候选人信息为自然语言描述"""
        if "error" in candidate_info:
            return candidate_info["error"]

        # 处理可能为None的字段
        def safe_get(key, default="无"):
            value = candidate_info.get(key)
            return value if value is not None else default

        return (
            f"候选人姓名: {safe_get('real_name')}\n"
            f"职位: {safe_get('job_name')}\n"
            f"上次面试结果: {safe_get('result')}\n"
            f"面试时长: {safe_get('take_time')}分钟\n"
            f"手机: {safe_get('mobile')}\n"
            f"邮箱: {safe_get('email')}\n"
            f"出生日期: {safe_get('birthday')}\n"
            f"所在城市: {safe_get('city')}\n"
        )

    def get_candidate_info_formatted(self, candidate_id: str) -> str:
        """一步获取格式化后的候选人信息"""
        info = self.get_candidate_info(candidate_id)
        return self.format_candidate_info(info)

    def write_reexamine_summary(self, mobile, s_ai="", s_p="", end_question=""):
        """写入总结包括历史记录总结"""
        sql = """
            SELECT c.id,COUNT(re.id) cnt
            FROM candidate c
            LEFT JOIN reexamine_summary re ON c.id = re.id
            WHERE c.mobile = %s
            GROUP BY c.id;
        """
        info = self.query_db(sql, mobile)
        if info:
            info = info[0]
            if info["cnt"]:  # 是否存在
                sql = """
                    UPDATE reexamine_summary
                    SET
                      summary_tmp_ai = CASE WHEN %s  != '' THEN %s ELSE summary_tmp_ai  END,
                      summary_tmp_answer = CASE WHEN %s  != '' THEN %s ELSE summary_tmp_answer  END,
                      end_question = CASE WHEN %s  != '' THEN %s ELSE end_question  END
                    WHERE id = %s;
                """
                return self.insert_db(sql, s_ai, s_ai, s_p, s_p, end_question, end_question, info["id"])
            else:
                sql = """
                    INSERT INTO reexamine_summary VALUES(%s,%s,%s,%s);
                """
                return self.insert_db(sql, info["id"], s_ai, s_p, end_question)
        else:
            return {"error": "未找到候选人信息"}

    def get_reexamine_summary(self, mobile):
        """读取总结"""
        sql = """
            SELECT re.summary_tmp_ai s_it,re.summary_tmp_answer s_a,re.end_question enq
            FROM candidate c
            JOIN reexamine_summary re ON c.id = re.id
            WHERE c.mobile = %s;
        """
        info = self.query_db(sql, mobile)
        if info:
            return info[0]
        else:
            return {"error": "未找到候选人信息"}

    def get_initial_interview_info(self, session_id: str):
        """获取初试对话"""
        sql = """
            SELECT ir.answer_content
            FROM candidate c
            JOIN interview_record ir ON c.id = ir.candidate_id
            WHERE c.mobile = %s;
        """
        result = self.query_db(sql, session_id)
        if result:
            return result
        else:
            return {"error": "未找到初试候选人信息"}

    def get_job_requirements(self, mobile):
        """获取岗位需求"""
        sql = """
            SELECT j.job_desc
            FROM candidate c
            JOIN job j ON c.job_id = j.id
            WHERE c.mobile = %s;
        """
        info = self.query_db(sql, mobile)
        if info:
            return info[0]
        else:
            return {"error": "未找到岗位需求信息"}

    def get_initial_interview_info(self, session_id: str):
        """获取初试对话"""
        sql = """
            SELECT ir.answer_content
            FROM candidate c
            JOIN interview_record ir ON c.id = ir.candidate_id
            WHERE c.mobile = %s;
        """
        result = self.query_db(sql, session_id)
        if result:
            return result
        else:
            return {"error": "未找到初试候选人信息"}

    def get_job_name(self, id: str):
        """获取岗位的名字"""
        sql = """
            SELECT job_name
            FROM job
            WHERE id=%s
        """
        info = self.query_db(sql, id)
        if info:
            return info[0]
        else:
            return {"error": "未找到对应岗位"}


# 使用示例
if __name__ == "__main__":
    # 测试前设置环境变量
    # os.environ["DB_HOST"] = "localhost"
    # os.environ["DB_PORT"] = "3306"
    # os.environ["DB_NAME"] = "aiinterviewerdb"
    # os.environ["DB_USER"] = "root"
    # os.environ["DB_PASSWORD"] = "easyzhp123"
    db = DatabaseTool()
    mobile = "12345678901"
    res = db.get_candidate_info(mobile)
    print(res)
    # 安全地打印结果，避免序列化问题
    # if isinstance(info, dict):
    #     for key, value in info.items():
    #         print(f"{key}: {value}")
    # else:
    #     print(info['job_name'])

    # print(info['job_name'])
    # print(info['city'])

    # formatted = db_tool.format_candidate_info(info)
    # print("\n格式化后的候选人信息:")
    # print(formatted)
    #
    # # 一步获取格式化信息
    # print("\n一步获取格式化信息:")
    # print(db_tool.get_candidate_info_formatted(candidate_id))
