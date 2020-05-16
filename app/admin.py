#coding:utf-8

from django.contrib import admin
from .models import  Userprofile,Commodity,Sale, CommodityType
# Register your models here.

admin.site.register(Userprofile)
admin.site.register(Commodity)
admin.site.register(Sale)
admin.site.register(CommodityType)

