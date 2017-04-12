#!/bin/bash

# uWSGI 服务管理脚本
# 可使用 supervisor 或者 crontab 监控服务

name="Flask uWSGI"

UWSGI_HOME=$(cd "$(dirname "$0")"; cd ..; pwd)
UWSGI_BIN=$UWSGI_HOME/venv/bin/uwsgi
UWSGI_LISTEN=127.0.0.1:8001
UWSGI_CONFIG=$UWSGI_HOME/config/uwsgi.yaml
UWSGI_LOG_FILE=$UWSGI_HOME/logs/uwsgi.$(date +'%Y%m%d').log
UWSGI_PID_FILE=/var/run/dapi-uwsgi.pid

start() {
    $UWSGI_BIN --yaml $UWSGI_CONFIG \
        --socket $UWSGI_LISTEN \
        --chdir $UWSGI_HOME --pidfile $UWSGI_PID_FILE \
        --daemonize $UWSGI_LOG_FILE > /dev/null 2>&1

    echo -e "\033[32m$name running on http://$UWSGI_LISTEN/.\033[0m"

    return 0
}

stop() {
    if status ; then
        pid=`cat "$UWSGI_PID_FILE"`
        echo -e "\033[33mKilling $name (pid $pid) with SIGQUIT.\033[0m"
        kill -QUIT $pid

        # Wait for it to exit.
        for i in 1 2 3 4 5 6 7 8 9 ; do
            echo -e "\033[33mWaiting $name (pid $pid) to die...\033[0m"
            status || break
            sleep 1
        done

        if status ; then
            echo -e "\033[31m$name stop failed; still running.\033[0m"
            return 1 # stop timed out and not forced
        else
            echo -e "\033[32m$name stopped.\033[0m"
        fi
    else
        echo -e "\033[31m$name is not running.\033[0m"
    fi
}

status() {
    if [ -f "$UWSGI_PID_FILE" ] ; then
        pid=`cat "$UWSGI_PID_FILE"`
        if kill -0 $pid > /dev/null 2> /dev/null ; then
            # process by this pid is running.
            # It may not be our pid, but that's what you get with just pidfiles.
            return 0
        else
            return 2 # program is dead but pid file exists
        fi
    else
        return 3 # program is not running
    fi
}

reload() {
    if status ; then
        kill -HUP `cat "$UWSGI_PID_FILE"`
        echo -e "\033[32m$name reloaded.\033[0m"
    else
        echo -e "\033[31m$name is not running.\033[0m"
    fi
}

force_stop() {
    if status ; then
        stop
        status && kill -KILL `cat "$UWSGI_PID_FILE"`
    fi
}

case "$1" in
    start)
        status
        code=$?
        if [ $code -eq 0 ]; then
            echo -e "\033[33m$name is already running.\033[0m"
        else
            start
            code=$?
        fi

        exit $code
        ;;

    stop)
        stop
        ;;

    force-stop)
        force_stop
        ;;

    status)
        status
        code=$?
        if [ $code -eq 0 ] ; then
            echo -e "\033[32m$name is running.\033[0m"
        else
            echo -e "\033[31m$name is not running.\033[0m"
        fi

        exit $code
        ;;

    reload)
        reload ;;

    restart)
        stop && start
        ;;

    *)
        echo "Usage: $0 {start|stop|force-stop|status|reload|restart}" >&2
        exit 3
        ;;
esac

exit $?
