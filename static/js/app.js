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
                    $('#content').load('welcome.html', function() { ShowWelcome() })
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
            'password': password
        }),
        contentType: 'application/json;charset=utf-8',
        success: function(data) {
            $('#loading_modal').on('shown.bs.modal', function() {
                $('#loading_modal').modal('hide')
            })
            $('#loading_modal').modal('hide')
            $('#loading_modal').on('hidden.bs.modal', function() {
                    if (!data['status']) {
                        if ($('#remember_me').is(':checked')) {
                            $.cookie('username', $('#username').val(), {
                                expires: 365
                            })
                            $.cookie('password', $('#password').val(), {
                                expires: 365
                            })
                            $.cookie('name', data['name'], {
                                expires: 365
                            })
                        } else {
                            $.cookie('username', $('#username').val())
                            $.cookie('password', $('#password').val())
                            $.cookie('name', data['name'])
                        }
                        $('#content').load('welcome.html', function() { ShowWelcome() })
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

function ShowWelcome() {
    $('#welcome_word').text($.cookie('name') + '，欢迎！')
    $('centralModalSm').show()
}


// 点击退出登录按钮
$(document).on('click', '#logout_button', function() {
    $.ajax({
        url: '/logout',
        type: 'POST',
        data: JSON.stringify({
            'username': $.cookie('username'),
            'password': $.cookie('password')
        }),
        contentType: 'application/json;charset=utf-8',
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

// 点击抢座按钮
$(document).on('click', '#get_seat_button', function() {
    $.ajax({
            url: '/get_seat',
            type: 'POST',
            data: JSON.stringify({
                'username': $.cookie('username'),
                'password': $.cookie('password')
            }),
            contentType: 'application/json;charset=utf-8',
            success: function(data) {
                if (data['status']) {
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
        // ajax轮询，每秒查询抢座状态
    var poll = setInterval(function() {
        $.ajax({
            url: '/get_status',
            type: 'POST',
            data: JSON.stringify({
                'username': $.cookie('username'),
                'password': $.cookie('password')
            }),
            contentType: 'application/json;charset=utf-8',
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
        $('#process_modal').on('hidden.bs.modal', function() {
            clearInterval(poll)
        })
    }, 1000)
})

$(document).on('click', '#cancel_get_seat', function() {
    $.ajax({
        url: '/cancel_get_seat',
        type: 'POST',
        data: JSON.stringify({
            'username': $.cookie('username'),
            'password': $.cookie('password')
        }),
        contentType: 'application/json;charset=utf-8',
        success: function(data) {
            if (data['status']) {
                alert(data['msg'])
            }
        }
    })
})