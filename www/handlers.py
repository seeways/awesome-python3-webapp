#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by TaoYuan on 2018/3/1 0001.
# @Link    : http://blog.csdn.net/lftaoyuan
# Github   : https://github.com/seeways

"""url handlers, 处理各种URL请求"""
import hashlib
import json
import re
import time
from aiohttp import web
import markdown2
from apis import Page, APIValueError, APIResourceNotFoundError, APIError, APIPermissionError
from config import configs
from logger import logger
from models import User, Comment, Blog, next_id
from web_framework import get, post

_ADMIN_EMAIL = "1876665310@qq.com"

"""
@get('/')
# 制定url是'/'的处理函数为index
async def index(request):
	users = await User.findAll()
	return{
		'__template__': 'test.html',
		'users': users
		#'__template__'指定的模板文件是test.html，其他参数是传递给模板的数据
	}
"""

"""
@get('/api/users')
async def api_get_users(*, page = '1'):
	page_index = get_page_index(page)
	# 获取到要展示的博客页数是第几页
	user_count = await User.findNumber('count(id)')
	# count为MySQL中的聚集函数，用于计算某列的行数
	# user_count代表了有多个用户id
	p = Page(user_count, page_index, page_size = 2)
	# 通过Page类来计算当前页的相关信息, 其实是数据库limit语句中的offset，limit

	if user_count == 0:
		return dict(page = p, users = ())
	else:
		users = await User.findAll(orderBy = 'created_at desc', limit = (p.offset, p.limit))
		# page.offset表示从那一行开始检索，page.limit表示检索多少行
	for u in users:
		u.passwd = '******************'
	return dict(page = p, users = users)
"""

COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')


def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p = 1
    return p


# 把存文本文件转为html格式的文本
def text2html(text):
    lines = map(lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'),
                filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)


# 检测当前用户是不是admin用户
def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()


# 根据用户信息拼接一个cookie字符串
def user2cookie(user, max_age):
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time()) + max_age)
    # 过期时间是当前时间+设置的有效时间
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    # 构建cookie存储的信息字符串
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    # SHA1是一种单向算法，即可以通过原始字符串计算出SHA1结果，但无法通过SHA1结果反推出原始字符串。
    return '-'.join(L)


# 根据cookie字符串，解析出用户相关信息
async def cookie2user(cookie_str):
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            # 如果不是3个元素的话，与我们当初构造sha1字符串时不符，返回None
            return None
        uid, expires, sha1 = L
        # 分别获取到用户id，过期时间和sha1字符串
        if int(expires) < time.time():
            # 如果超时(超过一天)，返回None
            return None
        user = await User.find(uid)
        # 根据用户id(id为primary key)查找库，对比有没有该用户
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        # 根据查到的user的数据构造一个校验sha1字符串
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logger.info('invalid sha1')
            return None

        user.passwd = '*******'
        return user
    except Exception as e:
        logger.exception(e)
        return None


# @get('/')
# async def index(request):
#     summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore ' \
#               'et dolore magna aliqua. '
#     # blogs = await Blog.findAll(orderBy='created_at desc')
#     blogs = [
#         Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
#         Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
#         Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200)
#     ]
#     return {
#         '__template__': 'blogs.html',
#         'blogs': blogs
#     }


@get('/')
async def index(*, page='1'):
    # 获取到要展示的博客页数是第几页
    page_index = get_page_index(page)
    # 查找博客表里的条目数
    num = await Blog.findNumber('count(id)')

    # 如果表里没有条目，则不需要显示
    if (not num) and num == 0:
        logger.info('the type of num is: %s' % type(num))
        blogs = []
    else:
        # 通过Page类来计算当前页的相关信息
        page = Page(num, page_index)

        # 否则，根据计算出来的offset(取的初始条目index)和limit(取的条数)，来取出条目
        blogs = await Blog.findAll(orderBy='created_at desc', limit=(page.offset, page.limit))
    # 返回给浏览器
    return {
        '__template__': 'blogs.html',
        'page': page,
        'blogs': blogs
    }


