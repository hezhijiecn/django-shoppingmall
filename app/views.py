#coding:utf-8

from django.shortcuts import render,redirect
from django.http import HttpResponse,HttpResponseRedirect
from django.views.generic import View
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Commodity, Sale, CommodityType, File, AssociationRule, AssociationTime

from django.http import JsonResponse
from .forms import FileForm
# Create your views here.


class homepage(View):
	Tempalte = 'mainpage/index.html'

	def get(self, request):


		user = request.user if request.user.is_authenticated else None
		commodities = Commodity.objects.filter().order_by('id')
	
		
		return render(request, self.Tempalte, locals())


class login(View):

	Tempalte = 'mainpage/login.html'

	def get(self, request):
		user = request.user if request.user.is_authenticated else None
		return render(request, self.Tempalte, locals())

	def post(self,request):
		username = request.POST.get('username')
		password = request.POST.get('password')
		user = auth.authenticate(username=username, password=password)

		if user is not None:
			auth.login(request, user)
			#commodities = Commodity.objects.filter()
			return HttpResponseRedirect('/')
			#return render(request, 'mainpage/index.html', locals()) #验证成功 登录到主页

		else:
			state = 'not_exist_or_password_error'
		content = {
			'active_menu':'homepage',
			'state':state,
			'user':None
		}
		return render(request, 'mainpage/login.html', content)


class signup(View):
	Tempalte = 'mainpage/signup.html'

	def get(self, request):
		user = request.user if request.user.is_authenticated else None
		return render(request, self.Tempalte, locals())

	def post(self, request):
		password = request.POST.get('password','')
		repeat_password = request.POST.get('repeat_password', '')
		if password =='' or repeat_password == '':
			state = 'empty'
		elif password !=repeat_password:
			state = 'repeat_error'
		else:
			username = request.POST.get('username', '')
			if User.objects.filter(username = username):
				state = 'user_exist'
			else:
				new_user = User.objects.create_user(username = username, password=password, email = request.POST.get('email',''))
				new_user.save()
				state = 'success'
		content = {
			'active_menu':'homepage',
			'state':state,
			'user':None
		}
		return render(request,self.Tempalte, content)

class setpassword(View):
	Tempalte = 'mainpage/setpassword.html'

	def get(self, request):

		return render(request, self.Tempalte)

	def post(self, request):
		user = request.user
		old_password = request.POST.get('old_password','')
		new_password = request.POST.get('new_password','')
		repeat_password = request.POST.get('repeat_password', '')
		if user.check_password(old_password):
			if not new_password:
				state = 'empty'
			elif new_password != repeat_password:
				state = 'repeat_error'
			else:
				user.set_password(new_password)
				user.save()
				state = 'success'
		else:
			state = 'password_error'
		content = {
			'user' : user, 
			'active_menu': homepage,
			'state':state
		}
		return render(request,self.Tempalte, content)


@login_required
def info(request):
	user = request.user
	return render(request, 'mainpage/info.html',locals())


#退出登录
def logout(request):
	auth.logout(request)
	return HttpResponseRedirect('/')


class SaleRecord(View):

	Tempalte = 'mainpage/sale_record.html'

	def get(self, request):

		SaleRecords = Sale.objects.filter().order_by('order_number')
		return render(request, self.Tempalte, locals())
		
	def post(self, request):
		commodity_name = request.POST.get('commodity_name')
		order_number = request.POST.get('order_number')

		if commodity_name!='':
			commodity = Commodity.objects.filter(name__icontains=commodity_name).first()
			SaleRecords = Sale.objects.filter(order_number__icontains=order_number, commodity=commodity).order_by('order_number')
		else:
			SaleRecords = Sale.objects.filter(order_number__icontains=order_number).order_by('order_number')
		users = User.objects.filter()
		return render(request, self.Tempalte, locals())
		

