from flask import Flask, request, make_response
import threading
from apscheduler.schedulers.blocking import BlockingScheduler
from crawler import *

app = Flask(__name__)


# 登录
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        params = {
            'username': data['username'],
            'password': data['password'],
            'from': 'mobile'
        }
        headers = {
            'user-agent': config.UA
        }
        user_session = requests.session()
        res = user_session.get(config.urls['login'], params=params, headers=headers)
        res_json = res.json()
        if res.status_code != requests.codes.ok:
            return {
                'status': 2,
                'msg': '向图书馆的网络请求失败',
            }
        if res_json['status'] != 1:
            return {
                'status': 1,
                'msg': '用户名或密码错误',
            }
        users.tmp_users[data['username']] = user_session
        if 'remember' in data:
            response = make_response({
                'status': 0,
                'msg': '登录成功',
                'name': res_json['data']['list']['name']
            })
            if data['remember']:
                out_date = datetime.today() + timedelta(days=10000)
                response.set_cookie('username', data['username'], expires=out_date)
                response.set_cookie('password', data['password'], expires=out_date)
            else:
                response.set_cookie('username', data['username'])
                response.set_cookie('password', data['password'])
            print(data['username'] + ' - ' + res_json['data']['list']['name'] + '登录成功')
            return response
    except Exception as err:
        print(err)
        return {
            'status': -1,
            'msg': str(err)
        }
    else:
        print(data['username'] + ' - ' + res_json['data']['list']['name'] + '登录成功')
        return {
            'status': 0,
            'msg': '登录成功',
            'name': res_json['data']['list']['name']
        }


# 退出登录
@app.route('/logout', methods=['GET'])
def logout():
    try:
        data = request.cookies
        if users.tmp_users.pop(data['username'], None):
            return {
                'status': 0,
                'msg': '已退出登录'
            }
        else:
            return {
                'status': 1,
                'msg': '未登录，无法退出登录'
            }
    except Exception as err:
        return {
            'status': -1,
            'msg': str(err)
        }


# 开始抢座
@app.route('/get_seat', methods=['POST'])
def get_seat():
    try:
        hour_now = datetime.now().hour
        if hour_now >= 21:
            return {
                'status': 3,
                'msg': '当天web预约已结束，不可预约!'
            }
        if hour_now < 6:
            return {
                'status': 3,
                'msg': '当天web预约未开始，不可预约!'
            }
        data = request.cookies
        floor_data = request.json
        users.user_floors[data['username']] = floor_data['floors']
        if data['username'] in users.tmp_users:
            users.last_check_time[data['username']] = datetime.now()
            users.waiting_users.append(users.tmp_users[data['username']])
            print('用户' + data['username'] + '进入抢座队列')
            del users.tmp_users[data['username']]
            return {
                'status': 0,
                'msg': '已开始抢座'
            }
        else:
            return {
                'status': 1,
                'msg': '未登录'
            }
    except Exception as err:
        print(err)
        return {
            'status': -1,
            'msg': str(err)
        }


# 取消抢座
@app.route('/cancel_get_seat', methods=['GET'])
def cancel_get_seat():
    try:
        data = request.cookies
        for user_session in users.waiting_users:
            if data['username'] == user_session.cookies.get('userid'):
                users.tmp_users[data['username']] = user_session
                users.waiting_users.popleft()
                del users.user_floors[data['username']]
                if data['username'] in users.last_check_time:
                    del users.last_check_time[data['username']]
                return {
                    'status': 0,
                    'msg': '成功取消'
                }
        if data['username'] in users.running_users:
            users.tmp_users[data['username']] = users.running_users[data['username']]
            del users.running_users[data['username']]
            del users.user_floors[data['username']]
            if data['username'] in users.last_check_time:
                del users.last_check_time[data['username']]
            return {
                'status': 0,
                'msg': '成功取消'
            }
        return {
            'status': 1,
            'msg': '用户未点击抢座或已抢座成功'
        }
    except Exception as err:
        return {
            'status': -1,
            'msg': str(err)
        }


# 获取当前抢座状态
@app.route('/get_status', methods=['GET'])
def get_status():
    try:
        data = request.cookies
        if data['username'] in users.tmp_users:
            return {
                'status': 3,
                'msg': '已取消抢座'
            }
        for user_session in users.waiting_users:
            if data['username'] == user_session.cookies.get('userid'):
                users.last_check_time[data['username']] = datetime.now()
                return {
                    'status': 0,
                    'msg': '正在等待'
                }
        if data['username'] in users.running_users:
            users.last_check_time[data['username']] = datetime.now()
            return {
                'status': 0,
                'msg': '正在抢座'
            }
        if data['username'] in users.success_users:
            seat_data = users.success_users.pop(data['username'])
            print(data['username'] + ' 抢座成功')
            return {
                'status': 1,
                'msg': '抢座成功',
                'data': seat_data[0] + '-' + seat_data[1]
            }
        if data['username'] in users.fail_users:
            tem_dic = {
                'status': 2,
                'msg': users.fail_users[data['username']]
            }
            users.fail_users.pop(data['username'])
            return tem_dic
        return {
            'status': 4,
            'msg': '未登录'
        }
    except Exception as err:
        return {
            'status': -1,
            'msg': str(err)
        }


# 每天晚上清空用户列表
def clean_users():
    try:
        print('清理用户中')
        users.tmp_users.clear()
        users.waiting_users.clear()
        users.running_users.clear()
        users.fail_users.clear()
        users.success_users.clear()
        users.user_floors.clear()
        users.last_check_time.clear()
        print('清理用户完成')
    except Exception as err:
        print(str(err))


# 每天早上6点抢第二天的座位
def get_tmr_seat():
    try:
        for user_id in users.tmr_waiting_users:
            users.tmr_running_users[user_id] = users.tmr_waiting_users[user_id]
            del users.tmr_waiting_users[user_id]
            tmr_traverse_area(user_id)
    except Exception as err:
        print(str(err))


# 定时任务
def routine():
    scheduler = BlockingScheduler()
    scheduler.add_job(clean_users, 'cron', hour=0)
    scheduler.add_job(get_tmr_seat, 'cron', hour=6, minute=1)


lib_thread = threading.Thread(target=traverse_loop)
routine_thread = threading.Thread(target=routine)
lib_thread.start()
routine_thread.start()
