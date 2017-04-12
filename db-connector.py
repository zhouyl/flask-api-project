# -*- coding: utf-8 -*-

from app.bootstrap import *

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='MySQL数据库连接工具')

    parser.add_argument('-b', action='store', dest='bin', type=str,
                        help='指定 mysql 的路径，默认为自动查找', default=None)

    parser.add_argument('-c', action='store', dest='connection', type=str,
                        help='最数据库连接名称，默认为 default，参考 config/db.yaml', default='default')

    parser.add_argument('-l', action='store_true', dest='list',
                        help='列出所有可用的数据库连接')

    args = parser.parse_args()
    opt = config('db').get(args.connection)

    if args.list:
        print '当前可用的数据库连接有：\n    ' + str(', '.join(config('db').keys()))
        sys.exit()

    if opt is None:
        print '无效的数据库连接名称，请查看 config/db.yaml 配置!!!'
        sys.exit()

    mysql = 'mysql' if args.bin is None else args.bin

    cmd = "%s -u%s -p'%s' -h'%s' -P %s --default-character-set=utf8 %s" % \
        (mysql, opt.get('user'), opt.get('passwd'), opt.get('host'),
            opt.get('port', 3306), opt.get('db', ''))

    print '-' * 80
    print cmd
    print '-' * 80

    os.system(cmd)
