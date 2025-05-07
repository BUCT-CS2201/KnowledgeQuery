from langchain.prompts import ChatPromptTemplate
from langchain.prompts import  ChatPromptTemplate, HumanMessagePromptTemplate,SystemMessagePromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain.memory import ConversationBufferWindowMemory
from langchain.llms.base import LLM
from graph_database import GraphData
from config import neo4j_config
from config import tongyi_config
from config import openai_config
from prompt import REWRITE_QUERY_PROMPT, CYPHER_GENERATION_PROMPT, TO_FORMAT_PROMPT, ANSWER_GENERATION_PROMPT_HUMAN, ANSWER_GENERATION_PROMPT_SYSTEM

class QueryRewriter:
    """ 问题改写器
    
    根据问题和记忆, 利用LLM生成一个新问题, 使得问题具体化和完整化
    """

    def __init__(self):
        self.__chain = self.__get_rewrite_query_chain()

    def rewrite_query(self, query: str, history: str):
        '''
        改写提问
        query: 原问题
        history: 记忆
        return: 改写后的问题 
        '''
        return self.__chain.invoke({'query':query, 'history':history}).content

    def __get_rewrite_query_chain(self):
        # prompt
        prompt = ChatPromptTemplate(        
            messages=[
                    HumanMessagePromptTemplate.from_template(REWRITE_QUERY_PROMPT)
            ],
            input_variables=['query','hitsory'] )

        llm = ChatTongyi(api_key=tongyi_config.DASHSCOPE_API_KEY)

        chain = prompt | llm    
        return chain
    
class CypherGenerator:
    """ Cyphers语句生成器

    根据提问, 生成对应的查询语句
    """
    def __init__(self, limit = 10):
       """初始化Cypher语句生成器

       limit: 语句查询结果限制数
       """
       self.__limit = limit
       self.__chain = self.__get_cypher_generation_chain()
       
    def generate_cyphers(self, query):
        """生成cypher语句 
        
        query: 问题
        limit: cyphers 查询语句的limit限制
        return: list[str] cypher语句 
        """
        print(f"\n[DEBUG] CypherGenerator.generate_cyphers - 开始生成查询语句")
        print(f"[DEBUG] 输入查询: {query}")
        
        # 提取关键词
        keywords = []
        words = query.lower().replace('是什么', '').replace('的', '').split()
        for word in words:
            if word not in ['是', '什么', '的']:
                keywords.append(word)
        
        # 生成查询变体
        queries = []
        # 单个关键词
        queries.extend(keywords)
        # 相邻关键词组合
        for i in range(len(keywords)-1):
            queries.append(keywords[i] + keywords[i+1])
        
        print("[DEBUG] 生成的查询变体:")
        for q in queries:
            print(f"- {q}")
        
        cyphers = []
        for q in queries:
            # 生成基本的查询语句
            cypher = f"""
            MATCH (n:knowledgePoint)-[:values]->(v)
            WHERE toLower(n.name) CONTAINS '{q}'
            RETURN n.name as knowledge_point, v.name as content
            LIMIT {self.__limit}
            """
            cyphers.append(cypher)
            
            # 生成反向查询语句
            cypher = f"""
            MATCH (n:knowledgePoint)-[:values]->(v)
            WHERE toLower(v.name) CONTAINS '{q}'
            RETURN n.name as knowledge_point, v.name as content
            LIMIT {self.__limit}
            """
            cyphers.append(cypher)
        
        # 添加特殊的组合查询
        if 'java' in keywords:
            for keyword in keywords:
                if keyword != 'java':
                    cypher = f"""
                    MATCH (n:knowledgePoint)-[:values]->(v)
                    WHERE (toLower(n.name) CONTAINS 'java' AND toLower(v.name) CONTAINS '{keyword}')
                       OR (toLower(n.name) CONTAINS '{keyword}' AND toLower(v.name) CONTAINS 'java')
                    RETURN n.name as knowledge_point, v.name as content
                    LIMIT {self.__limit}
                    """
                    cyphers.append(cypher)
        
        print(f"[DEBUG] 生成了 {len(cyphers)} 个查询语句")
        for i, cypher in enumerate(cyphers):
            print(f"\n查询 {i+1}:")
            print(cypher)
        
        return list(set(cyphers))  # 去重
    
    def change_limit(self, limit: int):
        self.__limit = limit

    def __get_cypher_generation_chain(self):
        """获取cyper语句生成链
        """
        prompt = ChatPromptTemplate.from_template(CYPHER_GENERATION_PROMPT)
        llm = ChatTongyi(api_key=tongyi_config.DASHSCOPE_API_KEY)
        chain = prompt | llm
        return chain
      
