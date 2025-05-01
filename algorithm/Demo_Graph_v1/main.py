import os
import requests
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging  # 添加日志库
import jieba  # 添加分词库
import time  # 添加用于重试机制

# 禁用jieba的日志输出
jieba.setLogLevel(logging.INFO)

# 加载环境变量
load_dotenv()

# 配置参数
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
ONEAPI_BASE_URL = os.getenv("ONEAPI_BASE_URL")
ONEAPI_API_KEY = os.getenv("ONEAPI_API_KEY")
ONEAPI_MODEL = os.getenv("ONEAPI_MODEL")
ONEAPI_EMBEDDING_MODEL = os.getenv("ONEAPI_EMBEDDING_MODEL")

class KnowledgeGraphQuery:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self.headers = {
            "Authorization": f"Bearer {ONEAPI_API_KEY}",
            "Content-Type": "application/json"
        }
        self.model = ONEAPI_MODEL
        self.neo4j_available = self.check_neo4j_status()  # 检查Neo4j是否可用
        self.api_available = self.check_api_status()  # 检查API是否可用
        
    def close(self):
        self.driver.close()
    
    def check_neo4j_status(self):
        """检查Neo4j数据库是否可用"""
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("✅ Neo4j数据库连接正常")
            return True
        except Exception as e:
            print(f"⚠️ Neo4j数据库连接失败: {str(e)}")
            print("请检查Neo4j服务是否正常运行和连接参数是否正确")
            return False
    
    def check_api_status(self):
        """检查API是否可用"""
        try:
            test_messages = [{"role": "user", "content": "你好"}]
            self.call_oneapi(test_messages, check_only=True)
            print("✅ API连接正常")
            return True
        except Exception as e:
            print(f"⚠️ API连接失败: {str(e)}")
            print("系统将使用本地模式运行")
            return False
        
    def execute_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]
    
    def call_oneapi(self, messages, temperature=0.1, max_retries=2, check_only=False):
        """调用ONEAPI，增加重试机制"""
        api_url = f"{ONEAPI_BASE_URL}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "max_tokens": 2000,
            "temperature": temperature,
            "top_p": 0.7,
            "frequency_penalty": 0.5,
            "n": 1,
            "response_format": {"type": "text"}
        }
        
        retries = 0
        while retries <= max_retries:
            try:
                response = requests.post(api_url, json=payload, headers=self.headers, timeout=30)
                response_data = response.json()
                
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    return response_data["choices"][0]["message"]["content"]
                elif check_only:  # 仅检查API状态
                    return True
                else:
                    error_msg = response_data.get("error", {}).get("message", "未知错误")
                    raise Exception(f"API响应格式错误: {error_msg}")
            except Exception as e:
                retries += 1
                if retries <= max_retries:
                    time.sleep(1)  # 重试间隔
                else:
                    if check_only:
                        return False
                    raise Exception(f"API调用失败: {str(e)}")
    
    def offline_fallback_response(self, question, results):
        """当API不可用时的离线回退处理"""
        # 提取节点的基本属性
        extracted_info = {}
        
        for item in results:
            for node_key, node_data in item.items():
                if isinstance(node_data, dict) and "name" in node_data:
                    node_name = node_data["name"]
                    if node_name not in extracted_info:
                        extracted_info[node_name] = {}
                    
                    # 复制所有属性（除了name）
                    for attr_key, attr_value in node_data.items():
                        if attr_key != "name":
                            extracted_info[node_name][attr_key] = attr_value
        
        # 生成简单回答
        answer = f"根据知识图谱中的信息，我找到了以下相关内容：\n\n"
        
        for name, attrs in extracted_info.items():
            answer += f"- {name}:\n"
            for attr_key, attr_value in attrs.items():
                answer += f"  • {attr_key}: {attr_value}\n"
            answer += "\n"
            
        if not extracted_info:
            answer += "很抱歉，未能从查询结果中提取到有用信息。"
            
        return answer
    
    def natural_language_to_cypher(self, question):
        """使用语义分析生成更智能的Cypher查询"""
        # 中文停用词列表（常见无意义词汇）
        stop_words = {'的', '了', '和', '是', '在', '我', '有', '这', '那', '你', '就', '也', '与', '而', '使', '一个', '吗', '呢', '吧', '啊'}
        
        # 使用jieba进行分词
        keywords = [word for word in jieba.lcut(question) if len(word) > 1 and word not in stop_words]
        
        # 生成优先级查询列表
        queries = []
        for keyword in keywords:
            # 生成Cypher查询
            cypher_query = f"MATCH (n) WHERE n.name CONTAINS '{keyword}' RETURN n"
            queries.append(cypher_query)
        return queries
    
    def explain_results(self, question, results):
        """使用大语言模型解释查询结果，添加错误处理和回退方案"""
        if not self.api_available:
            return self.offline_fallback_response(question, results)
            
        results_str = str(results)
        prompt = f"""
        基于以下知识图谱查询结果，回答问题：
        问题：{question}
        查询结果：{results_str}
        请提供一个清晰、准确的回答，基于查询结果中的信息。
        """
        messages = [
            {"role": "system", "content": "你是一个知识图谱查询解释器。你的任务是解释Neo4j查询结果并回答用户问题。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            explanation = self.call_oneapi(messages)
            return explanation.strip()
        except Exception as e:
            return self.offline_fallback_response(question, results)
    
    def query_knowledge_graph(self, question):
        """完整的查询流程"""
        # 1. 转换为多个Cypher查询
        cypher_queries = self.natural_language_to_cypher(question)
        
        # 2. 挨个执行查询，收集所有结果
        all_results = []
        
        for cypher_query in cypher_queries:
            try:
                results = self.execute_query(cypher_query)
                
                # 将有效结果添加到总结果集中
                if results:
                    all_results.extend(results)
            except Exception as e:
                pass
        
        # 3. 解释所有收集到的结果
        if all_results:
            # 限制结果数量避免API超长
            max_results = 30 if len(all_results) > 30 else len(all_results)
            answer = self.explain_results(question, all_results[:max_results])
            print(f"\n回答: {answer}", flush=True)
        else:
            print("\n未找到相关信息。")

def main():
    try:
        kg_query = KnowledgeGraphQuery()
        try:
            print("知识图谱查询系统 (输入'exit'退出)")
            print("------------------------------------")
            while True:
                question = input("\n请输入你的问题: ")
                if question.lower() == 'exit':
                    break
                kg_query.query_knowledge_graph(question)
        finally:
            kg_query.close()
    except Exception as e:
        print(f"程序发生错误: {str(e)}")
        print("请检查网络连接和API密钥是否正确设置。")

if __name__ == "__main__":
    main()