# -----------------------------------------------------注册register、登录signin、注销signout-----------------------------------

# 注册页面
@get('/register')
async def register():
    return {
        '__template__': 'register.html'
    }


@post('/api/users')
async def api_register_user(*, email, name, passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        # 判断email是否存在，且是否符合规定的正则表达式
        raise APIError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIError('passwd')

    users = await User.findAll('email=?', [email])
    # 查一下库里是否有相同的email地址，如果有的话提示用户email已经被注册过
    if len(users):
        raise APIError('register:failed', 'email', 'Email is already in use.')

    uid = next_id()
    # 生成一个当前要注册用户的唯一uid
    sha1_passwd = '%s:%s' % (uid, passwd)

    admin = False
    if email == _ADMIN_EMAIL:
        admin = True

    # 创建一个用户（密码是通过sha1加密保存）
    user = User(id=uid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),
                image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest(),
                admin=admin)
    # 注意数据库中存储的passwd是经过SHA1计算后的40位Hash字符串，所以服务器端并不知道用户的原始口令。

    await user.save()
    # 保存这个用户到数据库用户表
    logger.info('save user OK')
    r = web.Response()
    # 构建返回信息
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    # 86400代表24小时
    user.passwd = '******'
    # 只把要返回的实例的密码改成'******'，库里的密码依然是正确的，以保证真实的密码不会因返回而暴漏
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8')
    return r


# 登陆页面
@get('/signin')
async def signin():
    return {
        '__template__': 'signin.html'
    }

# 登录状态检查
@post('/api/authenticate')
async def authenticate(*, email, passwd):
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not passwd:
        raise APIValueError('passwd', 'Invalid password.')

    users = await User.findAll('email=?', [email])
    # 根据email在库里查找匹配的用户
    if not len(users):
        raise APIValueError('email', '邮箱不存在')
    user = users[0]
    # 可以理解为加盐
    browser_sha1_passwd = '%s:%s' % (user.id, passwd)
    browser_sha1 = hashlib.sha1(browser_sha1_passwd.encode('utf-8'))

    if user.passwd != browser_sha1.hexdigest():
        raise APIValueError("passwd", "无效密码")

    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '*********'
    # 只把要返回的实例的密码改成'******'，库里的密码依然是正确的，以保证真实的密码不会因返回而暴漏
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8')
    return r


# 登出操作


@get('/signout')
async def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    # 清理掉cookie得用户信息数据
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logger.info('user signed out')
    return r


# -----------------------------------------------------用户管理------------------------------------

@get('/show_all_users')
async def show_all_users():
    # 显示所有的用户
    users = await User.findAll()
    logger.info('to index...')
    # return (404, 'not found')

    return {
        '__template__': 'all_users.html',
        'users': users
    }


@get('/api/users')
async def api_get_users(request):
    # 返回所有的用户信息jason格式
    users = await User.findAll(orderBy='created_at desc')
    logger.info('users = %s and type = %s' % (users, type(users)))
    for u in users:
        u.passwd = '******'
    return dict(users=users)


@get('/manage/users')
async def manage_users(*, page='1'):
    # 查看所有用户
    return {
        '__template__': 'manage_users.html',
        'page_index': get_page_index(page)
    }


# ------------------------------------------博客管理的URL处理函数----------------------------------

@get('/manage/blogs/create')
async def manage_create_blog():
    # 写博客页面
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'action': '/api/blogs'  # 对应HTML页面中VUE的action名字
    }


@get('/manage/blogs')
async def manage_blogs(*, page='1'):
    # 博客管理页面
    return {
        '__template__': "manage_blogs.html",
        'page_index': get_page_index(page)
    }


@post('/api/blogs')
async def api_create_blog(request, *, name, summary, content):
    check_admin(request)
    # 只有管理员可以写博客 ,调用位置：manage_blog_edit.html 22行
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty')

    blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image,
                name=name.strip(), summary=summary.strip(), content=content.strip())
    await blog.save()
    return blog


