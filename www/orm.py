#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by TaoYuan on 2017/12/28 0028.
# @Link    : http://blog.csdn.net/lftaoyuan
# Github   : https://github.com/seeways
# @Remark  : Python学习群：315857408
import aiomysql
import logging
from aiohttp import web
import asyncio


def log(content, isSQL=False, args=()):
    if isSQL:
        logging.info("SQL:{} \r\n args:{}".format(content, args))
    else:
        logging.info(content)


# 创建连接池
async def create_pool(loop, **kw):
    log("CREATED DATABASE connection pool...")
    global __pool
    __pool = await aiomysql.create_pool(
        host=kw.get("host", "localhost"),  # 主机，默认本地
        port=kw.get("port", 3306),  # 端口号，默认3306
        user=kw["user"],  # 用户名，默认root
        password=kw["password"],  # 密码， 默认无
        db=kw["database"],  # 数据库
        charset=kw.get("charset", "utf8"),  # 字符集
        autocommit=kw.get("autocommit", True),  # 自动提交事务
        maxsize=kw.get("maxsize", 10),  # 最大连接数
        minsize=kw.get("minsize", 1),  # 最小连接数
        loop=loop
    )


"""
1. 使用带参数的sql，是常用的防止SQL注入手段
2. await 调用子协程，并直接获得子协程的结果
3. 传入size，可以获取最多指定数量的记录，否则get all
"""


async def select(sql, args, size=None):
    log(sql, True, args)
    global __pool

    async with __pool.get() as conn:
        try:
            # 获取游标
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # SQL语句的占位符是?  MySQL的占位符是%s，注意替换
                await cur.execute(sql.replace("?", "%s"), args or ())
                if size:
                    rs = await cur.fetchmany(size)
                else:
                    rs = await cur.fetchall()
        except Exception as e:
            rs = []
            log(e)

        log("rows returned:{}".format(len(rs)))
        return rs


# 增删改和查不同
# cursor对象不返回结果集，而是通过rowcount返回结果数。
async def execute(sql, args, autocommit=True):
    log(sql, True, args)

    async with __pool.get() as conn:
        if not autocommit:
            await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql.replace("?", "%s"), args)
                affected = cur.rowcount  # 获取执行个数
            if not autocommit:
                await conn.commit()
        except BaseException:
            if not autocommit:
                await conn.rollback()
            raise
        return affected


# 创建拥有几个占位符的字符串
def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ', '.join(L)


"""
Model从dict继承，所以具备所有dict的功能
而且实现了特殊方法__getattr__()和__setattr__()
所以可以像引用普通字段那样写
>>> user['id']
123
>>> user.id
123
"""


# Field和它的子类
class Field(object):
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return "<{}, {}:{}>".format(self.__class__.__name__, self.column_type, self.name)


class StringField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl="varchar(128)"):
        super().__init__(name, ddl, primary_key, default)


class BooleanField(Field):
    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)


class IntegerField(Field):
    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)


class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)


class TextField(Field):
    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)


# Model只是一个基类
# 需要将具体的子类(如User)的映射信息读出来
# 可以通过通过元类metaclass
class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        # 排除model本身
        if name == "Model":
            return type.__new__(cls, name, bases, attrs)
        # 获取table名称
        tableName = attrs.get("__table__", None) or name
        log("found model:{} (table:{})".format(name, tableName))
        # 获取所有的Field和主键名
        mappings = dict()
        fields = []
        primaryKey = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                log("found mapping: {} ==> {}".format(k, v))
                mappings[k] = v
                if v.primary_key:
                    # find primaryKey
                    if primaryKey:
                        raise RuntimeError("duplicate primary_key for failed: %s" % k)
                    primaryKey = k
                else:
                    fields.append(k)
        if not primaryKey:
            raise RuntimeError("primaryKey not found...")
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda f: "`%s`" % f, fields))
        attrs["__mappings__"] = mappings  # 保存属性和列的映射关系
        attrs["__table__"] = tableName  # 表名
        attrs["__primary_key__"] = primaryKey  # 主键属性名
        attrs["__fields__"] = fields  # 除主键外的属性名
        # # 构造默认的SELECT, INSERT, UPDATE和DELETE语句:
        attrs["__select__"] = "select `%s`, %s from `%s`" % (primaryKey, ", ".join(escaped_fields), tableName)
        attrs["__insert__"] = "insert into `%s` (%s, `%s`) values (%s)" % (
            tableName, ", ".join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs["__update__"] = "update `%s` set %s where `%s`=?" % (
            tableName, ", ".join(map(lambda f: "`%s`=?" % (mappings.get(f).name or f), fields)), primaryKey)
        attrs["__delete__"] = "delete from `%s` where `%s`=?" % (tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)


# 这样，任何继承自Model的类（比如User），会自动通过ModelMetaclass扫描映射关系，并存储到自身的类属性如__table__、__mappings__中。
# 然后，我们往Model类添加class方法，就可以让所有子类调用class方法


# 定义ORM映射的基类
class Model(dict, metaclass=ModelMetaclass):

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug("using default value for {}:{}".format(key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    async def findAll(cls, where=None, args=None, **kw):
        sql = [cls.__select__]
        if where:
            sql.append("where")
            sql.append(where)
        if args is None:
            args = []
        orderBy = kw.get("orderBy", None)
        if orderBy:
            sql.append("order by")
            sql.append(orderBy)
        limit = kw.get("limit", None)
        if limit is not None:
            sql.append("limit")
            if isinstance(limit, int):
                sql.append("?")
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append("?, ?")
                args.extend(limit)
            else:
                raise ValueError("invalid limit value: %s" % str(limit))

        rs = await select(" ".join(sql), args)
        return [cls(**r) for r in rs]

    @classmethod
    async def findNumber(cls, selectField, where=None, args=None):
        sql = ["select %s _num_ from `%s`" % (selectField, cls.__table__)]
        if where:
            sql.append("where")
            sql.append(where)
        rs = await select(" ".join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]["_num_"]

    @classmethod
    async def find(cls, pk):
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            log("failed to insert record: affected rows:{}".format(rows))

    async def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            log('failed to update by primary key: affected rows: %s' % rows)

    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            log('failed to remove by primary key: affected rows: %s' % rows)