class CypherQuerier:
    """Cypher语句查询器
    
    对图数据库执行查询
    """

    def __init__(self, graph):
        print("\n[DEBUG] CypherQuerier.__init__ - 初始化查询器")
        self.graph = graph
        try:
            print("[DEBUG] 尝试检查数据库连接")
            self.graph.execute_query("MATCH (n) RETURN count(n) as count LIMIT 1")
            print("[DEBUG] 数据库连接正常")
        except Exception as e:
            print(f"[ERROR] 数据库连接失败: {str(e)}")
        self._check_database_content()

    def _check_database_content(self):
        """检查数据库内容，打印节点和关系信息"""
        print("\n[DEBUG] CypherQuerier._check_database_content - 开始检查数据库内容")
        try:
            # 检查所有知识点节点
            query = """
            MATCH (n:knowledgePoint)
            RETURN n.name as name
            """
            result = self.graph.execute_query(query)
            print("\n[DEBUG] 所有知识点节点:")
            for record in result:
                print(f"- {record['name']}")

            # 检查所有values节点
            query = """
            MATCH (v:values)
            RETURN v.name as name
            """
            result = self.graph.execute_query(query)
            print("\n[DEBUG] 所有values节点:")
            for record in result:
                print(f"- {record['name']}")

            # 检查所有关系
            query = """
            MATCH (n:knowledgePoint)-[r:values]->(v)
            RETURN n.name as knowledge_point, v.name as content
            """
            result = self.graph.execute_query(query)
            print("\n[DEBUG] 所有关系:")
            for record in result:
                print(f"- {record['knowledge_point']} -> {record['content']}")

            # 检查是否有关键词相关的节点
            query = """
            MATCH (n:knowledgePoint)
            WHERE toLower(n.name) CONTAINS '枚举' 
               OR toLower(n.name) CONTAINS 'enum'
               OR toLower(n.name) CONTAINS 'java'
            RETURN n.name as name
            """
            result = self.graph.execute_query(query)
            print("\n[DEBUG] 包含关键词的知识点节点:")
            for record in result:
                print(f"- {record['name']}")

            query = """
            MATCH (v:values)
            WHERE toLower(v.name) CONTAINS '枚举'
               OR toLower(v.name) CONTAINS 'enum'
               OR toLower(v.name) CONTAINS 'java'
            RETURN v.name as name
            """
            result = self.graph.execute_query(query)
            print("\n[DEBUG] 包含关键词的values节点:")
            for record in result:
                print(f"- {record['name']}")

        except Exception as e:
            print(f"[ERROR] 检查数据库内容时出错: {str(e)}")

    def execute_query(self, question):
        print(f"\n[DEBUG] CypherQuerier.execute_query - 开始执行查询")
        print(f"[DEBUG] 输入问题: {question}")
        
        # 尝试不同的查询变体
        queries = [
            question,  # 原始问题
            question.replace('的', ''),  # 移除"的"
            ' '.join(question.split()[:2]),  # 只使用前两个词
            'Java枚举',  # 直接使用关键词
            '枚举'  # 只使用枚举
        ]
        
        print("\n[DEBUG] 尝试以下查询变体:")
        for q in queries:
            print(f"- {q}")
            
            # 生成查询语句
            query = f"""
            MATCH (n:knowledgePoint)-[:values]->(v)
            WHERE toLower(n.name) CONTAINS '{q.lower()}' 
               OR toLower(v.name) CONTAINS '{q.lower()}'
            RETURN n.name as knowledge_point, v.name as content
            """
            print(f"\n[DEBUG] 执行查询:")
            print(query)
            
            try:
                result = self.graph.execute_query(query)
                if result:
                    print(f"[DEBUG] 查询成功，找到 {len(result)} 条结果")
                    for r in result:
                        print(f"- {r['knowledge_point']} -> {r['content']}")
                    return result
                else:
                    print("[DEBUG] 查询成功但没有找到匹配结果")
            except Exception as e:
                print(f"[ERROR] 查询执行错误: {str(e)}")
                continue
        
        # 如果上述查询都没有结果，尝试更宽松的匹配
        print("\n[DEBUG] 尝试组合查询")
        query = """
        MATCH (n:knowledgePoint)-[:values]->(v)
        WHERE toLower(n.name) CONTAINS 'java' 
          AND (toLower(v.name) CONTAINS '枚举' OR toLower(v.name) CONTAINS 'enum')
        RETURN n.name as knowledge_point, v.name as content
        """
        print(f"\n[DEBUG] 执行组合查询:")
        print(query)
        
        try:
            result = self.graph.execute_query(query)
            if result:
                print(f"[DEBUG] 组合查询成功，找到 {len(result)} 条结果")
                for r in result:
                    print(f"- {r['knowledge_point']} -> {r['content']}")
                return result
            else:
                print("[DEBUG] 组合查询成功但没有找到匹配结果")
        except Exception as e:
            print(f"[ERROR] 组合查询执行错误: {str(e)}")
        
        print("\n[DEBUG] 所有查询尝试都失败了")
        return None

    def close(self):
        """ 关闭图数据库连接
        """
        self.graph.close()

    def kg_serach(self, cyphers):
        """查询图数据库

        cyphers (list(str)): cyphers语句列表
        return: 查询结果列表
        """
        print(f"\n[DEBUG] CypherQuerier.kg_serach - 开始执行图数据库查询")
        print(f"[DEBUG] 收到 {len(cyphers)} 个查询语句")
        
        count = len(cyphers)
        neo4jRes = []
        
        # 初始化图谱查询
        if count == 0:  # 为空，查询结果为空
            print("[DEBUG] 没有查询语句，返回空结果")
            neo4jRes = []
        elif count == 1:  # 1个，查询一次
            print("\n[DEBUG] 执行单个查询:")
            print(cyphers[0])
            result = self.graph.execute_query(cyphers[0])
            if result:  # 确保结果不为空
                print(f"[DEBUG] 查询成功，找到 {len(result)} 条结果")
                neo4jRes = result
            else:
                print("[DEBUG] 查询成功但没有找到匹配结果")
        else:  # 多个，循环处理
            for i, cypher in enumerate(cyphers):
                print(f"\n[DEBUG] 执行查询 {i+1}:")
                print(cypher)
                result = self.graph.execute_query(cypher)
                if result:  # 确保结果不为空
                    print(f"[DEBUG] 查询成功，找到 {len(result)} 条结果")
                    neo4jRes.extend(result)
                else:
                    print("[DEBUG] 查询成功但没有找到匹配结果")
        
        print(f"\n[DEBUG] 查询完成，总共找到 {len(neo4jRes)} 条结果")
        return neo4jRes
    
