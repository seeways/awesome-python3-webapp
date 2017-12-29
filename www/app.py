#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by TaoYuan on 2017/12/28 0028.
# @Link    : http://blog.csdn.net/lftaoyuan
# Github   : https://github.com/seeways
# @Remark  : Python学习群：315857408
import logging
import asyncio
import os
import json
import time
from datetime import datetime
from aiohttp import web
"""
注意点：
1. index 函数内，添加content_type，否则默认下载
2. 日志级别不要太高
3. 日志中的 http://localhost:9001 通过标准输入，可以直接在控制台点击，默认打开至默认浏览器
"""
logging.basicConfig(level=logging.INFO)  # 日志


def index(request):
    # return response is html,else is download
    return web.Response(body=b"<h1>Awesome</h1>", content_type='text/html')


async def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route("GET", "/", index)  # 主页
    srv = await loop.create_server(app.make_handler(), "", 9001)  # 本地9001端口
    logging.info("server start at http://localhost:9001")
    return srv

if __name__ == '__main__':
    # get EventLoop
    loop = asyncio.get_event_loop()
    # exec coroutine
    loop.run_until_complete(init(loop))
    # run forever   or   close
    loop.run_forever()