class Analysis(View):
	Tempalte = 'mainpage/analysis.html'

	def get(self, request):
		files_list = File.objects.all()
		return render(self.request, self.Tempalte , {'files': files_list})

	def post(self, request):
		form = FileForm(self.request.POST, self.request.FILES)

		if form.is_valid():
			title = file.file.name.split("/")[-1]
			file.title = title
			file.save()

		
		return redirect('analysis/')


@login_required
def clear_database(request):
	for file in File.objects.all():
		file.file.delete()
		file.delete()
	return redirect(request.POST.get('next'))

from django.conf import settings
import os 
from app import data_mining
import time
#Fp_growth算法
def Fp_growth(path, min_support, min_conf, name):
	#设置存储的log文件名称
	save_path=settings.MEDIA_ROOT+"/log/"+name.split("/")[-1].split(".")[0]+"_fpgrowth.txt"

	filename_rule = name.split("/")[-1].split(".")[0]+"_fpgrowth"

	data = data_mining.load_data(path)
	fp=data_mining.Fp_growth()

	#txt = os.path.join(settings.MEDIA_ROOT, '/files/groceries_fpgrowth.txt')

	rule_lists = fp.generate_R(data, min_support, min_conf)

	#将结果存储到文本文件里面
	if not os.path.exists(settings.MEDIA_ROOT+"/log"):
		os.mkdir(settings.MEDIA_ROOT+"/log")

	data_mining.save_rule(rule_lists,save_path)

	#去掉frozenset
	#round(item[2],2)保留小数点后两位
	rules=[]
	tmp=[]
	for item in rule_lists:
		tmp = [str(list(item[0])), str(list(item[1])), round(item[2],2)]
		AssociationRule.objects.create(antecedent = tmp[0], consequent=tmp[1],conf = tmp[2], filename = filename_rule,min_support=min_support,min_conf=min_conf)
		rules.append(tmp)
	return rules


#Apriori算法
def Apriori(path, min_support, min_conf, name):
	#设置存储的log文件名称
	save_path=settings.MEDIA_ROOT+"/log/"+name.split("/")[-1].split(".")[0]+"_apriori.txt"

	filename_rule = name.split("/")[-1].split(".")[0]+"_apriori"

	data = data_mining.load_data(path)
	apriori = data_mining.Apriori()

	#算出购买的商品以及购买次数
	#C1 = apriori.create_c1(data)
	#support_data = apriori.generate_lk_by_ck(data, C1, min_support, support_data)

	#txt = os.path.join(settings.MEDIA_ROOT, '/files/groceries_fpgrowth.txt')

	rule_lists = apriori.generate_R(data, min_support, min_conf)

	#将结果存储到文本文件里面
	if not os.path.exists(settings.MEDIA_ROOT+"/log"):
		os.mkdir(settings.MEDIA_ROOT+"/log")

	data_mining.save_rule(rule_lists,save_path)

	#去掉frozenset
	#round(item[2],2)保留小数点后两位
	rules=[]
	tmp=[]
	for item in rule_lists:
		tmp = [str(list(item[0])), str(list(item[1])), round(item[2],2)]
		AssociationRule.objects.create(antecedent = tmp[0], consequent=tmp[1],conf = tmp[2], filename = filename_rule, min_support=min_support, min_conf=min_conf)
		rules.append(tmp)

#保存算法运行的时间 方便计算
def AssociationTimeAdd(filename, algorithm, min_support,min_conf, time):
	#先检测
	time = round(time,3)#保留三位有效小数

	algorithm_time = AssociationTime.objects.filter(filename=filename, algorithm=algorithm, min_support=min_support, min_conf=min_conf)
	algorithm_time.delete()
	AssociationTime.objects.create(filename = filename, algorithm=algorithm,min_support = min_support,min_conf=min_conf, time = time)



