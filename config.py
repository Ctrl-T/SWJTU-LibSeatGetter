UA = 'Mozilla/5.0 (Linux; Android 9; MI 6 Build/PKQ1.190118.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) ' \
     'Version/4.0 Chrome/66.0.3359.126 MQQBrowser/6.2 TBS/045008 Mobile Safari/537.36 MMWEBID/2220 ' \
     'MicroMessenger/7.0.8.1540(0x27000834) '

urls = {
    'login': 'http://202.115.72.52/api.php/login',
    'floor': 'http://202.115.72.52/api.php/areas/{}',
    'area_time': 'http://202.115.72.52/api.php/space_time_buckets',
    'area': 'http://202.115.72.52/api.php/spaces_old',
    'book': 'http://202.115.72.52/api.php/spaces/{}/book'
}

floors = [2, 3, 4]

user_fail_chance = 2
