from collections import deque

# 登录但未开始抢座的用户，用dict储存用户名和session
tmp_users = {}
# 正在等待抢座的用户，只储存session
waiting_users = deque()
# 正在抢座的用户，用dict储存用户名和session
running_users = {}
# 成功的用户，储存用户名和座位
success_users = {}
# 失败的用户，用dict储存用户名和出错原因
fail_users = {}
# 存储用户抢座楼层信息
user_floors = {}
# 储存上次查询时间，用dict储存用户名和时间
last_check_time = {}

# 预约后天的用户
tmr_waiting_users = {}
# 正在为明天抢座的用户
tmr_running_users = {}
# 存储明天抢座用户抢座楼层信息
tmr_user_floors = {}