#Apriori_compress算法
def Apriori_Compress(path, min_support, min_conf, name):
	#设置存储的log文件名称
	save_path=settings.MEDIA_ROOT+"/log/"+name.split("/")[-1].split(".")[0]+"_apriori_compress.txt"

	filename_rule = name.split("/")[-1].split(".")[0]+"_apriori_compress"

	data = data_mining.load_data(path)
	apriori_compress = data_mining.Apriori_compress()

	rule_lists = apriori_compress.generate_R(data, min_support, min_conf)

	#将结果存储到文本文件里面
	if not os.path.exists(settings.MEDIA_ROOT+"/log"):
		os.mkdir(settings.MEDIA_ROOT+"/log")

	data_mining.save_rule(rule_lists,save_path)

	#去掉frozenset
	#round(item[2],2)保留小数点后两位
	rules=[]
	tmp=[]
	for item in rule_lists:
		tmp = [str(list(item[0])), str(list(item[1])), round(item[2],2)]
		AssociationRule.objects.create(antecedent = tmp[0], consequent=tmp[1],conf = tmp[2], filename = filename_rule, min_support=min_support, min_conf=min_conf)
		rules.append(tmp)	


#Apriori_Hash算法
def Apriori_Hash(path, min_support, min_conf, name):
	#设置存储的log文件名称
	save_path=settings.MEDIA_ROOT+"/log/"+name.split("/")[-1].split(".")[0]+"_apriori_hash.txt"

	filename_rule = name.split("/")[-1].split(".")[0]+"_apriori_hash"

	data = data_mining.load_data(path)
	apriori_hash = data_mining.Apriori_hash()

	rule_lists = apriori_hash.generate_R(data, min_support, min_conf)

	#将结果存储到文本文件里面
	if not os.path.exists(settings.MEDIA_ROOT+"/log"):
		os.mkdir(settings.MEDIA_ROOT+"/log")

	data_mining.save_rule(rule_lists,save_path)

	#去掉frozenset
	#round(item[2],2)保留小数点后两位
	rules=[]
	tmp=[]
	for item in rule_lists:
		tmp = [str(list(item[0])), str(list(item[1])), round(item[2],2)]
		AssociationRule.objects.create(antecedent = tmp[0], consequent=tmp[1],conf = tmp[2], filename = filename_rule, min_support=min_support, min_conf=min_conf)
		rules.append(tmp)	

#Apriori_Plus算法
def Apriori_Plus(path, min_support, min_conf, name):
	#设置存储的log文件名称
	save_path=settings.MEDIA_ROOT+"/log/"+name.split("/")[-1].split(".")[0]+"_apriori_plus.txt"

	filename_rule = name.split("/")[-1].split(".")[0]+"_apriori_plus"

	data = data_mining.load_data(path)
	apriori_plus = data_mining.Apriori_plus()

	rule_lists = apriori_plus.generate_R(data, min_support, min_conf)

	#将结果存储到文本文件里面
	if not os.path.exists(settings.MEDIA_ROOT+"/log"):
		os.mkdir(settings.MEDIA_ROOT+"/log")

	data_mining.save_rule(rule_lists,save_path)

	#去掉frozenset
	#round(item[2],2)保留小数点后两位
	rules=[]
	tmp=[]
	for item in rule_lists:
		tmp = [str(list(item[0])), str(list(item[1])), round(item[2],2)]
		AssociationRule.objects.create(antecedent = tmp[0], consequent=tmp[1],conf = tmp[2], filename = filename_rule, min_support=min_support, min_conf=min_conf)
		rules.append(tmp)


