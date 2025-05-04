from database.db import Base, engine
from models.user import User
from models.chat import ChatSession, ChatMessage

def init_db():
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    print("数据库表创建成功!")

if __name__ == "__main__":
    init_db() 