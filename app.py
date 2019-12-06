from flask import Flask, request, make_response
import requests
import json
import threading
import config
import users
from datetime import datetime, timedelta
import time

app = Flask(__name__)


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
                'msg': '登陆失败：向图书馆的网络请求失败',
            }
        if res_json['status'] != 1:
            return {
                'status': 1,
                'msg': '登陆失败：用户名或密码错误',
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
            return response
    except Exception as err:
        print(err)
        return {
            'status': -1,
            'msg': str(err)
        }
    else:
        return {
            'status': 0,
            'msg': '登录成功',
            'name': res_json['data']['list']['name']
        }


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


@app.route('/get_seat', methods=['POST'])
def get_seat():
    try:
        data = request.cookies
        floor_data = request.json
        print(data)
        users.user_floors[data['username']] = floor_data['floors']
        if data['username'] in users.tmp_users:
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


@app.route('/cancel_get_seat', methods=['GET'])
def cancel_get_seat():
    try:
        data = request.cookies
        for user_session in users.waiting_users:
            if data['username'] == user_session.cookies.get('userid'):
                users.tmp_users[data['username']] = user_session
                users.waiting_users.popleft()
                del users.user_floors[data['username']]
                return {
                    'status': 0,
                    'msg': '成功取消'
                }
        if data['username'] in users.running_users:
            users.tmp_users[data['username']] = users.running_users[data['username']]
            del users.running_users[data['username']]
            del users.user_floors[data['username']]
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
                return {
                    'status': 0,
                    'msg': '正在等待'
                }
        if data['username'] in users.running_users:
            return {
                'status': 0,
                'msg': '正在抢座'
            }
        if data['username'] in users.success_users:
            seat_data = users.success_users.pop(data['username'])
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


# 遍历主循环
def traverse_loop():
    print('抢座线程已经启动...')
    try:
        # 轮询用户队列
        while True:
            try:
                # 每0.5秒查一遍有没有用户
                if not users.waiting_users:
                    # print('用户列表为空')
                    # print(users.waiting_users)
                    time.sleep(5)
                    continue
                # 有用户，获取队头用户
                user_session = users.waiting_users.popleft()
                user_id = user_session.cookies.get('userid')
                users.running_users[user_id] = user_session
                print('开始为' + user_id + '抢座')
            except Exception as err:
                print('轮询users时出错：')
                print(str(err))
                continue
            traverse_floor(user_id)
    except Exception as err:
        print('寻座线程崩溃!')
        print(str(err))
        traverse_loop()


# 楼层遍历
def traverse_floor(user_id):
    while True:
        try:
            if not user_id:
                return
            if user_id not in users.running_users:
                return
            floors = [f for f in range(2, 6) if f in users.user_floors[user_id]]
            if not floors:
                if user_id in users.running_users:
                    users.fail_users[user_id] = '请求预约的楼层数为空'
                    del users.running_users[user_id]
                    del users.user_floors[user_id]
                return
            for floor in floors:
                res = requests.get(config.urls['floor'].format(floor))
                if res.status_code != requests.codes.ok:
                    raise Exception('向图书馆的网络请求失败')
                res_json = res.json()
                if res_json['status'] != 1:
                    raise Exception('提交信息有误')
                user_id = traverse_area(res_json['data']['list']['childArea'], user_id)
        except Exception as err:
            print('遍历楼层时出错：')


            print(str(err))
            if user_id in users.running_users:
                users.fail_users[user_id] = err
                del users.running_users[user_id]
                del users.user_floors[user_id]
            return


# 区域遍历
def traverse_area(areas, user_id):
    for area in areas:
        if not user_id:
            return None
        if user_id not in users.running_users:
            return None
        try:
            # 不约考研自习室
            if area['id'] == 24:
                continue
            # 区域满，则直接跳过
            if area['TotalCount'] == area['UnavailableSpace']:
                continue
            # 此请求用于获取segment，即为预约时间代号
            time_now = datetime.now()
            params = {
                'day': time_now.strftime('%Y-%m-%d'),
                'area': area['id']
            }
            res = requests.get(config.urls['area_time'], params=params)
            if res.status_code != requests.codes.ok:
                print('寻位错误：向图书馆的网络请求失败')
                continue
            res_json = res.json()
            if res_json['status'] != 1:
                print('寻位错误：提交信息有误')
                return None
            segment = res_json['data']['list'][0]['bookTimeId']
            # 此请求用于获取此区域的所有座位信息
            params = {
                'area': area['id'],
                'day': time_now.strftime('%Y-%m-%d'),
                'startTime': time_now.strftime('%H:%M'),
                'endTime': '22:30'
            }
            res = requests.get(config.urls['area'], params=params)
            if res.status_code != requests.codes.ok:
                raise Exception('寻位错误：向图书馆的网络请求失败')
            res_json = res.json()
            if res_json['status'] != 1:
                raise Exception('寻位错误：提交信息有误')
            user_id = traverse_seat(res_json['data']['list'], segment, user_id)
        except Exception as err:
            print('遍历区域时出错：')
            print(str(err))
            if user_id in users.running_users:
                users.fail_users[user_id] = err
                del users.running_users[user_id]
                del users.user_floors[user_id]
            continue
    return user_id


# 座位遍历
def traverse_seat(seats, segment, user_id):
    for seat in seats:
        if not user_id:
            return None
        if user_id not in users.running_users:
            return None
        try:
            # print(seat['area_name'] + seat['no'])
            # 找到空闲座位,开始抢座
            if seat['status'] == 1:
                payload = {
                    'access_token': users.running_users[user_id].cookies.get('access_token'),
                    'userid': user_id,
                    'segment': segment,
                    'type': 1
                }
                res = users.running_users[user_id].post(config.urls['book'].format(seat['id']), data=payload)
                if res.status_code != requests.codes.ok:
                    raise Exception('向图书馆的网络请求失败')
                res_json = res.json()
                if res_json['status'] != 1:
                    raise Exception(res_json['msg'])
                # 进入成功用户集合
                users.success_users[user_id] = [seat['area_name'], seat['name']]
                del users.running_users[user_id]
                del users.user_floors[user_id]
                return None
        except Exception as err:
            print('抢座时出错：')
            print(str(err))
            if user_id in users.running_users:
                users.fail_users[user_id] = str(err)
                del users.running_users[user_id]
                del users.user_floors[user_id]
            return None
    return user_id


# 每天晚上清空用户列表
def clean_loop():
    try:
        print('清理线程启动')
        while True:
            cur_time = datetime.now()
            if cur_time.hour == 24:
                print('清理用户中')
                users.tmp_users.clear()
                users.waiting_users.clear()
                users.running_users.clear()
                users.fail_users.clear()
                users.success_users.clear()
                users.user_floors.clear()
                time.sleep(60 * 60 * 20)
                continue
            time.sleep(60 * 30)
    except Exception as err:
        print(str(err))
        clean_loop()


lib_thread = threading.Thread(target=traverse_loop)
clean_thread = threading.Thread(target=clean_loop)
lib_thread.start()
clean_thread.start()
