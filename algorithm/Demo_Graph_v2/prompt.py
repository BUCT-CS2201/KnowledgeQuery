# Neo4j 图数据库模式定义
SCHEMA = """
Node: knowledgePoint: name (STRING)
Node: values: name (STRING)

Relationship: (:knowledgePoint)-[:values]->(:values)
"""

# 基础系统提示信息
PRE_MSG = f"""   
System: 您的任务是将关于 Neo4j 数据库内容的问题转换为 Cypher 查询语句。

规则：
1. 仅使用提供的关系类型和属性
2. 不要使用未在 schema 中定义的关系类型或属性
3. 如果无法基于提供的 schema 生成 Cypher 语句，向用户解释原因
4. 每个查询必须返回结果
5. 生成的 Cypher 语句必须严格遵循 schema 中定义的关系和属性
6. 注意关系箭头的方向，不要违反规则
7. 内容存储在 values 节点的 name 属性中

数据库模式：
{SCHEMA}
"""

# Cypher 查询生成提示
CYPHER_GENERATION_PROMPT = PRE_MSG + """
问题: '{query}'

生成规则：
1. 根据问题数量生成相应数量的查询语句
2. 不要包含任何解释或歉意
3. 不要使用 WHERE ... IN ... 语法
4. 只返回 Cypher 查询语句
5. 每个查询都要添加 LIMIT {limit}
6. 多个查询语句使用 *** 分隔，每个查询必须是完整的独立语句
7. 用反引号(```)包裹整个查询结果
8. 如果无法生成符合规则的查询，返回 MATCH (n) RETURN n LIMIT 0
9. 对于两个实体之间的查询，最多生成三条最相关的查询语句
10. 查询知识点内容时，同时获取其关联的 values 节点的内容

格式要求：
1. 使用单引号(')表示字符串
2. 节点标签和属性之间必须有空格，如：(n:Label {{prop: 'value'}})
3. 双向关系使用：MATCH (a)-[r1:REL_TYPE]->(b)<-[r2:REL_TYPE]-(a)
4. 不要使用 <-[:REL_TYPE]-> 这样的双向箭头语法

示例格式：
```
MATCH (n:knowledgePoint)-[:values]->(v)
WHERE n.name CONTAINS 'Java枚举'
RETURN n.name as knowledge_point, v.name as content LIMIT 10
```
"""

EXAMPLES = """
Example 1: Find what Java枚举 is
MATCH (n:knowledgePoint)-[r:values]->(v)
WHERE n.name CONTAINS 'Java枚举' OR v.name CONTAINS 'Java枚举'
RETURN n.name, v.name

Example 2: Find information about Java集合
MATCH (n:knowledgePoint)-[r:values]->(v)
WHERE n.name CONTAINS 'Java集合' OR v.name CONTAINS 'Java集合'
RETURN n.name, v.name

Example 3: Find what ArrayList is
MATCH (n:knowledgePoint)-[r:values]->(v)
WHERE n.name CONTAINS 'ArrayList' OR v.name CONTAINS 'ArrayList'
RETURN n.name, v.name
"""

# 查询结果格式化提示
TO_FORMAT_PROMPT = """
我会给你图谱查询返回的结果，请你重新排版其中信息，使它美观。
说明：如果查询结果为空，返回"None"。

查询结果：{kg_results}
"""

# 答案生成提示
ANSWER_GENERATION_PROMPT_SYSTEM = """
已知对话历史：{history}
"""

ANSWER_GENERATION_PROMPT_HUMAN = """
问题："{query}"
知识图谱返回信息：{kg_infomation}

请先考虑信息，再结合自身能力和知识回答问题。

回答要求：
1. 若知识图谱信息为 None，以"【AI回答】"开头
2. 若知识图谱信息帮助很小，以"【AI回答】"开头
3. 若使用了知识图谱信息，以"【基于知识图谱】"开头
4. 不需说明信息来源于人类
5. 必须在开头标注信息来源
6. 必须使用中文方括号【】
7. 标注必须在回答最开头
8. 标注后换行再开始回答
"""

# 问题改写提示
REWRITE_QUERY_PROMPT = """
根据对话历史对问题进行改写。

记忆：{history}
问题：{query}

改写规则：
1. 保持问题数量不变
2. 无记忆或记忆为空时直接返回原问题
3. 将指代词替换为具体内容
4. 考虑上下文关系进行适当扩展
5. 保持原意不变
6. 改写幅度适中
7. 无法改写的指代词保持原样
8. 直接返回改写结果，不需要其他说明

指代词处理示例：
- "这首歌" -> "XXX"（上文提到的具体歌名）
- "这首歌" -> "YYY的XXX"（考虑作者关系）
- "这个女人" -> "AAA的妻子BBB"（考虑关系）
- "这些XX" -> 展开为具体项目列表
"""

# Schema 格式化提示
REFORMATTED_SCHEMA = """
请按以下格式重新组织图数据库关系和节点信息：

节点格式：
Entity: property1 (TYPE), property2 (TYPE)

关系格式：
(:EntityA)-[:RELATION_TYPE]->(:EntityB)

关系属性格式：
RELATION_TYPE: property (TYPE)

要求：
1. 每个节点占一行
2. 不使用花括号
3. 只返回格式化后的数据
4. 减少换行
"""
