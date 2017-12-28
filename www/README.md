# web目录

## 架构
```
www/					 <-- web目录
|
+- static/               <-- 存放静态文件
|
+- templates/            <-- 存放模板文件
|
+- README.md             <-- 说明文件
```



## 更新日志：

### day01 搭建环境
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
C:\Users\Administrator>mysql --version
mysql  Ver 14.14 Distrib 5.7.17, for Win64 (x86_64)

[mysql 5.7解压缩版安装教程，附无法启动的问题](http://blog.csdn.net/lftaoyuan/article/details/70212232)

- ide

我是用sublime text开发，idea调试的

[关于Python的一些技巧(持续补充)](http://blog.csdn.net/lftaoyuan/article/details/78919437)


### day2 编写Web App骨架

