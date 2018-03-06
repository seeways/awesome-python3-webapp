## 说明
1. 这是一个非常简单的项目，真的很简单
2. 接口全都位于www目录下
3. 热部署：`pymonitor.py`
4. markdown支持：`markdown2.py`
5. 

## 主要架构
```
awesome-python3-webapp/
 +- www/                     <-- web目录
 |   |
 |   +- static/               <-- 静态文件
 |   |
 |   +- templates/            <-- 模板文件
 |   |
 |   +- README.md             <-- 说明文件
 |
 +- log/                     <-- 日志目录
 |
 +- conf/                    <-- 配置目录
```


## 三方库

```
# 异步框架aiohttp
pip install aiohttp

# 前端模板引擎jinja2
pip install jinja2

# MySQL的Python异步驱动程序aiomysql(首先装了mysql)
pip install aiomysql

# 监控(可选)
pip install watchdog
```

## 部署

CentOS 7

watchdog和supervisor都是监控工具，这里用supervisor
```
安装程序
yum install nginx supervisor python mysql-server
安装三方库
pip install jinja2 aiomysql aiohttp
```

设置MySQL数据库
```
1. 执行数据库脚本schema.sql(创建数据库和表,文件位于www目录)
mysql -u root -p < schema.sql
2. 修改config_produce.py生产配置
```