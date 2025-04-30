from sqlalchemy import create_engine, Column, Integer, String, SmallInteger, TIMESTAMP, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.config_info import settings

# 创建数据库连接引擎
DATABASE_URL = f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_IP}:{settings.MYSQL_PORT}/{settings.MYSQL_BASE}"
engine = create_engine(DATABASE_URL)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 定义用户表模型
class User(Base):
    __tablename__ = "user"
    
    user_id = Column(Integer, primary_key=True, autoincrement=True, comment="用户id")
    phone_number = Column(String(20), nullable=False, comment="电话号码")
    password = Column(String(32), nullable=False, comment="密码")
    id_number = Column(String(18), nullable=False, comment="身份证号")
    name = Column(String(20), nullable=False, comment="用户名")
    description = Column(String(255), nullable=True, comment="用户简介")
    gender = Column(SmallInteger, nullable=True, comment="用户性别，0：女，1：男")
    age = Column(SmallInteger, nullable=True, comment="年龄")
    address = Column(String(255), nullable=True, comment="地址")
    wechat = Column(String(50), nullable=True, comment="微信号")
    qq = Column(String(50), nullable=True, comment="qq号")
    status = Column(SmallInteger, nullable=False, default=1, comment="用户状态, 0:禁用,1:启用")
    role_type = Column(SmallInteger, nullable=False, default=0, comment="用户角色, 0:用户,1:管理员")
    create_time = Column(TIMESTAMP, nullable=True, server_default=text("CURRENT_TIMESTAMP"), comment="创建时间")
    update_time = Column(TIMESTAMP, nullable=True, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"), comment="更新时间")

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
