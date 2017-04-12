# -*- coding: utf-8 -*-

import os
import sys
import pytz

# 项目运行环境
if os.path.isfile('/etc/env.production'):
    ENV = 'PRODUCTION'
elif os.path.isfile('/etc/env.testing'):
    ENV = 'TESTING'
else:
    ENV = 'DEVELOPMENT'

PRODUCTION = ENV is 'PRODUCTION'
TESTING = ENV is 'TESTING'
DEVELOPMENT = ENV is 'DEVELOPMENT'

# 时区
TIMEZONE = 'UTC'

# 用于 datetime 的默认时区设置
TZINFO = pytz.timezone(TIMEZONE)

# 日期时间格式
DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M:%S'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# 项目根目录
ROOTPATH = os.path.dirname(os.path.dirname(__file__))
