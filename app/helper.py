# -*- coding: utf-8 -*-

import os
import sys
import CONST
import time
import datetime
import timelib
import dateutil.parser


def auto_module_init(dirpath):
    '''自动为模块目录生成 __init__.py 的数据

    __all__ = auto_module_init(os.path.dirname(__file__))
    '''
    names = []

    for file in os.listdir(dirpath):
        if file[-3:] == '.py' and file not in ['__init__.py']:
            names.append(file[:-3])

    return names


__config = {}


def config(name, default=None):
    '''快速加载配置文件

    该函数会根据传入的 name 参数，查找 config 目录下的 yaml 配置文件，
    并支持通过路径的方式进行查找，例如：config('db.dbase')
    '''
    import yaml
    global __config

    if name.find('.') == -1:
        parts = []
    else:
        parts = name.split('.')
        name = parts[0]

    def __from_config_dict(data, parts, default):
        '''从 dict 配置中读取数据'''
        for key in parts[1:]:
            if isinstance(data, dict) and data.has_key(key):
                data = data.get(key)
            else:
                return default

        return data

    def __load_config_file(name):
        '''将配置加载到会话缓存中'''
        files = [
            '%s/config/%s/%s.yaml' % (CONST.ROOTPATH, CONST.ENV.lower(), name),
            '%s/config/%s.yaml' % (CONST.ROOTPATH, name)
        ]

        for file in files:
            if os.path.isfile(file):
                return yaml.load(open(file, 'r'))

        # 配置文件不存在
        raise IOError('The configuration file "%s" is not found' % files[-1])

    if not __config.has_key(name):
        __config[name] = __load_config_file(name)

    return __from_config_dict(__config[name], parts, default)


__mysql_connections = {}


def db(name='default', new_instance=False):
    '''根据 config/db.yaml 的配置文件，获取数据库连接

    该方法创建的数据库连接将被缓存
    当参数 new_instance=True 时，将得到一个重新创建的连接
    '''
    from .utils import MySQL
    global __mysql_connections

    if new_instance is True:
        return MySQL.Connection(name)

    if not __mysql_connections.has_key(name):
        __mysql_connections[name] = MySQL.Connection(name)

    return __mysql_connections[name]


__memcache_instance = None


def memcache():
    '''尝试根据配置文件获取 memcache 实例'''
    import memcache
    global __memcache_instance

    if __memcache_instance is None:
        __memcache_instance = memcache.Client(config('cache.memcache'))

    return __memcache_instance


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


def to_timestamp(dtime):
    '''将任意日期/时间类型转换为 timestamp

    dtime: str/timestamp/datetime.datetime
        2017-1-1 00:00:00 +08:00
        2017-1-1 00:00:00 UTC
        2017-1-1 00:00:00
        [datetime.datetime(2017, 1, 1, 0, 0, 0, 0)]
        1483200000.0
    '''
    if isinstance(dtime, str):
        return strtotime(dtime)
    elif isinstance(dtime, datetime.datetime):
        return int(time.mktime(dtime.timetuple()))
    elif isinstance(dtime, (int, long, float)):
        return int(dtime)

    return 0


def to_datetime(dtime, tzinfo=CONST.TZINFO):
    '''将任意日期/时间类型转换为 datetime

    dtime:  str/timestamp/datetime.datetime
    tzinfo: pytz.timezone()
    '''
    if isinstance(dtime, (int, long, float)) and dtime > 0:
        dtime = datetime.datetime.fromtimestamp(dtime, tz=tzinfo)
    elif isinstance(dtime, str):
        dtime = strtodatetime(dtime, tzinfo)

    if isinstance(dtime, datetime.datetime):
        if dtime.tzinfo is None:
            return dtime.replace(tzinfo=tzinfo)

        return dtime.astimezone(tzinfo)

    return None


