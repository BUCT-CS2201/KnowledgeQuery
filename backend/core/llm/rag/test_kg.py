import asyncio
import logging
import sys
import os
from typing import List, Dict

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from core.llm.rag.cypher_generator import CypherGenerator
from core.llm.rag.knowledge_graph import KnowledgeGraph
from config.config_info import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockLLMClient:
    """模拟LLM客户端，用于测试Cypher生成"""
    async def get_response(self, prompt: str) -> str:
        # 根据问题生成对应的Cypher查询
        if "清朝" in prompt:
            return "MATCH (r:CulturalRelic) WHERE r.dynasty CONTAINS '清' RETURN r.name, r.description, r.dynasty LIMIT 5"
        elif "纸质" in prompt:
            return "MATCH (r:CulturalRelic) WHERE r.description CONTAINS '纸本' RETURN r.name, r.description, r.type LIMIT 5"
        elif "册页" in prompt:
            return "MATCH (r:CulturalRelic) WHERE r.type CONTAINS '册页' RETURN r.name, r.description, r.type LIMIT 5"
        elif "尺寸" in prompt:
            return "MATCH (r:CulturalRelic) WHERE r.size CONTAINS '高：3' RETURN r.name, r.description, r.size LIMIT 5"
        return "MATCH (r:CulturalRelic) RETURN r.name, r.description LIMIT 5"

class TestKnowledgeGraph:
    def __init__(self):
        self.kg = KnowledgeGraph()
        self.mock_llm = MockLLMClient()
        self.cypher_generator = CypherGenerator(self.mock_llm)
        
    async def test_connection(self):
        """测试数据库连接"""
        try:
            # 执行一个简单的查询
            query = "MATCH (n) RETURN count(n) as count"
            results = await self.kg.execute_query(query)
            logger.info(f"数据库连接测试成功，节点总数: {results[0]['count']}")
            return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {str(e)}")
            return False
            
    async def test_basic_queries(self):
        """测试基本查询"""
        test_queries = [
            # 测试1：查询所有文物基本信息
            "MATCH (r:CulturalRelic) RETURN r.name, r.description, r.dynasty, r.size, r.type LIMIT 5",
            
            # 测试2：查询特定朝代的文物
            "MATCH (r:CulturalRelic) WHERE r.dynasty CONTAINS '清' RETURN r.name, r.description, r.dynasty LIMIT 5",
            
            # 测试3：查询特定材质的文物（从description中查找）
            "MATCH (r:CulturalRelic) WHERE r.description CONTAINS '纸本' RETURN r.name, r.description, r.type LIMIT 5",
            
            # 测试4：查询特定类型的文物
            "MATCH (r:CulturalRelic) WHERE r.type CONTAINS '册页' RETURN r.name, r.description, r.type LIMIT 5"
        ]
        
        for i, query in enumerate(test_queries, 1):
            try:
                logger.info(f"\n执行测试查询 {i}:")
                logger.info(f"查询语句: {query}")
                results = await self.kg.execute_query(query)
                formatted_results = await self.kg.format_results(results)
                logger.info(f"查询结果:\n{formatted_results}")
            except Exception as e:
                logger.error(f"测试查询 {i} 失败: {str(e)}")
                
    async def test_cypher_generation(self):
        """测试Cypher查询生成"""
        test_questions = [
            "查找清朝的文物",
            "查找所有纸质文物",
            "查找所有册页类型的文物",
            "查找尺寸大于30厘米的文物"
        ]
        
        for question in test_questions:
            try:
                logger.info(f"\n测试问题: {question}")
                # 直接使用mock_llm生成查询
                cypher_query = await self.mock_llm.get_response(question)
                logger.info(f"生成的Cypher查询: {cypher_query}")
                
                # 执行生成的查询
                results = await self.kg.execute_query(cypher_query)
                formatted_results = await self.kg.format_results(results)
                logger.info(f"查询结果:\n{formatted_results}")
            except Exception as e:
                logger.error(f"测试失败: {str(e)}")
                
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始运行知识图谱测试...")
        
        # 测试数据库连接
        if not await self.test_connection():
            logger.error("数据库连接测试失败，终止其他测试")
            return
            
        # 运行基本查询测试
        logger.info("\n=== 运行基本查询测试 ===")
        await self.test_basic_queries()
        
        # 运行Cypher生成测试
        logger.info("\n=== 运行Cypher生成测试 ===")
        await self.test_cypher_generation()
        
        # 关闭数据库连接
        await self.kg.close()
        logger.info("\n测试完成")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(TestKnowledgeGraph().run_all_tests()) 