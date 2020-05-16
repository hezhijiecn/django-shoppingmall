#coding:utf-8

from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Userprofile(models.Model):
	user = models.OneToOneField(User, blank=True, null=True, on_delete=models.SET_NULL)
	birthday = models.DateTimeField()
	phone = models.CharField(db_index=True, blank=True, default=0,max_length=11)
	balance = models.FloatField(default=0.0)
	consume = models.FloatField(default=0.0)
	def __str__(self):
		return 'User:{}'.format(self.user.username)

class CommodityType(models.Model):
	first_type = models.CharField(max_length=20)
	second_type = models.CharField(max_length=20)
	class META:
		ordering = ['id']

	def __str__(self):
		return 'first_type:{},second_type:{}'.format(self.first_type,self.second_type)

class Commodity(models.Model):
	commodity_type = models.ForeignKey(CommodityType, related_name='commoditytype', on_delete=models.SET_NULL, blank=True,null=True)
	name = models.CharField(unique=True, max_length=100, blank=False)
	price = models.FloatField(default=0.0)
	stock = models.IntegerField(default=0)
	num = models.IntegerField(default=0, null=True)							#商品被购买次数
	filename = models.CharField(max_length=20, blank=True)
	add_time = models.DateTimeField(auto_now_add=True,null=True)                 #商品添加时间

	class META:
		ordering = ['name']

			
	def __str__(self):
		return 'name:{},stock:{}'.format(self.name,self.stock)


class Sale(models.Model):
	user = models.ForeignKey(User, related_name='sale_user', on_delete=models.SET_NULL, blank=True,null=True)
	commodity = models.ForeignKey(Commodity, related_name='sale_commodity', on_delete=models.SET_NULL, blank=True,null=True)
	number = models.IntegerField(default=0)
	order_number = models.CharField(max_length=20)
	create_time = models.DateTimeField(auto_now_add=True)
	class META:
		ordering = ['order_number']

	def __str__(self):
		return 'user:{},commodity:{},number:{}'.format(self.user.username, self.commodity.name,self.number)



class File(models.Model):
    title = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to='files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


class AssociationRule(models.Model):
	antecedent = models.CharField(max_length=255)
	consequent = models.CharField(max_length=255)
	conf = models.FloatField(default=0.0)
	filename = models.CharField(max_length=30)
	min_support = models.FloatField(default=25)
	min_conf = models.FloatField(default=0.7)


class AssociationTime(models.Model):
	filename = models.CharField(max_length=100)
	algorithm = models.CharField(max_length=100)
	min_support = models.FloatField(default=0.0)
	min_conf = models.FloatField(default=0.0)
	time = models.FloatField(default=0.0)