def strtodatetime(tstr, tzinfo=CONST.TZINFO):
    '''将字符串转换为 datetime

    由于 timelib.strtodatetime 不支持指定时区，因此重写简化该方法
    '''

    # 由于 timelib 不支持时区处理
    # 因此先尝试使用 dateutil.parser 对规范化的日期字符进行处理
    # 当 dateutil.parser 无法进行处理时，再尝试使用 timelib.strtodatetime
    try:
        dtime = dateutil.parser.parse(tstr)
    except Exception:
        dtime = timelib.strtodatetime(tstr)

    if not isinstance(dtime, datetime.datetime):
        raise ValueError("Invalid datetime str '%s'" % tstr)

    if dtime.tzinfo is None:
        return dtime.replace(tzinfo=tzinfo)

    return dtime.astimezone(tzinfo)


def strtotime(tstr):
    '''将字符串转换为 timestamp'''
    return int(time.mktime(strtodatetime(tstr).timetuple()))


def now_datetime(tzinfo=CONST.TZINFO):
    '''根据时区，获取当前时间的 datetime'''
    return datetime.datetime.now(tzinfo)


def localtime():
    '''获取当前时区时间戳'''
    return int(time.mktime(time.localtime()))


def gmtime():
    '''获取当前 GMT 时间戳'''
    return int(time.mktime(time.gmtime()))


def date_format(dtime, format=CONST.DATETIME_FORMAT,
                default=None, tzinfo=CONST.TZINFO):
    '''对任何类型的日期/时间类型进行格式化输出

    相当于 datetime.strftime()，可支持 datetime,timestamp,str类型
    返回结果为 datetime 类型
    '''
    dtime = to_datetime(dtime, tzinfo)

    if not isinstance(dtime, datetime.datetime):
        if default is None:
            raise ValueError('Invalid dtime value')

        return default

    return dtime.strftime(format)


def timestamp_of_day(dtime, daytime='00:00:00', diff_hours=0):
    '''时间处理，获取某天某个时间点的时间戳'''
    dtime = to_datetime(dtime).strftime('%Y-%m-%d ' + daytime)
    dtime = strtodatetime(dtime) - datetime.timedelta(hours=diff_hours)

    return int(time.mktime(dtime.timetuple()))


def __month_diff_days(month_diff):
    '''日期差 = 相差年份（相差月数/12）*365 + 相差年份/4（闰年）+月数*30.5'''
    return month_diff / 12 * 365 + month_diff / 12 / 4 + month_diff % 12 * 30.5


def first_day_of_month(dtime, month_diff=0):
    '''时间处理，获取本月的第一天

    dtime:      str/timestamp/datetime.datetime
    month_diff: int (目标月份与当前相差的月份数)
    '''
    dtime = to_datetime(dtime).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0)
    daysdiff = math.floor(__month_diff_days(month_diff))
    month = dtime + datetime.timedelta(days=daysdiff)

    return month.replace(day=1)


def last_day_of_month(dtime, month_diff=0):
    '''时间处理，获取本月的最后一天

    dtime:      str/timestamp/datetime.datetime
    month_diff: int (目标月份与当前相差的月数)
    '''
    dtime = to_datetime(dtime).replace(
        day=15, hour=0, minute=0, second=0, microsecond=0)
    daysdiff = math.floor(__month_diff_days(month_diff+1))
    nextmonth = dtime + datetime.timedelta(days=daysdiff)

    return nextmonth.replace(day=1) + datetime.timedelta(days=-1)


def fint(value, default=0):
    '''强制转换为 int'''
    return default if value is None else int(value)


def ffloat(value, default=0):
    '''强制转换为 float'''
    return default if value is None else float(value)


def fbool(value, default=False):
    '''强制转换为 bool'''
    return default if value is None else bool(value)


def fstr(value, default=''):
    '''强制转换为 str'''
    return default if value is None else str(value)


def fdict(value, default={}):
    '''强制转换为 dict'''
    return default if value is None else dict(value)


def ftuple(value, default={}):
    '''强制转换为 tuple'''
    return default if value is None else tuple(value)


def flist(value, default={}):
    '''强制转换为 list'''
    return default if value is None else list(value)