#Fp_Growth_Plus算法
def Fp_Growth_Plus(path, min_support, min_conf, name):
	#设置存储的log文件名称
	save_path=settings.MEDIA_ROOT+"/log/"+name.split("/")[-1].split(".")[0]+"_fp_growth_plus.txt"

	filename_rule = name.split("/")[-1].split(".")[0]+"_fp_growth_plus"

	data = data_mining.load_data(path)
	apriori_plus = data_mining.Fp_growth_plus()

	rule_lists = apriori_plus.generate_R(data, min_support, min_conf)

	#将结果存储到文本文件里面
	if not os.path.exists(settings.MEDIA_ROOT+"/log"):
		os.mkdir(settings.MEDIA_ROOT+"/log")

	data_mining.save_rule(rule_lists,save_path)

	#去掉frozenset
	#round(item[2],2)保留小数点后两位
	rules=[]
	tmp=[]
	for item in rule_lists:
		tmp = [str(list(item[0])), str(list(item[1])), round(item[2],2)]
		AssociationRule.objects.create(antecedent = tmp[0], consequent=tmp[1],conf = tmp[2], filename = filename_rule, min_support=min_support, min_conf=min_conf)
		rules.append(tmp)	





@login_required
def analysis_detail(request, name):
	Tempalte = 'mainpage/analysis_detail.html'

	if request.method == 'POST':

		path = os.path.join(settings.MEDIA_ROOT, name)

		min_support = float(request.POST.get('min_support', '25'))#最小支持度
		min_conf = float(request.POST.get('min_conf', '0.7'))#最小置信度

		file_name = name.split("/")[-1]
		algorithm = ['Apriori','Fp_growth','Apriori_Compress', 'Apriori_Hash','Apriori_Plus','Fp_Growth_Plus']
	

		#------------------------------------------------------------------------------------------#
		#检测是否已经生成过该数据的apriori关联规则
		filename_apriori_rule = name.split("/")[-1].split(".")[0]+"_apriori"
		apriori_rulelists = AssociationRule.objects.filter(filename=filename_apriori_rule, min_support=min_support, min_conf=min_conf)

		if not apriori_rulelists:
			#计算算法运行时间
			apriori_start_time = time.perf_counter()

			Apriori(path, min_support,min_conf,name)

			apriori_end_time = time.perf_counter()
			apriori_time = apriori_end_time - apriori_start_time
			
			AssociationTimeAdd(file_name, algorithm[0], min_support, min_conf, apriori_time)

			apriori_rulelists = AssociationRule.objects.filter(filename=filename_apriori_rule, min_support=min_support, min_conf=min_conf)
		#------------------------------------------------------------------------------------------#

		#算出购买的商品以及购买次数
		filename_commodity = name.split("/")[-1].split(".")[0]
		file_commodities = Commodity.objects.filter(filename=filename_commodity)

		if not file_commodities:

			support_data = {}
			apriori = data_mining.Apriori()
			data = data_mining.load_data(path)
			C1 = apriori.create_c1(data)
			L1 = apriori.generate_lk_by_ck(data, C1, 0, support_data)
		
			for key,value in support_data.items():
				tmp = [str(list(key)[0]), value]
				Commodity.objects.create(name=tmp[0],num=tmp[1], filename = filename_commodity)
			file_commodities = Commodity.objects.filter(filename=filename_commodity)

		#------------------------------------------------------------------------------------------#
		#检测是否已经生成过该数据的fp-growth关联规则
		filename_fp_rule = name.split("/")[-1].split(".")[0]+"_fpgrowth"
		fp_rulelists = AssociationRule.objects.filter(filename=filename_fp_rule, min_support=min_support, min_conf=min_conf)

		if not fp_rulelists:

			fp_growth_start_time = time.perf_counter()

			Fp_growth(path, min_support,min_conf,name)

			fp_growth_end_time = time.perf_counter()
			fp_growth_time = fp_growth_end_time - fp_growth_start_time

			AssociationTimeAdd(file_name, algorithm[1], min_support, min_conf, fp_growth_time)

			fp_rulelists = AssociationRule.objects.filter(filename=filename_fp_rule,min_support=min_support, min_conf=min_conf)
		#------------------------------------------------------------------------------------------#
		#检测是否已经生成过该数据的apriori_compress关联规则
		filename_apriori_compress_rule = name.split("/")[-1].split(".")[0]+"_apriori_compress"
		apriori_compress_rulelists = AssociationRule.objects.filter(filename=filename_apriori_compress_rule, min_support=min_support, min_conf=min_conf)

		if not apriori_compress_rulelists:

			apriori_compress_start_time = time.perf_counter()

			Apriori_Compress(path, min_support,min_conf,name)

			apriori_compress_end_time = time.perf_counter()
			apriori_compress_time = apriori_compress_end_time - apriori_compress_start_time

			AssociationTimeAdd(file_name, algorithm[2], min_support, min_conf, apriori_compress_time)

			apriori_compress_rulelists = AssociationRule.objects.filter(filename=filename_apriori_compress_rule, min_support=min_support, min_conf=min_conf)


		#------------------------------------------------------------------------------------------#
		#检测是否已经生成过该数据的apriori_hash关联规则
		filename_apriori_hash_rule = name.split("/")[-1].split(".")[0]+"_apriori_hash"
		apriori_hash_rulelists = AssociationRule.objects.filter(filename=filename_apriori_hash_rule, min_support=min_support, min_conf=min_conf)

		if not apriori_hash_rulelists:

			apriori_hash_start_time = time.perf_counter()

			Apriori_Hash(path, min_support,min_conf,name)

			apriori_hash_end_time = time.perf_counter()
			apriori_hash_time = apriori_hash_end_time - apriori_hash_start_time

			AssociationTimeAdd(file_name, algorithm[3], min_support, min_conf, apriori_hash_time)

			apriori_hash_rulelists = AssociationRule.objects.filter(filename=filename_apriori_hash_rule, min_support=min_support, min_conf=min_conf)


		#------------------------------------------------------------------------------------------#
		#检测是否已经生成过该数据的apriori_plus关联规则
		filename_apriori_plus_rule = name.split("/")[-1].split(".")[0]+"_apriori_plus"
		apriori_plus_rulelists = AssociationRule.objects.filter(filename=filename_apriori_plus_rule, min_support=min_support, min_conf=min_conf)

		if not apriori_plus_rulelists:

			apriori_plus_start_time = time.perf_counter()

			Apriori_Plus(path, min_support,min_conf,name)

			apriori_plus_end_time = time.perf_counter()
			apriori_plus_time = apriori_plus_end_time - apriori_plus_start_time

			AssociationTimeAdd(file_name, algorithm[4], min_support, min_conf, apriori_plus_time)

			apriori_plus_rulelists = AssociationRule.objects.filter(filename=filename_apriori_plus_rule, min_support=min_support, min_conf=min_conf)


		#------------------------------------------------------------------------------------------#
		#检测是否已经生成过该数据的fp_growth_plus关联规则
		filename_fp_growth_plus_rule = name.split("/")[-1].split(".")[0]+"_fp_growth_plus"
		fp_growth_plus_rulelists = AssociationRule.objects.filter(filename=filename_fp_growth_plus_rule, min_support=min_support, min_conf=min_conf)

		if not fp_growth_plus_rulelists:

			fp_growth_plus_start_time = time.perf_counter()

			Fp_Growth_Plus(path, min_support,min_conf,name)

			fp_growth_plus_end_time = time.perf_counter()
			fp_growth_plus_time = fp_growth_plus_end_time - fp_growth_plus_start_time

			AssociationTimeAdd(file_name, algorithm[5], min_support, min_conf, fp_growth_plus_time)

			fp_growth_plus_rulelists = AssociationRule.objects.filter(filename=filename_fp_growth_plus_rule, min_support=min_support, min_conf=min_conf)


		#------------------------------------------------------------------------------------------#
		#算法时间进行对比
		algorithm_time_lists = AssociationTime.objects.filter(filename = file_name,  min_support=min_support, min_conf=min_conf)

		#
		return render(request, Tempalte , locals())