@get('/api/blogs')
async def api_blogs(*, page='1'):
    # 获取博客信息,调用位置：manage_blogs.html 40行
    '''
	请参考29行的api_get_users函数的注释
	'''
    page_index = get_page_index(page)
    blog_count = await Blog.findNumber('count(id)')
    p = Page(blog_count, page_index)
    if blog_count == 0:
        return dict(page=p, blogs=[])
    blogs = await Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)


@get('/blog/{id}')
async def get_blog(id):
    # 根据博客id查询该博客信息
    blog = await Blog.find(id)
    # 根据博客id查询该条博客的评论
    comments = await Comment.findAll('blog_id=?', [id], orderBy='created_at desc')
    # markdown2是个扩展模块，这里把博客正文和评论套入到markdonw2中
    for c in comments:
        c.html_content = text2html(c.content)
    blog.html_content = markdown2.markdown(blog.content)

    return {
        '__template__': 'blog.html',
        'blog': blog,
        'comments': comments
    }


@get('/api/blogs/{id}')
async def api_get_blog(*, id):
    # 获取某条博客的信息
    blog = await Blog.find(id)
    return blog


@post('/api/blogs/{id}/delete')
async def api_delete_blog(id, request):
    # 删除一条博客
    logger.info("删除博客的博客ID为：%s" % id)
    # 先检查是否是管理员操作，只有管理员才有删除评论权限
    check_admin(request)
    # 查询一下评论id是否有对应的评论
    b = await Blog.find(id)
    # 没有的话抛出错误
    if b is None:
        raise APIResourceNotFoundError('Comment')
    # 有的话删除
    await b.remove()
    return dict(id=id)


@post('/api/blogs/modify')
async def api_modify_blog(request, *, id, name, summary, content):
    # 修改一条博客
    logger.info("修改的博客的博客ID为：%s", id)
    # name，summary,content 不能为空
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty')

    # 获取指定id的blog数据
    blog = await Blog.find(id)
    blog.name = name
    blog.summary = summary
    blog.content = content

    # 保存
    await blog.update()
    return blog


@get('/manage/blogs/modify/{id}')
async def manage_modify_blog(id):
    # 修改博客的页面
    return {
        '__template__': 'manage_blog_modify.html',
        'id': id,
        'action': '/api/blogs/modify'
    }


# ---------------------------------------评论管理--------------------------------------


# 评论管理页面
@get('/manage/')
async def manage():
    return 'redirect:/manage/comments'


@get('/manage/comments')
async def manage_comments(*, page='1'):
    # 查看所有评论
    return {
        '__template__': 'manage_comments.html',
        'page_index': get_page_index(page)
    }


@get('/api/comments')
async def api_comments(*, page='1'):
    # 根据page获取评论，注释可参考 index 函数的注释，不细写了
    page_index = get_page_index(page)
    num = await Comment.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, comments=())
    comments = await Comment.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, comments=comments)


@post('/api/blogs/{id}/comments')
async def api_create_comment(id, request, *, content):
    # 对某个博客发表评论
    user = request.__user__
    # 必须为登陆状态下，评论
    if user is None:
        raise APIPermissionError('content')
    # 评论不能为空
    if not content or not content.strip():
        raise APIValueError('content')
    # 查询一下博客id是否有对应的博客
    blog = await Blog.find(id)
    # 没有的话抛出错误
    if blog is None:
        raise APIResourceNotFoundError('Blog')
    # 构建一条评论数据
    comment = Comment(blog_id=blog.id, user_id=user.id, user_name=user.name,
                      user_image=user.image, content=content.strip())
    # 保存到评论表里
    await comment.save()
    return comment


@post('/api/comments/{id}/delete')
async def api_delete_comments(id, request):
    # 删除某个评论
    logger.info(id)
    # 先检查是否是管理员操作，只有管理员才有删除评论权限
    check_admin(request)
    # 查询一下评论id是否有对应的评论
    c = await Comment.find(id)
    # 没有的话抛出错误
    if c is None:
        raise APIResourceNotFoundError('Comment')
    # 有的话删除
    await c.remove()
    return dict(id=id)
