# 一、环境配置

## 1、参考文档

+ virtualenv (<https://virtualenv.pypa.io/en/stable/>)
+ flask (<http://www.pythondoc.com/flask/>)
+ happybase (<https://happybase.readthedocs.io/en/latest/>)

## 2、安装 virtualenv

首先在服务器或开发环境安装 `virtualenv`，在此之前你需要安装 `python2.7`

```
$ pip install virtualenv
```

在 ubuntu 下也可以尝试用以下命令安装

```
$ sudo apt-get install python-virtualenv
```

## 3、安装项目环境及依赖包

```
$ cd my.app/
$ virtualenv --no-site-packages venv
$ venv/bin/pip install -r requirements.txt
```

**如果后续开发过程中，有新增的   packages，请在根目录下运行以下命令**

```
$ venv/bin/pip freeze > requirements.txt
```

## 4、环境配置及项目启动

### 4.1) 开发环境

在开发环境下，直接运行以下命令即可，web 服务将监听在 http://127.0.0.1:5000/：

```
$ venv/bin/python manage.py
```

### 4.2) 生产或测试环境部署

配置 nginx

```
server {
    listen       80;
    server_name  my.app;
    location / {
        include                    uwsgi_params;
        uwsgi_pass                 127.0.0.1:8001;
        uwsgi_param  UWSGI_PYHOME  /data/vhosts/my.app/venv;
        uwsgi_param  UWSGI_CHDIR   /data/vhosts/my.app;
        uwsgi_param  UWSGI_SCRIPT  manage:app;
    }
    access_log  /var/log/nginx/my.app.log  main;
}
```

配置环境识别文件

```
$ touch /etc/env.testing # 测试环境
$ touch /etc/env.production # 生产环境
```

启动 uwsgi 服务

```
$ bash bin/uwsgi.sh start
```

注册 uwsgi 守护进程

可选择两种方式，通过 supervisor 或者 crontab

```
*/10 * * * * /data/vhosts/my.app/bin/uwsgi.sh start
```

supervisor 配置方式请参考：http://supervisord.org/

# 二、开发参考

## 1、目录结构

    ├── app
    │   ├── blueprints      # Blueprint 存放目录
    │   ├── models          # 业务模型存放目录
    │   └── utils           # 项目开发工具包存放目录
    ├── bin                 # 可执行脚本目录
    │   ├── db.sh           # 数据库连接工具
    │   └── uwsgi.sh        # uWSGI 服务管理脚本
    ├── config              # 配置文件目录
    │   ├── production      # 生产环境配置文件目录
    │   └── testing         # 测试环境配置文件目录
    ├── logs                # 日志目录
    ├── venv                # python-virtualenv 生产目录
    ├── db-connector.py     # 数据库连接工具
    └── manage.py           # 项目管理启动脚本

## 2、开发范例

每一个 blueprint 需要指定一个 url 前缀，例如一个用户数据的 api 接口

在 app/blueprints 下创建 user.py

```python
# -*- coding: utf-8 -*-

from ..bootstrap import *
from flask import Blueprint, request
from ..models import user

userbp = Blueprint('user', __name__, url_prefix='/user')

@userbp.route('/')
@userbp.route('/index')
def index():
    return make_response(dict(foo='bar'))

@userbp.route('/profile/<int:user_id>')
def profile(user_id)
    return make_response(user.profile(user_id))

app.register_blueprint(userbp) # 这行一定要放在最后
```

在 app/models 下创建 user.py

```python
# -*- coding: utf-8 -*-

from ..bootstrap import *

def profile(user_id):
    return db('user').fetch_row('select * from users where user_id = %d' % user_id)
```

## 3、调试

可通过浏览器或者 curl 进行调试

```
$ curl -X GET 'http://127.0.0.1:5000/user/index'
```

输出结果

    {
      "message": "ok",
      "code": 200,
      "data": [
        "foo": "bar,
      ],
      "@timestamp": 1491983914,
      "@datetime": "2017-04-12 07:58:34 UTC"
    }

## 4、 统一输出标准

请统一使用 make_response 方法进行数据输出

```python
def make_response(data=None, code=200, message='ok'):
    '''用于构造项目的标准数据输出格式'''
    from flask import jsonify

    return jsonify({
        'code': code,
        'message': message,
        'data': {} if data is None else data,
        '@timestamp': localtime(),
        '@datetime': date_format('now', '%Y-%m-%d %H:%M:%S %Z'),
    })
```

请注意 code 的值，参考 http status 进行错误处理，其中 `600` 之后的代码可用于业务逻辑错误

```
100: CONTINUE
101: SWITCHING_PROTOCOLS
200: OK
201: CREATED
202: ACCEPTED
203: NON_AUTHORITATIVE_INFORMATION
204: NO_CONTENT
205: RESET_CONTENT
206: PARTIAL_CONTENT
207: MULTI_STATUS
300: MULTIPLE_CHOICES
301: MOVED_PERMANENTLY
302: FOUND
303: SEE_OTHER
304: NOT_MODIFIED
305: USE_PROXY
306: RESERVED
307: TEMPORARY_REDIRECT
308: PERMANENT_REDIRECT
400: BAD_REQUEST
401: UNAUTHORIZED
402: PAYMENT_REQUIRED
403: FORBIDDEN
404: NOT_FOUND
405: METHOD_NOT_ALLOWED
406: NOT_ACCEPTABLE
407: PROXY_AUTHENTICATION_REQUIRED
408: REQUEST_TIMEOUT
409: CONFLICT
410: GONE
411: LENGTH_REQUIRED
412: PRECONDITION_FAILED
413: REQUEST_ENTITY_TOO_LARGE
414: REQUEST_URI_TOO_LONG
415: UNSUPPORTED_MEDIA_TYPE
416: REQUESTED_RANGE_NOT_SATISFIABLE
417: EXPECTATION_FAILED
428: PRECONDITION_REQUIRED
429: TOO_MANY_REQUESTS
431: REQUEST_HEADER_FIELDS_TOO_LARGE
444: CONNECTION_CLOSED_WITHOUT_RESPONSE
500: INTERNAL_SERVER_ERROR
501: NOT_IMPLEMENTED
502: BAD_GATEWAY
503: SERVICE_UNAVAILABLE
504: GATEWAY_TIMEOUT
505: HTTP_VERSION_NOT_SUPPORTED
508: LOOP_DETECTED
510: NOT_EXTENDED
511: NETWORK_AUTHENTICATION_REQUIRED
```
