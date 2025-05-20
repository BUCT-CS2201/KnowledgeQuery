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
1. 某博物馆的文物查询：
MATCH (r:CulturalRelic)-[:所在博物馆]->(m:Museum)
WHERE toLower(m.museum_name) CONTAINS toLower('大英博物馆')
   OR toLower(m.museum_name) CONTAINS toLower('British Museum')
   OR toLower(m.museum_name) CONTAINS toLower('大英')
RETURN r.name as relic_name, r.description as description, r.dynasty as dynasty,
       r.type as type, r.size as size, r.material_name as material, m.museum_name as museum_name

2. 某文物的基本信息：
MATCH (r:CulturalRelic) WHERE r.name = '镂空模纹壶' 
RETURN r.name, r.description, r.dynasty, r.type, r.size, r.material_name, r.author

3. 某文物的朝代/年代：
MATCH (r:CulturalRelic) WHERE r.name = '镂空模纹壶' 
RETURN r.name, r.dynasty

4. 某文物的材质：
MATCH (r:CulturalRelic) WHERE r.name = '镂空模纹壶' 
RETURN r.name, r.material_name, r.matrials

5. 某文物的尺寸：
MATCH (r:CulturalRelic) WHERE r.name = '镂空模纹壶' 
RETURN r.name, r.size

6. 某文物的作者：
MATCH (r:CulturalRelic) WHERE r.name = '镂空模纹壶' 
RETURN r.name, r.author

7. 某文物收藏于哪个博物馆：
MATCH (r:CulturalRelic)-[:所在博物馆]->(m:Museum) 
WHERE r.name = '镂空模纹壶'
RETURN r.name, m.museum_name

8. 某博物馆的简介：
MATCH (m:Museum) 
WHERE toLower(m.museum_name) CONTAINS toLower('大英博物馆')
   OR toLower(m.museum_name) CONTAINS toLower('British Museum')
   OR toLower(m.museum_name) CONTAINS toLower('大英')
RETURN m.museum_name, m.description

9. 某朝代的所有文物：
MATCH (r:CulturalRelic) 
WHERE r.dynasty = '清代'
RETURN r.name, r.description, r.dynasty

10. 某类型的所有文物：
MATCH (r:CulturalRelic) 
WHERE r.type = '木版画'
RETURN r.name, r.description, r.type

11. 某材质的所有文物：
MATCH (r:CulturalRelic) 
WHERE r.material_name = '瓷器'
   OR r.matrials = '瓷器'
RETURN r.name, r.description, r.material_name, r.matrials

12. 某博物馆的所有文物（带博物馆信息）：
MATCH (r:CulturalRelic)-[:所在博物馆]->(m:Museum)
WHERE toLower(m.museum_name) CONTAINS toLower('大英博物馆')
   OR toLower(m.museum_name) CONTAINS toLower('British Museum')
   OR toLower(m.museum_name) CONTAINS toLower('大英')
RETURN r.name as relic_name, r.description as description, r.dynasty as dynasty,
       r.type as type, r.size as size, r.material_name as material, m.museum_name as museum_name

13. 某文物的图片：
MATCH (r:CulturalRelic)-[:HAS_IMAGE]->(img) 
WHERE r.name = '镂空模纹壶'
RETURN img.img_url
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