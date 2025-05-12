from typing import List, Dict, Any
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError, ClientError
import json
from config.config_info import settings
import logging
import asyncio

logger = logging.getLogger(__name__)

class KnowledgeGraph:
    def __init__(self):
        self.driver = None
        self._connect()
        
    def _connect(self):
        """建立数据库连接"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
                max_connection_lifetime=settings.NEO4J_MAX_CONNECTION_LIFETIME,
                max_connection_pool_size=settings.NEO4J_MAX_CONNECTION_POOL_SIZE,
                connection_timeout=settings.NEO4J_CONNECTION_TIMEOUT
            )
            logger.info(f"成功连接到Neo4j数据库: {settings.NEO4J_URI}")
        except ServiceUnavailable as e:
            logger.error(f"Neo4j服务不可用: {str(e)}")
            raise Exception("Neo4j数据库服务未启动或无法访问，请确保数据库服务正在运行。")
        except AuthError as e:
            logger.error(f"Neo4j认证失败: {str(e)}")
            raise Exception("Neo4j数据库认证失败，请检查用户名和密码。")
        except Exception as e:
            logger.error(f"连接Neo4j数据库失败: {str(e)}")
            raise Exception(f"无法连接到Neo4j数据库: {str(e)}")
        
    async def close(self):
        """关闭数据库连接"""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j数据库连接已关闭")
        
    async def execute_query(self, cypher_query: str) -> List[Dict[str, Any]]:
        """
        执行Cypher查询并返回结果
        
        Args:
            cypher_query: Cypher查询语句
            
        Returns:
            List[Dict[str, Any]]: 查询结果
        """
        if not self.driver:
            self._connect()
            
        try:
            async with self.driver.session() as session:
                result = await session.run(cypher_query)
                records = await result.data()
                return records
        except ServiceUnavailable as e:
            logger.error(f"Neo4j服务不可用: {str(e)}")
            raise Exception("Neo4j数据库服务未启动或无法访问，请确保数据库服务正在运行。")
        except ClientError as e:
            logger.error(f"Cypher查询语法错误: {str(e)}")
            raise Exception(f"查询语句有误: {str(e)}")
        except Exception as e:
            logger.error(f"执行Cypher查询失败: {str(e)}")
            raise Exception(f"执行查询时出错: {str(e)}")
            
    async def format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        将查询结果格式化为易读的文本
        
        Args:
            results: 查询结果列表
            
        Returns:
            str: 格式化后的文本
        """
        if not results:
            return "None"
            
        try:
            formatted_text = []
            for record in results:
                # 将每个记录转换为易读的文本
                record_text = []
                for key, value in record.items():
                    if value is None:
                        value = "None"
                    elif isinstance(value, dict):
                        value = json.dumps(value, ensure_ascii=False)
                    record_text.append(f"{key}: {value}")
                formatted_text.append(" | ".join(record_text))
                
            return "\n".join(formatted_text)
        except Exception as e:
            logger.error(f"格式化查询结果失败: {str(e)}")
            return str(results)  # 如果格式化失败，返回原始结果 