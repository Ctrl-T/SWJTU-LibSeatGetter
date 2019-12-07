$(document).ready(function() {
    if (!$.cookie('username')) {
        $('#content').load('login.html')
    } else {
        // 加载“加载”模态框
        $('#loading').load('loading.html', function() {
            $('#loading_modal').modal('show')
        })
        $.ajax({
            url: '/login',
            type: 'POST',
            data: JSON.stringify({
                'username': $.cookie('username'),
                'password': $.cookie('password')
            }),
            contentType: 'application/json;charset=utf-8',
            success: function(data) {
                if (!data['status']) {
                    $('#content').load('welcome.html', function() { $('#welcome_word').text(data['name'] + '，欢迎！') })
                } else {
                    $('#content').load('login.html')
                }
                $('#loading_modal').modal('hide')
            }
        })
    }
    // 加载“关于”模态框
    $('#about').load('about.html', function() {
        $('#about_button').on('click', function() {
            $('#about_modal').modal('show')
        })
    })
})

$(document).on('click', '#login_button', function() {
    var username = String($('#username').val()).trim()
    var password = String($('#password').val()).trim()
    if (!username || !password) {
        $('#warning_info').text('用户名或密码不能为空！')
        return
    }
    // 加载“加载”模态框
    $('#loading').load('loading.html', function() {
        $('#loading_modal').modal('show')
    })
    $.ajax({
        url: '/login',
        type: 'POST',
        data: JSON.stringify({
            'username': username,
            'password': password,
            'remember': $('#remember_me').is(':checked')
        }),
        contentType: 'application/json;charset=utf-8',
        success: function(data) {
            $('#loading_modal').on('shown.bs.modal', function() {
                $('#loading_modal').modal('hide')
            })
            $('#loading_modal').modal('hide')
            $('#loading_modal').on('hidden.bs.modal', function() {
                    if (!data['status']) {
                        $('#content').load('welcome.html', function() { $('#welcome_word').text(data['name'] + '，欢迎！') })
                    } else {
                        switch (data['status']) {
                            case 1:
                                $('#warning_info').text('用户名或密码错误！')
                                break
                            case 2:
                                $('#warning_info').text('网络错误！')
                                break
                            default:
                                $('#warning_info').text('系统错误！')
                                break;
                        }
                    }
                })
                // $('#loading_modal').modal('hide')

        }
    })
})


// 点击退出登录按钮
$(document).on('click', '#logout_button', function() {
    $.ajax({
        url: '/logout',
        type: 'GET',
        success: function(data) {
            if (!data['status']) {
                $('#content').load('login.html')
                for (cookie in $.cookie()) {
                    $.removeCookie(cookie)
                }
            } else {
                switch (data['status']) {
                    case 1:
                        alert('未登录！')
                        break
                    default:
                        $('#warning_info').text('系统错误！')
                        break;
                }
            }
        }
    })
})

var poll
    // 点击抢座按钮
$(document).on('click', '#get_seat_button', function() {
    var floors = new Array()
    if ($('#2_floor').is(":checked")) {
        floors.push(2)
    }
    if ($('#3_floor').is(":checked")) {
        floors.push(3)
    }
    if ($('#4_floor').is(":checked")) {
        floors.push(4)
    }
    if ($('#5_floor').is(":checked")) {
        floors.push(5)
    }
    if (!floors.length) {
        $('#warning_info').text('未选择楼层')
        return
    }
    $.ajax({
        url: '/get_seat',
        type: 'POST',
        data: JSON.stringify({
            'floors': floors
        }),
        contentType: 'application/json;charset=utf-8',
        success: function(data) {
            if (data['status']) {
                switch (data['status']) {
                    case 1:
                        $('#warning_info').text('未登录')
                        break
                    default:
                        $('#warning_info').text('系统错误！')
                        break;
                }
            }
        }
    })

    // ajax轮询，每0.5秒查询抢座状态
    poll = setInterval(function() {
        $('#process_modal').on('hidden.bs.modal', function() {
            clearInterval(poll)
        })
        $.ajax({
            url: '/get_status',
            type: 'GET',
            success: function(data) {
                if (data['status']) {
                    switch (data['status']) {
                        case 0: // 正在抢座中
                            break
                        case 1: // 抢座成功
                            $('#process_modal').modal('hide')
                            $('#process_modal').on('hidden.bs.modal', function() {
                                $('#content').load('success.html', function() {
                                    $('#seat_no b').text(data['data'])
                                })
                            })
                            clearInterval(poll)
                            return
                        case 3: // 已取消抢座
                            $('#process_modal').modal('hide')
                            return
                        default: // 抢座失败
                            $('#process_modal').modal('hide')
                            $('#process_modal').on('hidden.bs.modal', function() {
                                $('#content').load('fail.html', function() {
                                    $('#fail_info').text(data['msg'])
                                })
                            })
                            clearInterval(poll)
                            return
                    }
                }
            }
        })
    }, 500)
})

$(document).on('click', '#cancel_get_seat', function() {
    $.ajax({
        url: '/cancel_get_seat',
        type: 'GET',
        success: function(data) {
            clearInterval(poll)
            if (data['status']) {
                alert(data['msg'])
            }
        }
    })
})

console.log('恭喜你发现这段文字！\n%cUVEgODUwODIzNDc1%c\n使用过程中发现bug或是有新需求欢迎交流！', 'color:#00a1d6', '')