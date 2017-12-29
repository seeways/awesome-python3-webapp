#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by TaoYuan on 2017/12/29 0029.
# @Link    : http://blog.csdn.net/lftaoyuan
# Github   : https://github.com/seeways
# @Remark  : Python学习群：315857408
from orm import Model, StringField, IntegerField
import asyncio
import aiomysql
"""
定义在User类中的__table__、id和name是类的属性，不是实例的属性。
所以，在类级别上定义的属性用来描述User对象和表的映射关系
而实例属性必须通过__init__()方法去初始化，所以两者互不干扰
"""
class User(Model):
    __table__ = "users"
    # id主键 int
    id = IntegerField(primary_key=True)
    # 姓名 text
    name = StringField()

# 创建实例
# user = User(id=123, name="TaoYuan")
# # 存入数据库
# user.insert()
# # 查询所有user对象
# # users = User.findAll()
# user = await User.find("123")

