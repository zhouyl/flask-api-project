# -*- coding: utf-8 -*-

import logging.config

from flask import Flask
from .helper import *

# 设置时区
os.environ['TZ'] = CONST.TIMEZONE
time.tzset()

# 确定编码的正确性
reload(sys)
sys.setdefaultencoding('utf-8')

# 初始化日志配置
logging.config.dictConfig(config('logging'))

# 初始化 Flask
app = Flask(__name__)

# 加载项目配置
for (_k, _v) in config('app.flask').items():
    app.config[_k] = _v


if CONST.PRODUCTION:
    '''错误异常处理，在生产环境下不输出详细的错误信息'''

    @app.errorhandler(404)
    def error_404(error):
        return make_response('The requested URL was not found on the server', 404)

    @app.errorhandler(Exception)
    def error_500(error):
        return make_response(str(error), 500)
