import os
import pymysql
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库连接配置
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "knowledge_query")

def run_migration():
    """添加web_search字段到chat_messages表"""
    print("开始迁移：添加web_search字段...")
    
    try:
        # 使用pymysql直接连接
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4'
        )
        
        try:
            with connection.cursor() as cursor:
                # 检查字段是否已存在
                cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'chat_messages' AND COLUMN_NAME = 'web_search'",
                    (DB_NAME,)
                )
                if cursor.fetchone()[0] == 0:
                    print("添加web_search字段到chat_messages表...")
                    cursor.execute(
                        "ALTER TABLE chat_messages ADD COLUMN web_search BOOLEAN DEFAULT FALSE"
                    )
                    connection.commit()
                    print("字段添加成功！")
                else:
                    print("web_search字段已存在，跳过迁移。")
            
            print("迁移完成！")
        finally:
            connection.close()
            
    except Exception as e:
        print(f"迁移失败: {str(e)}")

if __name__ == "__main__":
    run_migration() 