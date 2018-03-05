#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by TaoYuan on 2017/12/29 0029.
# @Link    : http://blog.csdn.net/lftaoyuan
# Github   : https://github.com/seeways
# @Remark  : Python学习群：315857408
from orm import Model, StringField, IntegerField, BooleanField, TextField, FloatField
import time
import uuid


def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)


"""
定义在User类中的__table__、id和name是类的属性，不是实例的属性。
所以，在类级别上定义的属性用来描述User对象和表的映射关系
而实例属性必须通过__init__()方法去初始化，所以两者互不干扰
"""


class User(Model):
    __table__ = "users"
    # id主键 int
    id = StringField(primary_key=True, default=next_id, ddl="varchar(50)")
    # 邮箱
    email = StringField(ddl="varchar(50)")
    # 姓名 text
    name = StringField(ddl="varchar(50)")
    # 密码
    passwd = StringField(ddl="varchar(50)")
    # 是否管理
    admin = BooleanField()
    # 头像
    image = StringField(ddl="varchar(500)")
    # 创建时间
    created_at = FloatField(default=time.time)


class Blog(Model):
    __table__ = 'blogs'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    name = StringField(ddl='varchar(50)')
    summary = StringField(ddl='varchar(200)')
    content = TextField()
    created_at = FloatField(default=time.time)


class Comment(Model):
    __table__ = 'comments'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    blog_id = StringField(ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    content = TextField()
    created_at = FloatField(default=time.time)
