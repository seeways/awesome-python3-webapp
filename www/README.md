# web目录

## 架构
```
www/                     <-- web目录
|
+- static/               <-- 存放静态文件
|
+- templates/            <-- 存放模板文件
|
+- README.md             <-- 说明文件
```



## 更新日志：

### 第一天12.28
#### 搭建环境和框架
- python版本

```
python --version
Python 3.6.3 :: Anaconda custom (64-bit)
```

- 查询三方库是否安装(conda or pip)

```
conda search aiohttp
conda search jinja2
conda search aiomysql
```

- 安装三方库

```
异步框架aiohttp
pip3 install aiohttp

前端模板引擎jinja2
pip3 install jinja2

MySQL的Python异步驱动程序aiomysql(首先装了mysql)
pip3 install aiomysql
```

- 数据库  
```
C:\Users\Administrator>mysql --version
mysql  Ver 14.14 Distrib 5.7.17, for Win64 (x86_64)
```

- [mysql 5.7解压缩版安装教程，附无法启动的问题](http://blog.csdn.net/lftaoyuan/article/details/70212232)

- ide  
    我是用sublime text开发，idea调试的

- [关于Python的一些技巧(持续补充)](http://blog.csdn.net/lftaoyuan/article/details/78919437)


#### 编写Web App骨架
- 可以本地预览的网页(主页)
- local：www/app.py

#### 编写ORM
程序中很多地方的数据都需要存储和获取，所以数据库必不可少

数据库使用MySQL 5.7，以前android，ios都用sqlite，但是不太适合服务器

访问数据库需要创建数据库连接、游标对象，然后执行SQL语句，最后处理异常，清理资源。
这些访问数据库的代码如果分散到各个函数中，势必无法维护，也不利于代码复用。
所以，**先得把增删改查封装起来**

由于Web框架使用了基于asyncio的aiohttp，这是基于协程的异步模型。
在协程中，不能调用普通的同步IO操作，因为所有用户都是由一个线程服务的，
协程的执行速度必须非常快，才能处理大量用户的请求。
而耗时的IO操作不能在协程中以同步的方式调用，否则，等待一个IO操作时，系统无法响应任何其他用户。

这就是异步编程的一个原则：一旦决定使用异步，则系统每一层都必须是异步，“开弓没有回头箭”。

幸运的是aiomysql为MySQL数据库提供了异步IO的驱动。

