#!/bin/bash

# MySQL数据库连接工具
#
# 可根据 config/db.yaml 中的配置来快速连接指定的数据库
#
# optional arguments:
#   -h, --help     show this help message and exit
#   -b BIN         指定 mysql 的路径，默认为自动查找
#   -c CONNECTION  最数据库连接名称，默认为 default，参考 config/db.yaml

home=$(cd "$(dirname "$0")"; cd ..; pwd)
$home/venv/bin/python $home/db-connector.py $*
