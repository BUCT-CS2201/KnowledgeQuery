from typing import List, Dict, Any
import json
from .prompts import CYPHER_GENERATION_SYSTEM_PROMPT
import logging

logger = logging.getLogger(__name__)

class CypherGenerator:
    def __init__(self, llm_client):
        self.llm_client = llm_client
        
    async def generate_cypher(self, question: str) -> str:
        """
        使用大语言模型生成Cypher查询语句
        
        Args:
            question: 用户的问题
            
        Returns:
            str: 生成的Cypher查询语句
        """
        # 添加一些示例查询来帮助模型理解
        examples = """
示例查询：
1. 查找所有文物基本信息：
MATCH (r:CulturalRelic) RETURN r.name, r.description, r.dynasty, r.size, r.type LIMIT 5

2. 查找特定朝代的文物：
MATCH (r:CulturalRelic) WHERE r.dynasty CONTAINS '清' RETURN r.name, r.description, r.dynasty LIMIT 5

3. 查找特定材质的文物：
MATCH (r:CulturalRelic) WHERE r.description CONTAINS '纸本' RETURN r.name, r.description, r.type LIMIT 5

4. 查找特定类型的文物：
MATCH (r:CulturalRelic) WHERE r.type CONTAINS '册页' RETURN r.name, r.description, r.type LIMIT 5

5. 查找特定尺寸的文物：
MATCH (r:CulturalRelic) WHERE r.size CONTAINS '高：3' RETURN r.name, r.description, r.size LIMIT 5

6. 查找不包含特定内容的文物：
MATCH (r:CulturalRelic) WHERE NOT r.description CONTAINS '作者' RETURN r.name, r.description LIMIT 5

7. 查找多个条件的文物：
MATCH (r:CulturalRelic) 
WHERE r.dynasty CONTAINS '清' AND r.description CONTAINS '纸本'
RETURN r.name, r.description, r.dynasty, r.type LIMIT 5

8. 查找特定范围的文物：
MATCH (r:CulturalRelic) 
WHERE r.size CONTAINS '高：3' AND r.size CONTAINS '厘米'
RETURN r.name, r.description, r.size LIMIT 5

9. 查找特定朝代的特定类型文物：
MATCH (r:CulturalRelic) 
WHERE r.dynasty CONTAINS '清' AND r.type CONTAINS '册页'
RETURN r.name, r.description, r.dynasty, r.type LIMIT 5

10. 查找特定朝代的特定材质文物：
MATCH (r:CulturalRelic) 
WHERE r.dynasty CONTAINS '清' AND r.description CONTAINS '纸本'
RETURN r.name, r.description, r.dynasty, r.type LIMIT 5
"""
        
        messages = [
            {"role": "system", "content": CYPHER_GENERATION_SYSTEM_PROMPT + examples},
            {"role": "user", "content": f"请为以下问题生成Cypher查询语句：\n{question}"}
        ]
        
        try:
            response = await self.llm_client.get_response(messages)
            # 提取反引号中的内容
            if "```" in response:
                response = response.split("```")[1].strip()
            logger.info(f"生成的Cypher查询: {response}")
            return response.strip()
        except Exception as e:
            logger.error(f"生成Cypher查询失败: {str(e)}")
            raise Exception(f"生成Cypher查询失败: {str(e)}") 