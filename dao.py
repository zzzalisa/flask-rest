from flask_sqlalchemy import SQLAlchemy, BaseQuery

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)

def query(cls) -> BaseQuery:  # 声明返回的类型是BaseQuery类型
    return db.session.query(cls)  # cls是传进的类
def queryAll(cls):
    return query(cls).all()
def queryById(cls,id):
    return query(cls).get(int(id))
def add(obj):
    db.session.add(obj)
    db.session.commit()
def delete(obj):
    db.session.delete(obj)
    db.session.commit()
def deleteById(cls,id):
    try:
        obj = queryById(cls,id)
        delete(obj)
        return '删除成功'
    except:
        return '用户不存在'



