class CypherQuerier:
    def __init__(self, graph):
        self.graph = graph

    async def execute_query(self, question):
        print(f"\n[DEBUG] CypherQuerier.execute_query - 开始执行查询")
        print(f"[DEBUG] 输入问题: {question}")

        # 博物馆名称转换映射
        museum_name_mappings = {
            '哈佛艺术博物馆': ['Harvard Art Museum', 'Harvard Museum of Art', 'Harvard'],
            '大英博物馆': ['British Museum', 'The British Museum', '大英'],
            '卢浮宫': ['Louvre Museum', 'Musée du Louvre', 'The Louvre'],
            '大都会艺术博物馆': ['Metropolitan Museum of Art', 'The Met', 'Metropolitan'],
            '故宫博物院': ['Palace Museum', 'Forbidden City', '故宫'],
        }

        # 优先处理博物馆文物相关的宽泛问法
        import re
        museum_relics_patterns = [
            r'(介绍|列举|展示|说说|讲讲|给我.*?一些|有哪些|有啥|有何|包含哪些|都有哪些).*?(博物馆).*?(文物|藏品|展品)',
            r'(.*?博物馆).*?(有哪些|有啥|有何|包含哪些|都有哪些|介绍|列举|展示|说说|讲讲|给我.*?一些).*(文物|藏品|展品)',
            r'(.*?博物馆).*?(文物|藏品|展品)'
        ]
        
        for pattern in museum_relics_patterns:
            if re.search(pattern, question):
                # 提取博物馆名
                museum_name = None
                m = re.search(r'(.*?博物馆)', question)
                if m:
                    museum_name = m.group(1).strip()
                else:
                    museum_name = question

                # 获取博物馆名称的所有可能变体
                museum_variants = [museum_name]
                if museum_name in museum_name_mappings:
                    museum_variants.extend(museum_name_mappings[museum_name])
                else:
                    # 生成常见的变体
                    museum_variants.extend([
                        museum_name.replace('博物馆', ''),
                        museum_name.replace('博物馆', ' Museum'),
                        museum_name.replace('博物馆', ' Art Museum'),
                        museum_name.replace('博物馆', ' Museum of Art'),
                    ])

                # 构建查询条件
                where_conditions = []
                for variant in museum_variants:
                    where_conditions.append(f"toLower(m.museum_name) CONTAINS toLower('{variant}')")
                where_clause = " OR ".join(where_conditions)

                # 首先检查博物馆是否存在
                check_museum_query = f"""
                MATCH (m:Museum)
                WHERE {where_clause}
                RETURN m.museum_name, m.description
                """
                print(f"[DEBUG] 检查博物馆是否存在，执行查询: {check_museum_query}")
                museum_result = self.graph.execute_query(check_museum_query)
                
                if not museum_result:
                    return f"【基于知识图谱】未在知识图谱中找到{museum_name}的相关信息。"

                # 如果博物馆存在，查询其文物
                query = f"""
                MATCH (r:CulturalRelic)-[:所在博物馆]->(m:Museum) 
                WHERE {where_clause}
                RETURN r.name as relic_name, r.description as description, r.dynasty as dynasty, \
                       r.type as type, r.size as size, r.material_name as material, m.museum_name as museum_name
                """
                print(f"[DEBUG] 命中博物馆文物宽泛问法，博物馆名: {museum_name}")
                print(f"[DEBUG] 使用的博物馆名称变体: {museum_variants}")
                print(f"[DEBUG] 执行查询: {query}")
                
                result = self.graph.execute_query(query)
                relics_info = []
                for r in result:
                    info = []
                    if r.get('relic_name'):
                        info.append(f"{r['relic_name']}")
                    if r.get('description'):
                        info.append(f"：{r['description']}")
                    if r.get('dynasty'):
                        info.append(f"，{r['dynasty']}时期")
                    if r.get('type'):
                        info.append(f"，属于{r['type']}")
                    if r.get('size'):
                        info.append(f"，尺寸{r['size']}")
                    if r.get('material'):
                        info.append(f"，材质为{r['material']}")
                    relics_info.append(''.join(info))
                
                if relics_info:
                    return f"【基于知识图谱】根据提供的知识图谱信息，{museum_name}的文物包含：\n" + "\n".join(relics_info)
                else:
                    # 如果找到博物馆但无文物，返回博物馆信息
                    museum_info = []
                    for m in museum_result:
                        if m.get('museum_name'):
                            info = [m['museum_name']]
                            if m.get('description'):
                                info.append(f"：{m['description']}")
                            museum_info.append(''.join(info))
                    
                    if museum_info:
                        return f"【基于知识图谱】在知识图谱中找到了{museum_name}（{', '.join(museum_info)}），但未发现相关文物信息。"
                    else:
                        return f"【基于知识图谱】在知识图谱中找到了{museum_name}，但未发现相关文物信息。"

        # 处理特定文物是否属于某博物馆的查询
        if '属于' in question and '博物馆' in question:
            import re
            match = re.search(r'(.*?)属于(.*?博物馆)', question)
            if match:
                relic_name = match.group(1).strip()
                museum_name = match.group(2).strip()
                query = """
                MATCH (r:CulturalRelic)-[:所在博物馆]->(m:Museum)
                WHERE r.name = $relic_name 
                  AND (toLower(m.museum_name) CONTAINS toLower($museum_name)
                       OR toLower(m.museum_name) CONTAINS toLower('British Museum')
                       OR toLower(m.museum_name) CONTAINS toLower('大英'))
                RETURN r.name as relic_name, m.museum_name as museum_name
                LIMIT 5
                """
                result = self.graph.execute_query(query, {
                    "relic_name": relic_name,
                    "museum_name": museum_name
                })
                if result:
                    return f"是的，{relic_name}属于{result[0]['museum_name']}。"
                else:
                    # 知识图谱无结果时，使用大语言模型回答
                    try:
                        prompt = f"""请回答以下关于文物收藏地的问题：
问题：{relic_name}是否属于{museum_name}？

要求：
1. 如果知道这个文物的收藏地，请直接回答
2. 如果不确定具体收藏地，请根据文物名称和博物馆名称推测可能性
3. 回答要简洁专业
4. 如果完全无法推测，请说明无法确定
"""
                        llm_response = await self.llm_client.get_response([
                            {"role": "system", "content": "你是一个专业的文物鉴定专家，请根据文物名称和博物馆名称推测其可能的收藏关系。"},
                            {"role": "user", "content": prompt}
                        ])
                        return llm_response
                    except Exception as e:
                        print(f"[ERROR] 调用大语言模型失败: {str(e)}")
                        return f"根据知识图谱信息，无法确认{relic_name}是否属于{museum_name}。"

        # 处理文物收藏地查询
        elif ('收藏于' in question or '收藏地' in question or '在哪' in question or '在' in question or '哪里' in question) and '博物馆' in question:
            # 例：镂空模纹壶在大英博物馆吗？
            import re
            match = re.search(r'(.*?)[在于](.*?博物馆)', question)
            if match:
                relic = match.group(1).strip()
                museum = match.group(2).strip()
                # 修正引号
                relic = relic.replace(''','"').replace(''','"').replace('"','"').replace('"','"')
                museum = museum.replace(''','"').replace(''','"').replace('"','"').replace('"','"')
                
                query = """
                MATCH (r:CulturalRelic)-[:所在博物馆]->(m:Museum)
                WHERE r.name = $relic AND m.museum_name = $museum
                RETURN r.name as relic_name, m.museum_name as museum_name
                LIMIT 5
                """
                print(f"[DEBUG] 执行博物馆查询: {query}")
                print(f"[DEBUG] 参数: relic={relic}, museum={museum}")
                
                result = self.graph.execute_query(query, {
                    "relic": relic,
                    "museum": museum
                })
                if result:
                    return f"是的，{relic}在{result[0]['museum_name']}。"
                else:
                    # 知识图谱无结果时，使用大语言模型回答
                    try:
                        prompt = f"""请回答以下关于文物收藏地的问题：
问题：{relic}是否在{museum}？

要求：
1. 如果知道这个文物的收藏地，请直接回答
2. 如果不确定具体收藏地，请根据文物名称和博物馆名称推测可能性
3. 回答要简洁专业
4. 如果完全无法推测，请说明无法确定
"""
                        llm_response = await self.llm_client.get_response([
                            {"role": "system", "content": "你是一个专业的文物鉴定专家，请根据文物名称和博物馆名称推测其可能的收藏关系。"},
                            {"role": "user", "content": prompt}
                        ])
                        return llm_response
                    except Exception as e:
                        print(f"[ERROR] 调用大语言模型失败: {str(e)}")
                        return f"根据知识图谱信息，无法确认{relic}是否在{museum}。"
            else:
                name = question.replace('收藏于哪里', '').replace('收藏地', '').replace('在哪', '').replace('在', '').replace('哪里', '').strip()
                # 修正引号
                name = name.replace(''','"').replace(''','"').replace('"','"').replace('"','"')
                
                query = """
                MATCH (r:CulturalRelic)-[:所在博物馆]->(m:Museum) 
                WHERE r.name = $name
                RETURN r.name as relic_name, m.museum_name as museum_name
                LIMIT 5
                """
                print(f"[DEBUG] 执行博物馆查询: {query}")
                print(f"[DEBUG] 参数: name={name}")
                
                result = self.graph.execute_query(query, {"name": name})
                if result:
                    museums = [r['museum_name'] for r in result]
                    return f"{name}在{', '.join(museums)}。"
                else:
                    # 知识图谱无结果时，使用大语言模型回答
                    try:
                        prompt = f"""请回答以下关于文物收藏地的问题：
问题：{name}收藏于哪个博物馆？

要求：
1. 如果知道这个文物的收藏地，请直接回答
2. 如果不确定具体收藏地，请根据文物名称推测可能的收藏地
3. 回答要简洁专业
4. 如果完全无法推测，请说明无法确定
"""
                        llm_response = await self.llm_client.get_response([
                            {"role": "system", "content": "你是一个专业的文物鉴定专家，请根据文物名称推测其可能的收藏地。"},
                            {"role": "user", "content": prompt}
                        ])
                        return llm_response
                    except Exception as e:
                        print(f"[ERROR] 调用大语言模型失败: {str(e)}")
                        return f"根据知识图谱信息，无法确定{name}的收藏地。"

        # 处理特定文物的材质查询
        if '材质' in question:
            import re
            match = re.search(r'(.*?)(的材质|是什么材质|材质)', question)
            if match:
                relic_name = match.group(1).strip()
                # 修正引号
                relic_name = relic_name.replace(''','"').replace(''','"').replace('"','"').replace('"','"')
                # 构建查询，同时检查material_name和description字段
                query = """
                MATCH (r:CulturalRelic)
                WHERE r.name = $relic_name
                   OR toLower(r.name) CONTAINS toLower($relic_name)
                   OR toLower(r.description) CONTAINS toLower($relic_name)
                RETURN r.name as relic_name, 
                       r.material_name as material_name,
                       r.matrials as matrials,
                       r.description as description
                LIMIT 5
                """
                print(f"[DEBUG] 执行文物材质查询: {query}")
                print(f"[DEBUG] 参数: relic_name={relic_name}")
                
                # 使用参数化查询
                result = self.graph.execute_query(query, {"relic_name": relic_name})
                
                if result:
                    relic = result[0]
                    print(f"[DEBUG] 查询结果: {relic}")  # 添加调试输出
                    
                    # 检查材质信息
                    material_info = None
                    
                    # 1. 首先检查material_name字段
                    if relic.get('material_name') and relic['material_name'] != '暂无':
                        material_info = relic['material_name']
                        print(f"[DEBUG] 从material_name字段获取材质信息: {material_info}")
                    
                    # 2. 如果material_name为空，检查matrials字段
                    elif relic.get('matrials') and relic['matrials'] != '暂无':
                        material_info = relic['matrials']
                        print(f"[DEBUG] 从matrials字段获取材质信息: {material_info}")
                    
                    # 3. 如果两个字段都为空，检查description字段
                    elif relic.get('description'):
                        description = relic['description']
                        if len(description) < 50 and not any(char in description for char in ['，', '。', '；']):
                            material_info = description
                            print(f"[DEBUG] 从description字段获取材质信息: {material_info}")

                    # 统一返回 material 字段
                    relic['material'] = material_info

                    # 返回结构化 JSON，便于前端直接读取 material 字段
                    return {
                        "relic_name": relic['relic_name'],
                        "material": material_info,
                        "raw": relic  # 可选，便于调试
                    }
                else:
                    # 知识图谱无结果时，使用大语言模型回答
                    try:
                        # 构建提示词
                        prompt = f"""请回答以下关于文物材质的问题：
问题：{relic_name}的材质是什么？

要求：
1. 如果知道这个文物的材质，请直接回答
2. 如果不确定具体材质，请根据文物名称推测可能的材质
3. 回答要简洁专业
4. 如果完全无法推测，请说明无法确定
"""
                        # 调用大语言模型
                        llm_response = await self.llm_client.get_response([
                            {"role": "system", "content": "你是一个专业的文物鉴定专家，请根据文物名称推测其可能的材质。"},
                            {"role": "user", "content": prompt}
                        ])
                        
                        return {
                            "relic_name": relic_name,
                            "material": llm_response,
                            "source": "llm"  # 标记来源为大语言模型
                        }
                    except Exception as e:
                        print(f"[ERROR] 调用大语言模型失败: {str(e)}")
                        return {
                            "relic_name": relic_name,
                            "material": None,
                            "error": "无法获取材质信息"
                        }

        # 常用问题模板
        if '基本信息' in question:
            name = question.replace('的基本信息是什么', '').replace('的基本信息', '').strip()
            query = f"""
            MATCH (r:CulturalRelic) WHERE r.name = '{name}'
            RETURN r.name, r.description, r.dynasty, r.type, r.size, r.material_name, r.matrials, r.author
            """
            result = self.graph.execute_query(query)
            if result:
                relic = result[0]
                # 检查材质信息
                material_info = None
                if relic.get('matrials') and relic['matrials'] != '暂无':
                    material_info = relic['matrials']
                elif relic.get('material_name'):
                    material_info = relic['material_name']
                elif relic.get('description'):
                    description = relic['description']
                    if len(description) < 50 and not any(char in description for char in ['，', '。', '；']):
                        material_info = description
                relic['material'] = material_info
                return relic
            else:
                return None
        elif '朝代' in question or '年代' in question:
            name = question.replace('的朝代', '').replace('的年代', '').replace('属于哪个朝代', '').strip()
            query = f"""
            MATCH (r:CulturalRelic) WHERE r.name = '{name}'
            RETURN r.name, r.dynasty
            """
        elif '尺寸' in question or '多大' in question:
            name = question.replace('有多大', '').replace('的尺寸', '').strip()
            query = f"""
            MATCH (r:CulturalRelic) WHERE r.name = '{name}'
            RETURN r.name, r.size
            """
        elif '作者' in question or '谁制作' in question:
            name = question.replace('是谁制作的', '').replace('的作者', '').strip()
            query = f"""
            MATCH (r:CulturalRelic) WHERE r.name = '{name}'
            RETURN r.name, r.author
            """
        elif ('收藏于' in question or '收藏地' in question or '在哪' in question or '在' in question or '哪里' in question) and '博物馆' in question:
            # 例：镂空模纹壶在大英博物馆吗？
            import re
            match = re.search(r'(.*?)[在于](.*?博物馆)', question)
            if match:
                relic = match.group(1).strip()
                museum = match.group(2).strip()
                query = f"""
                MATCH (r:CulturalRelic)-[:所在博物馆]->(m:Museum)
                WHERE r.name = '{relic}' AND m.museum_name = '{museum}'
                RETURN r.name as relic_name, m.museum_name as museum_name
                """
            else:
                name = question.replace('收藏于哪里', '').replace('收藏地', '').replace('在哪', '').replace('在', '').replace('哪里', '').strip()
                query = f"""
                MATCH (r:CulturalRelic)-[:所在博物馆]->(m:Museum) WHERE r.name = '{name}'
                RETURN r.name as relic_name, m.museum_name as museum_name
                """
        elif '简介' in question and '博物馆' in question:
            name = question.replace('的简介', '').replace('简介', '').strip()
            query = f"""
            MATCH (m:Museum) WHERE m.museum_name = '{name}'
            RETURN m.museum_name, m.description
            """
        elif ('有哪些文物' in question or '文物' in question) and '博物馆' in question:
            name = question.replace('有哪些文物', '').replace('文物', '').replace('博物馆', '').strip()
            query = f"""
            MATCH (r:CulturalRelic)-[:所在博物馆]->(m:Museum) 
            WHERE m.museum_name CONTAINS '{name}'
            RETURN r.name as relic_name, r.description as description, r.dynasty as dynasty, \
                   r.type as type, r.size as size, r.material_name as material
            """
        elif '图片' in question:
            name = question.replace('的图片有哪些', '').replace('的图片', '').strip()
            query = f"""
            MATCH (r:CulturalRelic)-[:HAS_IMAGE]->(img) WHERE r.name = '{name}'
            RETURN img.img_url
            """
        else:
            queries = [
                question,  # 原始问题
                question.replace('的', ''),  # 移除"的"
                ' '.join(question.split()[:2]),  # 只使用前两个词
            ]
            print("\n[DEBUG] 尝试以下查询变体:")
            for q in queries:
                print(f"- {q}")
                query = f"""
                MATCH (r:CulturalRelic)-[:所在博物馆]->(m:Museum)
                WHERE toLower(r.name) CONTAINS '{q.lower()}' 
                   OR toLower(r.description) CONTAINS '{q.lower()}'
                   OR toLower(m.museum_name) CONTAINS '{q.lower()}'
                   OR toLower(m.description) CONTAINS '{q.lower()}'
                RETURN r.name as relic_name, r.description as description, m.museum_name as museum_name, m.description as museum_description
                UNION
                MATCH (m:Museum)
                WHERE toLower(m.museum_name) CONTAINS '{q.lower()}'
                   OR toLower(m.description) CONTAINS '{q.lower()}'
                RETURN null as relic_name, null as description, m.museum_name as museum_name, m.description as museum_description
                """
                print(f"\n[DEBUG] 执行查询:")
                print(query)
                try:
                    result = self.graph.execute_query(query)
                    if result:
                        print(f"[DEBUG] 查询成功，找到 {len(result)} 条结果")
                        for r in result:
                            if r['relic_name']:
                                print(f"- 文物: {r['relic_name']} -> {r['description']}")
                                print(f"  所在博物馆: {r['museum_name']} -> {r['museum_description']}")
                            else:
                                print(f"- 博物馆: {r['museum_name']} -> {r['museum_description']}")
                        return result
                    else:
                        print("[DEBUG] 查询无结果")
                except Exception as e:
                    print(f"[ERROR] 执行查询时出错: {str(e)}")
            return []

        print(f"\n[DEBUG] 执行常用问题查询:")
        print(query)
        try:
            result = self.graph.execute_query(query)
            if result:
                # 优化：如果是文物-博物馆关系，直接肯定回答
                if '所在博物馆' in query:
                    museums = []
                    for r in result:
                        if r.get('relic_name') and r.get('museum_name'):
                            museums.append(r['museum_name'])
                        elif r.get('r.name') and r.get('m.museum_name'):
                            museums.append(r['m.museum_name'])
                    if museums:
                        relic_name = result[0].get('relic_name') or result[0].get('r.name')
                        return f"{relic_name}在{', '.join(museums)}。"
                # 优化：如果是博物馆文物查询，返回详细信息
                elif '有哪些文物' in question or '文物' in question:
                    relics_info = []
                    for r in result:
                        info = []
                        if r.get('relic_name'):
                            info.append(f"{r['relic_name']}")
                        if r.get('description'):
                            info.append(f"：{r['description']}")
                        if r.get('dynasty'):
                            info.append(f"，{r['dynasty']}时期")
                        if r.get('type'):
                            info.append(f"，属于{r['type']}")
                        if r.get('size'):
                            info.append(f"，尺寸{r['size']}")
                        if r.get('material'):
                            info.append(f"，材质为{r['material']}")
                        relics_info.append(''.join(info))
                    if relics_info:
                        return f"【基于知识图谱】根据提供的知识图谱信息，{name}的文物包含：\n" + "\n".join(relics_info)
                print(f"[DEBUG] 查询成功，找到 {len(result)} 条结果")
                return result
            else:
                print("[DEBUG] 查询无结果")
                return "未查到相关信息，建议访问官网进一步核实。"
        except Exception as e:
            print(f"[ERROR] 执行查询时出错: {str(e)}")
            return "未查到相关信息，建议访问官网进一步核实。" 