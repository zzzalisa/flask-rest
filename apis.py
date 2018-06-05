import uuid

import os
from flask import request, session
from flask_restful import Api, Resource, fields, marshal_with, marshal, reqparse
from sqlalchemy import or_
from werkzeug.datastructures import FileStorage

import settings
from models import *
from dao import *

api = Api()  # 给前端提供接口 '/user/'

def init_api(app):
    api.init_app(app)

#创建 Resource 子类
class UserApi(Resource):  # 声明User资源
    #JSON 最常见的用法之一，是从 web 服务器上读取 JSON 数据（作为文件或作为 HttpRequest），
    # 将 JSON 数据转换为 JavaScript 对象，然后在网页中使用该数据。
    def get(self):  # 字典会自动转化为json数据
        val = request.args.get('val')
        if val:
            result = {'state': 'fail', 'msg': '查无数据'}

            # 等值条件查询  搜索用户信息val=id/name/phone【其中一个】  导入sqlalchemy的or_函数
            qs = query(User).filter(or_(User.id == val, User.name == val, User.phone == val))
            if qs.count():
                result['state'] = 'ok'
                result['msg'] = '查询成功'
                result['data'] = qs.first().json  # json转化为字典
            return result

        # 查询,从数据库查询所有的用户
        users = queryAll(User)
        return {'state':'ok',
                'data':[user.json for user in users]}

    # 后端写法
    def post(self):
        # 从上传的form对象中取出name和phone
        name = request.form.get('name')
        phone = request.form.get('phone')
        print(name,phone)

        # 数据存到数据库中
        user=User
        user.name = name
        user.phone = phone
        add(user)

        return {'state':'ok','msg':'添加{}用户成功!'.format(name)}

    def delete(self):
        id = request.args.get('id') # id 是字符串类型
        # user = queryById(User,id)   # 考虑id不存在情况
        # delete(user)  # dao的delete函数

        flag = deleteById(User,id)  # 或者此方法

        return {'state':'ok',
                'flag':flag,
                'msg':'删除{}成功'.format(id)}

    def put(self):
        # 从form的隐藏域中获取id,方便查询id的用户数据进行更新
        id = request.form.get('id')
        user = queryById(User, id)
        # if id:
        user.name = request.form.get('name')
        user.phone = request.form.get('phone')
        add(user)
        return {'state': 'ok', 'msg': '{}更新成功'.format(user.name)}

class ImageApi(Resource):
    img_fields = {'id':fields.Integer,
                  'name':fields.String,
                  'url':fields.String,
                  # 'image_url':fields.String(attribute='url'),  理解功能就可以
                  'size':fields.Integer(default=0)}
    get_out_fields = {
        'state':fields.String(default='ok'),
        'data':fields.Nested(img_fields),
        'size':fields.Integer(default=1)
    }

    # @marshal_with(get_out_fields)
    def get(self):
        id = request.args.get('id')
        if id:
            images = query(Image).filter(Image.id == id).all()
        else:
            images = queryAll(Image)
            data={'data':images,
                'size':len(images)}

            # 向session中存放用户名
            session['login_name']='alisa'

        # 强对象转成输出的字段格式（json格式）
        return marshal(data,self.get_out_fields)

class MusicApi(Resource):
    # 创建request参数的解析器
    parser = reqparse.RequestParser()
    #向解析器中添加请求参数说明
    parser.add_argument('key',dest='name',type=str,required=True,help='必须提供搜索的关键字')
            # key 为前端请求参数，dest=name是args解析后存储的参数
    parser.add_argument('id',type=int,help='请确定id的类型是否为数值型')
    parser.add_argument('tag',action='append',required=True,help='至少提供一个tag标签')
    parser.add_argument('session',location='cookies',required=True,help='cookie中不存在session')


    # 定制输出
    music_fields = {
        'id':fields.Integer,
        'name':fields.String,
        'singer':fields.String,
        'url':fields.String(attribute='mp3_url')
    }
    out_fields = {
        'state':fields.String(default='ok'),
        'msg':fields.String(default='查询成功'),
        'data':fields.Nested(music_fields)
    }

    def get(self):
    #     name = request.args.get('name')  # 按name搜索
    #     if name:
    #         return {'msg':'None'}
    #     else:
    #         return {'msg':'必须提供查询参数'}

        # 通过request 参数解析器,开始解析参数
        # 如果请求参数不能满足要求,则直接返回help
        args = self.parser.parse_args()
        # 从args中读取name请求的参数值
        name = args.get('name')
        tags = args.get('tag')
        # 从args中读取session
        session=args.get('session')
        print('session-->',session)

        musics=query(Music).filter(Music.name.like('%{}%'.format(name)))
        if musics.count():
            return {'data':musics.all()}

        return {'msg':'搜索标签为{}的{}音乐不存在'.format(tags,name)}

class UploadApi(Resource):
    # 验证请求参数是否满足条件
    parser = reqparse.RequestParser()
    parser.add_argument('img',type=FileStorage,required=True,location='files',help='必须提供一个名为img的File表单')

    def post(self):
        # 验证请求参数是否满足
        args = self.parser.parse_args()  # 不满足则抛出help的提示

        # 保存上传文件
        uploadFile:FileStorage  = args.get('img')
        print('上传的文件名:',uploadFile.filename)

        newFileName = str(uuid.uuid4()).replace('-','')
        newFileName+='.'+uploadFile.filename.split('.')[-1]
        uploadFile.save(os.path.join(settings.MEDIA_DIR,newFileName))  #FileStorage类的函数save（）

        return {'msg':'上传成功',
                'path':'/static/uploads/{}'.format(newFileName)}


# 将资源UserApi添加到api对象中【其中包括很多行为方法】并声明uri
api.add_resource(UserApi,'/user/')
api.add_resource(ImageApi,'/images/')
api.add_resource(MusicApi,'/music/')
api.add_resource(UploadApi,'/upload/')