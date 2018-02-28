#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by TaoYuan on 2018/2/28 0028. 
# @Link    : http://blog.csdn.net/lftaoyuan  
# Github   : https://github.com/seeways
import asyncio
import orm
from models import User, Blog, Comment


@asyncio.coroutine
def test(loop):
    yield from orm.create_pool(loop=loop, user='root', password='123456', database='awesome')
    u = User(name='TaoYuan', email='1876665310@qq.com', passwd='123abc', image='about:blank')
    yield from u.save()


loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()
