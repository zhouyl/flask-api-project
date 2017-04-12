# -*- coding: utf-8 -*-

import logging
import MySQLdb

from ..helper import *
from warnings import filterwarnings

filterwarnings('error', category=MySQLdb.Warning)
logger = logging.getLogger('mysql')

'''
针对 MySQLdb 进行的二次封装，可根据配置自动实例化数据库连接
'''

class Connection:

    sql = []

    def __init__(self, name):
        self.name = name
        self.connect()

    # 创建 mysql 连接
    def connect(self):
        try:
            conf = config('db').get(self.name)
            if conf is None:
                raise RuntimeError('Invalid mysql connection "%s"' % self.name)

            timezone = conf.get('timezone')
            autocommit = conf.get('autocommit', True)

            # MySQLdb 的连接参数中，没有 autocommit 和 timezone
            if conf.has_key('timezone'):
                del conf['timezone']

            if conf.has_key('autocommit'):
                del conf['autocommit']

            conn = MySQLdb.connect(**conf)

            # 默认打开自动提交
            conn.autocommit(autocommit)

            # 设置当前数据库时区
            if timezone is not None:
                conn.cursor().execute("set time_zone='%s'" % timezone)

            self.conn = conn
            self.cursor = conn.cursor()

            return conn
        except Exception, e:
            logger.error('[%s] %s: %s' % (self.name, e.__class__.__name__, e))
            raise e

    def autocommit(self, flag=True):
        return self.conn.autocommit(flag)

    def begin(self):
        return self.conn.query('BEGIN')

    def commit(self):
        return self.conn.query('COMMIT')

    def rollback(self):
        return self.conn.query('ROLLBACK')

    def close(self):
        return self.conn.close()

    def affected_rows(self):
        return self.conn.affected_rows()

    def insert_id(self):
        return self.conn.insert_id()

    # 执行 SQL 语句
    def execute(self, sql, param=None):
        self.sql.append(sql)

        # 尝试执行 sql 语句，当连接被断开时，自动重连
        def _execute(sql, param):
            try:
                return self.cursor.execute(sql, param)
            except MySQLdb.Warning, w:
                logger.warning('[%s] %s', self.name, w)
            except MySQLdb.Error, e:
                logger.error('[%s] query sql: %s', self.name, re.sub(r'\s+', ' ', sql))
                logger.error('[%s] %s: %s', self.name, e.__class__.__name__, e)

                # 2006: MySQL server has gone away
                # 2013: Lost connection to MySQL server during query
                if e[0] in [2006, 2013]:
                    try:
                        self.connect()
                        logger.info('[%s] try reconnecting success', self.name)
                    except Exception, e:
                        logger.error('[%s] try to reconnect failed: %s', self.name, e)
                        raise e

                    return _execute(sql, param)
                else:
                    raise e

        return _execute(sql, param)

    # 替代数据库记录
    def replace(self, table, data, desql=False):
        columns = ', '.join(map(self.quote, data.keys()))
        values = ', '.join(map(self.quote_val, data.values()))

        sql = 'REPLACE INTO %s (%s) VALUES (%s)' % \
            (self.quote(table), columns, values)

        return sql if desql else self.execute(sql)

    # 写入数据库记录
    def insert(self, table, data, desql=False, ignore=False):
        columns = ', '.join(map(self.quote, data.keys()))
        values = ', '.join(map(self.quote_val, data.values()))

        sql = 'INSERT %sINTO %s (%s) VALUES (%s)' % \
            ('IGNORE ' if ignore else '', self.quote(table), columns, values)

        return sql if desql else self.execute(sql)

    # 批量替代数据库记录
    def multi_replace(self, table, data, desql=False):
        columns = ', '.join(map(self.quote, data[0].keys()))
        values = ''
        for row in data:
            values += '(' + (', '.join(map(self.quote_val, row.values()))) + '),'

        sql = 'REPLACE INTO %s (%s) VALUES %s' % \
            (self.quote(table), columns, values[:-1])

        return sql if desql else self.execute(sql)

    # 批量写入数据库记录
    def multi_insert(self, table, data, desql=False, ignore=False):
        columns = ', '.join(map(self.quote, data[0].keys()))
        values = ''
        for row in data:
            values += '(' + (', '.join(map(self.quote_val, row.values()))) + '),'

        sql = 'INSERT %sINTO %s (%s) VALUES %s' % \
            ('IGNORE ' if ignore else '', self.quote(table), columns, values[:-1])

        return sql if desql else self.execute(sql)

    # 更新数据库记录
    def update(self, table, data, where=None, desql=False):
        parts = []
        for (col, val) in data.iteritems():
            parts.append("%s = %s" % (self.quote(col), self.quote_val(val)))

        sql = 'UPDATE %s SET %s %s' % \
            (self.quote(table), ', '.join(parts), self._where(where))

        return sql if desql else self.execute(sql)

    # 更新或写入数据库记录
    def update_insert(self, table, data, where=None, desql=False):
        if self.count(table, where) > 0:
            return self.update(table, data, where, desql)

        return self.insert(table, data, desql)

    # 删除数据库记录
    def delete(self, table, where=None, desql=False):
        sql = 'DELETE FROM %s %s' % (self.quote(table), self._where(where))

        return sql if desql else self.execute(sql)

    # 统计记录数
    def count(self, table, where=None, column='*', desql=False):
        sql = "SELECT COUNT(%s) FROM %s %s" % \
            (column, table, self._where(where))

        return sql if desql else self.fetch_column(sql, column=0)

    # 消除数据中的非法字符
    def quote_val(self, value):
        if isinstance(value, bool):
            value = int(value)
        elif value is None:
            value = ''
        elif isinstance(value, str) and value.upper() == 'NULL':
            value = ''

        return "'%s'" % MySQLdb.escape_string(str(value))

    # 为字段添加表名定界符
    def quote(self, table):
        return '.'.join(map(lambda x: "`%s`" % x, table.split('.')))

    # 构造 where 查询条件
    def _where(self, where):
        if isinstance(where, list) or isinstance(where, tuple):
            where = ' AND '.join(where)

        return '' if where is None else 'WHERE %s' % str(where)

    # 查询所有结果
    def fetch_all(self, sql, param=None):
        self.execute(sql, param)
        if not self.cursor.rowcount:
            return []

        fields = map(lambda x: x[0], self.cursor.description)

        return [dict(zip(fields, row)) for row in self.cursor.fetchall()]

    # 查询单行结果
    def fetch_row(self, sql, param=None):
        self.execute(sql, param)
        if not self.cursor.rowcount:
            return None

        fields = map(lambda x: x[0], self.cursor.description)

        return dict(zip(fields, self.cursor.fetchone()))

    # 取出第一行指定序号列的结果
    def fetch_column(self, sql, param=None, column=0):
        self.execute(sql, param)
        if not self.cursor.rowcount:
            return None

        row = self.cursor.fetchone()

        return None if column >= len(row) else row[column]

    # 取出第一行第一列的结果
    def fetch_first(self, sql, param=None):
        return self.fetch_column(sql, param, 0)

    '''这是一个数据量的迭代方法，将自动根据 sql 迭代查询数据库
    可为大数据量的查询提供便捷的查询操作，对比模拟的 cursor 具有更好的性能

    可以有效替代以下查询代码：
        cursor.execute(sql)
        while True:
            row = cursor.fetchone()
            if row is None:
                break

    查询参数：
        sql      SELECT 查询语句
        max      最大记录数，默认值为 0，不限制
        limit    每次查询的记录数，默认值 100
        callback 回调函数，每次迭代都会执行一次，当返回 False 时停止迭代

    例如：
        for row in db('crm').iterator(sql, limit=5000):
            print row
    '''
    def iterator(self, sql, max=0, limit=100, callback=None):
        if not re.match(r'^SELECT.+FROM\s+[0-9a-zA-Z,_ ()\'"`]+', sql, re.I | re.S):
            raise ValueError('Invalid query sql "%s"' % sql)

        offset = 0
        index = 0
        results = []

        while True:
            # 根据回调函数判断是否需要停止迭代
            if hasattr(callback, '__call__') and callback(offset, index) is False:
                raise StopIteration

            # 判断是否达到限制的记录数
            if max > 0 and offset >= max:
                raise StopIteration

            if index >= len(results):
                index = 0
                self.execute('%s LIMIT %d OFFSET %d' % (sql, limit, offset))

                if not self.cursor.rowcount:
                    raise StopIteration

                results = [dict(zip(map(lambda x: x[0], self.cursor.description), row))
                           for row in self.cursor.fetchall()]

            offset += 1
            index += 1

            yield results[index-1]
