import requests
import time
from datetime import datetime, timedelta
import config
import users


# 遍历主循环
def traverse_loop():
    print('抢座线程已经启动...')
    try:
        # 轮询用户队列
        while True:
            try:
                # 每1秒查一遍有没有用户
                if not users.waiting_users:
                    time.sleep(1)
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


# 将失败用户移入失败dict中
def move_running_to_fail(user_id, err):
    try:
        if user_id in users.running_users:
            users.fail_users[user_id] = err
            del users.running_users[user_id]
            del users.user_floors[user_id]
            del users.last_check_time[user_id]
    except Exception as err:
        print('将失败用户移入失败dict中时发生错误：')
        print(err)


# 楼层遍历
def traverse_floor(user_id):
    while True:
        try:
            # user_id为空说明该用户抢座结束
            if not user_id:
                return
            # 不在说明用户已经取消抢座
            if user_id not in users.running_users:
                return
            # 前端超过5分钟未向后端发送状态请求即将其踢出
            time_now = datetime.now()
            if user_id in users.last_check_time:
                if (time_now - users.last_check_time[user_id]).seconds > 5 * 60:
                    raise Exception('前端过长时间未响应')
            floors = [f for f in range(2, 6) if f in users.user_floors[user_id]]
            if not floors:
                if user_id in users.running_users:
                    raise Exception('请求预约的楼层数为空')
            for floor in floors:
                res = requests.get(config.urls['floor'].format(floor))
                if res.status_code != requests.codes.ok:
                    raise Exception('向图书馆的网络请求失败')
                res_json = res.json()
                if res_json['status'] != 1:
                    raise Exception('提交信息有误')
                user_id = traverse_area(res_json['data']['list']['childArea'], user_id)
                if not user_id:
                    return
        except Exception as err:
            print('遍历楼层时出错：')
            print(user_id + ':' + str(err))
            move_running_to_fail(user_id, str(err))
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
                raise Exception('寻位错误：向图书馆的网络请求失败')
            res_json = res.json()
            if res_json['status'] != 1:
                raise Exception('寻位错误：提交信息有误')
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
            if not user_id:
                return None
        except Exception as err:
            print('遍历区域时出错：')
            print(user_id + ':' + str(err))
            move_running_to_fail(user_id, str(err))
            return None
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
                if user_id in users.running_users:
                    del users.running_users[user_id]
                    del users.user_floors[user_id]
                    del users.last_check_time[user_id]
                return None
        except Exception as err:
            print('抢座时出错：')
            print(user_id + ':' + str(err))
            move_running_to_fail(user_id, str(err))
            return None
    return user_id


# 移除预约第二天的用户
def del_tmr_running_user(user_id):
    try:
        if user_id in users.tmr_running_users:
            del users.tmr_running_users[user_id]
            del users.tmr_user_floors[user_id]
    except Exception as err:
        print('移除预约第二天的用户时发生错误：')
        print(err)


# 第二天楼层遍历
def tmr_traverse_area(user_id):
    try:
        # user_id为空说明该用户抢座结束
        if not user_id:
            return
        # 不在说明用户已经取消抢座
        if user_id not in users.tmr_running_users:
            return
        floors = [f for f in range(2, 6) if f in users.tmr_user_floors[user_id]]
        if not floors:
            if user_id in users.running_users:
                raise Exception('请求预约的楼层数为空')
        for floor in floors:
            for area in config.areas[floor]:
                # 此请求用于获取segment，即为预约时间代号
                time_now = datetime.now() + timedelta(days=1)
                params = {
                    'day': time_now.strftime('%Y-%m-%d'),
                    'area': area
                }
                res = requests.get(config.urls['area_time'], params=params)
                if res.status_code != requests.codes.ok:
                    raise Exception('寻位错误：向图书馆的网络请求失败')
                res_json = res.json()
                if res_json['status'] != 1:
                    raise Exception('寻位错误：提交信息有误')
                segment = res_json['data']['list'][0]['bookTimeId']
                # 此请求用于获取此区域的所有座位信息
                params = {
                    'area': area,
                    'day': time_now.strftime('%Y-%m-%d'),
                    'startTime': '8:00',
                    'endTime': '22:30'
                }
                res = requests.get(config.urls['area'], params=params)
                if res.status_code != requests.codes.ok:
                    raise Exception('寻位错误：向图书馆的网络请求失败')
                res_json = res.json()
                if res_json['status'] != 1:
                    raise Exception('寻位错误：提交信息有误')
                user_id = traverse_seat(res_json['data']['list'], segment, user_id)
                if not user_id:
                    return None
    except Exception as err:
        print('遍历楼层时出错：')
        print(user_id + ':' + str(err))
        del_tmr_running_user(user_id)
        return


# 明天座位遍历
def tmr_traverse_seat(seats, segment, user_id):
    for seat in seats:
        if not user_id:
            return None
        if user_id not in users.tmr_running_users:
            return None
        try:
            # print(seat['area_name'] + seat['no'])
            # 找到空闲座位,开始抢座
            if seat['status'] == 1:
                payload = {
                    'access_token': users.tmr_running_users[user_id].cookies.get('access_token'),
                    'userid': user_id,
                    'segment': segment,
                    'type': 1
                }
                res = users.tmr_running_users[user_id].post(config.urls['book'].format(seat['id']), data=payload)
                if res.status_code != requests.codes.ok:
                    raise Exception('向图书馆的网络请求失败')
                res_json = res.json()
                if res_json['status'] != 1:
                    raise Exception(res_json['msg'])
                del_tmr_running_user(user_id)
                return None
        except Exception as err:
            print('抢座时出错：')
            print(user_id + ':' + str(err))
            del_tmr_running_user(user_id)
            return None
    return user_id
