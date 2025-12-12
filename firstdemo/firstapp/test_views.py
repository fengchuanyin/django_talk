from django.shortcuts import render
from django.http import HttpResponse

def test_view(request):
    return HttpResponse("""
    <html>
    <head><title>测试页面</title></head>
    <body>
        <h1>电商评论洞察系统</h1>
        <p><a href="/reviews/">访问评论洞察系统</a></p>
        <p><a href="/admin/">访问管理后台</a></p>
    </body>
    </html>
    """)