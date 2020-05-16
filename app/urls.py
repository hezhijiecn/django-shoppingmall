#coding:utf-8

from django.urls import path
from django.conf.urls import url

from app.views import homepage, login, signup, logout, setpassword,info, SaleRecord,Analysis,analysis_detail, clear_database

urlpatterns = [
    path('', homepage.as_view(), name='homepage'),
    path('accounts/login/', login.as_view(), name='login'),
    path('accounts/signup/', signup.as_view(), name='signup'),
    path('accounts/logout/', logout, name='logout'),
    path('accounts/setpassword/', setpassword.as_view(), name='setpassword'),
    path('accounts/info/', info, name='info'),
    path('sale_record/', SaleRecord.as_view(), name='sale_record'),
    path('analysis/', Analysis.as_view(), name='analysis'),
    path('clear/', clear_database, name='clear_database'),
    url(r'^analysis_detail/(.+?)$', analysis_detail, name='analysis_detail'),
]