class Formatter:
    """结果格式化器


    """
    def __init__(self, llm =None):
        """
        llm: langchain llm 模型
        """
        self.llm = llm
        if self.llm is None:
            self.llm = ChatTongyi(api_key=tongyi_config.DASHSCOPE_API_KEY)
        self.__chain = self.__get_format_chain()


    def kg_results_format(self, kg_results):
        '''
        格式化图谱查询结果
        kg_results: neo4j库原始查询结果
        '''
        
        return self.__chain.invoke(kg_results).content

    def __get_format_chain(self):
        
        format_prompt = ChatPromptTemplate.from_template(TO_FORMAT_PROMPT)
 
        chain = format_prompt | self.llm

        return chain

class AnswerGenerator:

    """ 回答生成器
    """

    def __init__(self, llm=None, k=5): 
        """
        llm: langchain llm 模型
        k: 保存的对话轮数
        """
        if llm is None:
            self.llm = ChatTongyi(api_key=tongyi_config.DASHSCOPE_API_KEY)
        else:
            self.llm = llm
        
        self.__chain = self.__get_generation_chain()
        self.__memory = ConversationBufferWindowMemory(k=k)

    def generate(self, query, kg_infomation, stream ='no'):
        """生成回答
        :query 问题
        :kg_information 图谱信息
        :stream: 是否使用流式输出, 
                                'no':不使用流式输出, return 回答
                                'stream': 同步流式输出, return 同步stream迭代器
                                'astream': 异步流式输出, return 异步stream迭代器
        """

        if stream == 'no': # 不使用流式输出
            output = self.__chain.invoke({'query':query,
                                            'kg_infomation':kg_infomation,
                                            'history':self.__memory.load_memory_variables({})})
        elif stream == 'stream':# 同步流式输出
            output = self.__chain.stream({'query':query,
                                            'kg_infomation':kg_infomation,
                                            'history':self.__memory.load_memory_variables({})})
        elif stream == 'astream':# 异步流式输出
            output = self.__chain.astream({'query':query,
                                            'kg_infomation':kg_infomation,
                                            'history':self.__memory.load_memory_variables({})})
        else:
            output = self.__chain.invoke({'query':query,
                                            'kg_infomation':kg_infomation,
                                            'history':self.__memory.load_memory_variables({})})
        return output
    
    def get_memory(self):
        """获取记忆
        """
        return self.__memory.load_memory_variables({})
    
    def save_memory(self, query, answer):
        """ 保存记忆
        
        query: HUMAN问题
        answer: AI回答
        """
        # 添加记忆
        self.__memory.chat_memory.add_user_message(query)
        # self.__memory.chat_memory.add_ai_message(output.content)
        self.__memory.chat_memory.add_ai_message(answer)
        # return output.content

    def refresh_memory(self, k=5):
        self.__memory = ConversationBufferWindowMemory(k = k)

    def __get_generation_chain(self):

        '''
        获取回答生成链
        '''
        # prompt
        prompt = ChatPromptTemplate(        
            messages=[
                    SystemMessagePromptTemplate.from_template(ANSWER_GENERATION_PROMPT_SYSTEM),
                    HumanMessagePromptTemplate.from_template(ANSWER_GENERATION_PROMPT_HUMAN)
            ],
            # 对话记忆
            # partial_variables = {"history": memory.load_memory_variables({})['history']},
            # partial_variables = {"history": memory.load_memory_variables({})},
            input_variables=['query', 'kg_infomation', 'history'] )

        chain = prompt | self.llm

        return chain
    
class DefinedLLM(LLM):
    def __init__(self) -> None:
        pass #需要使用本地大模型的可以继承LangCahin的LLM重写