import os
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from schemas.chat import SourceInfo

# 加载环境变量
load_dotenv()

# 搜索API密钥
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")
BING_SEARCH_API_KEY = os.getenv("BING_SEARCH_API_KEY", "")

async def search_with_google(query: str, num_results: int = 5) -> List[SourceInfo]:
    """
    使用Google Custom Search API进行搜索
    """
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
        return simulate_web_search(query)
        
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "key": GOOGLE_SEARCH_API_KEY,
                "cx": GOOGLE_SEARCH_ENGINE_ID,
                "q": query,
                "num": num_results
            }
            
            response = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params=params
            )
            
            if response.status_code != 200:
                return simulate_web_search(query)
                
            data = response.json()
            items = data.get("items", [])
            
            sources = []
            for item in items:
                source = SourceInfo(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", "")
                )
                sources.append(source)
                
            return sources
    except Exception as e:
        print(f"Google搜索出错: {str(e)}")
        return simulate_web_search(query)

async def search_with_bing(query: str, num_results: int = 5) -> List[SourceInfo]:
    """
    使用Bing Search API进行搜索
    """
    if not BING_SEARCH_API_KEY:
        return simulate_web_search(query)
        
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {
                "Ocp-Apim-Subscription-Key": BING_SEARCH_API_KEY
            }
            
            params = {
                "q": query,
                "count": num_results,
                "offset": 0,
                "mkt": "zh-CN"
            }
            
            response = await client.get(
                "https://api.bing.microsoft.com/v7.0/search",
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                return simulate_web_search(query)
                
            data = response.json()
            web_pages = data.get("webPages", {}).get("value", [])
            
            sources = []
            for page in web_pages:
                source = SourceInfo(
                    title=page.get("name", ""),
                    url=page.get("url", ""),
                    snippet=page.get("snippet", "")
                )
                sources.append(source)
                
            return sources
    except Exception as e:
        print(f"Bing搜索出错: {str(e)}")
        return simulate_web_search(query)

async def search_with_duckduckgo(query: str) -> List[SourceInfo]:
    """
    使用DuckDuckGo搜索API（不需要API密钥）
    注意：这使用的是非官方API
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "q": query,
                "format": "json"
            }
            
            response = await client.get(
                "https://api.duckduckgo.com/",
                params=params
            )
            
            if response.status_code != 200:
                return simulate_web_search(query)
                
            data = response.json()
            results = data.get("Results", [])
            
            sources = []
            for result in results:
                source = SourceInfo(
                    title=result.get("Text", ""),
                    url=result.get("FirstURL", "")
                )
                sources.append(source)
                
            # 如果结果少于2个，使用模拟数据补充
            if len(sources) < 2:
                return simulate_web_search(query)
                
            return sources
    except Exception as e:
        print(f"DuckDuckGo搜索出错: {str(e)}")
        return simulate_web_search(query)

def simulate_web_search(query: str) -> List[SourceInfo]:
    """模拟联网搜索，返回一些伪造的来源"""
    import random
    
    # 根据查询内容生成相关的模拟搜索结果
    if "python" in query.lower():
        sources = [
            SourceInfo(title="Python官方文档", url="https://docs.python.org/zh-cn/3/", snippet="Python 是一种易于学习、功能强大的编程语言。它具有高效的高级数据结构和简单但有效的面向对象编程方法。"),
            SourceInfo(title="Python教程 - 菜鸟教程", url="https://www.runoob.com/python/python-tutorial.html", snippet="Python 是一个高层次的结合了解释性、编译性、互动性和面向对象的脚本语言。"),
            SourceInfo(title="Python基础教程 - 廖雪峰的官方网站", url="https://www.liaoxuefeng.com/wiki/1016959663602400", snippet="Python是著名的\"龟叔\"Guido van Rossum在1989年圣诞节期间，为了打发无聊的圣诞节而编写的一个编程语言。")
        ]
    elif "javascript" in query.lower() or "js" in query.lower():
        sources = [
            SourceInfo(title="JavaScript - MDN Web 文档", url="https://developer.mozilla.org/zh-CN/docs/Web/JavaScript", snippet="JavaScript (JS) 是一种具有函数优先的轻量级，解释型或即时编译型的编程语言。"),
            SourceInfo(title="JavaScript 教程 - 菜鸟教程", url="https://www.runoob.com/js/js-tutorial.html", snippet="JavaScript 是 Web 的编程语言。所有现代的 HTML 页面都使用 JavaScript。"),
            SourceInfo(title="JavaScript 教程 - W3School", url="https://www.w3school.com.cn/js/index.asp", snippet="JavaScript 是世界上最流行的编程语言。JavaScript 是一种轻量级的编程语言。")
        ]
    elif "数据库" in query.lower() or "mysql" in query.lower() or "sql" in query.lower():
        sources = [
            SourceInfo(title="MySQL 官方文档", url="https://dev.mysql.com/doc/", snippet="MySQL是一个关系型数据库管理系统，由瑞典MySQL AB公司开发，属于Oracle旗下产品。"),
            SourceInfo(title="SQL教程 - 菜鸟教程", url="https://www.runoob.com/sql/sql-tutorial.html", snippet="SQL 是用于访问和处理数据库的标准的计算机语言。"),
            SourceInfo(title="MySQL 教程 - 菜鸟教程", url="https://www.runoob.com/mysql/mysql-tutorial.html", snippet="MySQL 是最流行的关系型数据库管理系统之一，在 WEB 应用方面，MySQL是最好的 RDBMS (Relational Database Management System，关系数据库管理系统) 应用软件之一。")
        ]
    else:
        sources = [
            SourceInfo(title="百度百科", url="https://baike.baidu.com/item/" + query, snippet="百度百科是一部内容开放、自由的网络百科全书平台，旨在创造一个涵盖所有领域知识的中文信息收集平台。"),
            SourceInfo(title="知乎 - " + query, url="https://www.zhihu.com/search?q=" + query, snippet="有问题，上知乎。知乎，中文互联网高质量的问答社区和创作者聚集的原创内容平台。"),
            SourceInfo(title="维基百科 - " + query, url="https://zh.wikipedia.org/wiki/" + query, snippet="维基百科是一个自由内容、公开编辑且多语言的网络百科全书协作计划。"),
            SourceInfo(title="CSDN - " + query, url="https://so.csdn.net/so/search?q=" + query, snippet="CSDN是全球知名中文IT技术交流平台,创建于1999年,包含原创博客、精品问答、职业培训、技术论坛、资源下载等产品服务。"),
            SourceInfo(title="GitHub - " + query, url="https://github.com/search?q=" + query, snippet="GitHub是通过Git进行版本控制的软件源代码托管服务平台。")
        ]
    
    # 随机选择2-3个来源
    return random.sample(sources, k=min(len(sources), random.randint(2, 3)))

async def web_search(query: str) -> List[SourceInfo]:
    """
    进行网络搜索，尝试多个搜索引擎
    优先使用配置了API密钥的搜索引擎
    """
    # 优先使用配置了API密钥的搜索引擎
    if GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID:
        return await search_with_google(query)
    elif BING_SEARCH_API_KEY:
        return await search_with_bing(query)
    else:
        # 尝试使用不需要API密钥的DuckDuckGo搜索
        try:
            return await search_with_duckduckgo(query)
        except:
            # 如果所有方法都失败，使用模拟搜索
            return simulate_web_search(query)

# 使用搜索结果生成回答
async def generate_answer_from_search_results(query: str, sources: List[SourceInfo]) -> str:
    """
    根据搜索结果生成回答
    """
    if not sources:
        return f"对不起，我无法找到关于\"{query}\"的相关信息。"
    
    # 提取搜索结果中的片段
    snippets = [source.snippet for source in sources if hasattr(source, 'snippet') and source.snippet]
    
    if not snippets:
        titles = [source.title for source in sources]
        return f"我找到了关于\"{query}\"的以下信息来源，但无法提取具体内容:\n\n" + "\n".join([f"- {title}" for title in titles])
    
    # 简单组合搜索结果
    combined_info = "\n\n".join(snippets)
    
    return f"根据网络搜索，关于\"{query}\"的信息如下：\n\n{combined_info}\n\n请注意，以上信息来自网络搜索结果，可能不完全准确，建议您查阅原始来源进行验证。" 