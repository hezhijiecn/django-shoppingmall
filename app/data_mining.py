#-*- coding: utf-8 -*-
import os
import time
from tqdm import tqdm

#根据路径加载数据集
def load_data(path):
	ans=[]#将数据保存到该数组
	if path.split(".")[-1]=="xls":#若路径为药方.xls   若后缀名为xls文件                   
		from xlrd import open_workbook
		import xlwt
		workbook=open_workbook(path)
		sheet=workbook.sheet_by_index(0)#读取第一个sheet
		for i in range(1,sheet.nrows):#忽视header,从第二行开始读数据,第一列为处方ID,第二列为药品清单
			temp=sheet.row_values(i)[1].split(";")[:-1]#取该行数据的第二列并以“;”分割为数组
			if len(temp)==0: continue
			temp=[j.split(":")[0] for j in temp]#将药品后跟着的药品用量去掉
			temp=list(set(temp))#去重，排序
			temp.sort()
			ans.append(temp)#将处理好的数据添加到数组
	elif path.split(".")[-1]=="csv":
		import csv
		with open(path,"r") as f:
			reader=csv.reader(f)
			for row in reader:
				row=list(set(row))#去重，排序
				row.sort()# 注意 这里 去重排序都是一个记录中内部的去重和排序
				ans.append(row)#将添加好的数据添加到数组
	return ans#返回处理好的数据集，为二维数组
  
def save_rule(rule,path):#保存结果到txt文件
	with open(path,"w") as f:
		f.write("index  confidence"+"   rules\n")
		index=1
		for item in rule:
			s=" {:<4d}  {:.3f}        {}=>{}\n".format(index,item[2],str(list(item[0])),str(list(item[1])))
			index+=1
			f.write(s)
		f.close()
	print("result saved,path is:{}".format(path))
#---------------------------------------------------------------------------------#
#Apriori()算法
class Apriori():

	def create_c1(self,dataset):#遍历整个数据集生成c1候选集
		c1=set()
		for i in dataset:
			for j in i:
				item = frozenset([j])
				c1.add(item)
		return c1

	def create_ck(self,Lk_1,size):#通过频繁项集Lk-1创建ck候选项集
		Ck = set()
		l = len(Lk_1)
		lk_list = list(Lk_1)
		for i in range(l):
			for j in range(i+1, l):#两次遍历Lk-1，找出前n-1个元素相同的项
				l1 = list(lk_list[i])
				l2 = list(lk_list[j])
				l1.sort()
				l2.sort()
				if l1[0:size-2] == l2[0:size-2]:#只有最后一项不同时，生成下一候选项  如果前k-1项都是相同的
					Ck_item = lk_list[i] | lk_list[j]

					#这个地方其实提前就删去了那些子集不频繁的情况
					#因为Lk这个频繁项集产生ck+1时候  有可能产生不频繁的k+1候选项  原因是因为其子集就不频繁，这个时候我们验证一下  可以避免这种情况 
					if self.has_infrequent_subset(Ck_item, Lk_1):#检查该候选项的子集是否都在Lk-1中
						Ck.add(Ck_item)
		return Ck

	def has_infrequent_subset(self,Ck_item, Lk_1):#检查候选项Ck_item的子集是否都在Lk-1中
		for item in Ck_item: 
			sub_Ck = Ck_item - frozenset([item])
			if sub_Ck not in Lk_1:
				return False
		return True

	def generate_lk_by_ck(self,data_set,ck,min_support,support_data):#通过候选项ck生成lk，并将各频繁项的支持度保存到support_data字典中
		item_count={}#用于标记各候选项在数据集出现的次数
		Lk = set()
		for t in tqdm(data_set):#遍历数据集
			for item in ck:#检查候选集ck中的每一项是否出现在事务t中
				if item.issubset(t):  #如果item在这个t事务中出现了  则应该+1  但要分是第几次出现
					if item not in item_count:
						item_count[item] = 1
					else:
						item_count[item] += 1

		t_num = float(len(data_set))
		
		for item in item_count:#将满足支持度的候选项添加到频繁项集中
			if item_count[item] >= min_support:
				Lk.add(item)
				support_data[item] = item_count[item]
		return Lk
		

	def generate_L(self,data_set, min_support):#用于生成所有频繁项集的主函数，k为最大频繁项的大小
		support_data = {} #用于保存各频繁项的支持度
		C1 = self.create_c1(data_set) #生成C1 候选1项集  但是并不一定符合频繁度
		L1 = self.generate_lk_by_ck(data_set, C1, min_support, support_data)#根据C1生成L1  频繁1项集

		Lksub1 = L1.copy() #初始时Lk.-1=L1
		L = []
		L.append(Lksub1)
		i=2

		while(True):
			Ci = self.create_ck(Lksub1, i)  #根据Lk-1生成Ck
			Li = self.generate_lk_by_ck(data_set, Ci, min_support, support_data) #根据Ck生成Lk
			
			if len(Li)==0:break

			Lksub1 = Li.copy()  #下次迭代时Lk-1=Lk
			L.append(Lksub1)
			i+=1

		for i in range(len(L)):
			print("frequent item {}：{}".format(i+1,len(L[i])))  #但是这个len好像是所有的频繁项集长度之和  包括频繁1,2,3-i的项集
		return L, support_data

	def generate_R(self,dataset, min_support, min_conf):
		L,support_data=self.generate_L(dataset,min_support)#根据频繁项集和支持度生成关联规则

		rule_list = []#保存满足置信度的规则
		sub_set_list = []#该数组保存检查过的频繁项

		#生成关联规则
		for i in range(0, len(L)):
			for freq_set in L[i]:#遍历Lk

				for sub_set in sub_set_list:#sub_set_list中保存的是L1到Lk-1
					if sub_set.issubset(freq_set):#检查sub_set是否是freq_set的子集
						#检查置信度是否满足要求，是则添加到规则
						conf = support_data[freq_set] / support_data[freq_set - sub_set]
						big_rule = (freq_set - sub_set, sub_set, conf)
						if conf >= min_conf and big_rule not in rule_list:
							rule_list.append(big_rule)

				sub_set_list.append(freq_set)

		rule_list = sorted(rule_list,key=lambda x:(x[2]),reverse=True)
		return rule_list



#---------------------------------------------------------------------------------#
#fp-growth 算法
class Node:
	def __init__(self, node_name,count,parentNode):
		self.name = node_name
		self.count = count
		self.nodeLink = None#根据nideLink可以找到整棵树中所有nodename一样的节点
		self.parent = parentNode#父亲节点
		self.children = {}#子节点{节点名字:节点地址}

class Fp_growth():
	def update_header(self,node, targetNode):#更新headertable中的node节点形成的链表
		while node.nodeLink != None:
			node = node.nodeLink
		node.nodeLink = targetNode

	def update_fptree(self,items, node, headerTable):#用于更新fptree
		if items[0] in node.children:
			# 判断items的第一个结点是否已作为子结点
			node.children[items[0]].count+=1
		else:
			# 创建新的分支
			node.children[items[0]] = Node(items[0],1,node)
			# 更新相应频繁项集的链表，往后添加
			if headerTable[items[0]][1] == None:
				headerTable[items[0]][1] = node.children[items[0]]
			else:
				self.update_header(headerTable[items[0]][1], node.children[items[0]])
			# 递归
		if len(items) > 1:
			self.update_fptree(items[1:], node.children[items[0]], headerTable)

	def create_fptree(self,data_set, min_support,flag=False):#建树主函数
		'''
		根据data_set创建fp树
		header_table结构为
		{"nodename":[num,node],..} 根据node.nodelink可以找到整个树中的所有nodename
		'''
		item_count = {}#统计各项出现次数
		for t in data_set:#第一次遍历，得到频繁一项集
			for item in t:
				if item not in item_count:
					item_count[item]=1
				else:
					item_count[item]+=1
		headerTable={}
		for k in item_count:#剔除不满足最小支持度的项
			if item_count[k] >= min_support:
				headerTable[k]=item_count[k]
		
		freqItemSet = set(headerTable.keys())#满足最小支持度的频繁项集
		if len(freqItemSet) == 0:
			return None, None
		for k in headerTable:
			headerTable[k] = [headerTable[k], None] # element: [count, node]
		tree_header = Node('head node',1,None)
		if flag:
			ite=tqdm(data_set)
		else:
			ite=data_set
		for t in ite:#第二次遍历，建树
			localD = {}
			for item in t:
				if item in freqItemSet: # 过滤，只取该样本中满足最小支持度的频繁项
					localD[item] = headerTable[item][0] # element : count
			if len(localD) > 0:
				# 根据全局频数从大到小对单样本排序
				order_item = [v[0] for v in sorted(localD.items(), key=lambda x:x[1], reverse=True)]
				# 用过滤且排序后的样本更新树
				self.update_fptree(order_item, tree_header, headerTable)
		return tree_header, headerTable

	def find_path(self,node, nodepath):
		'''
		递归将node的父节点添加到路径
		'''
		if node.parent != None:
			nodepath.append(node.parent.name)
			self.find_path(node.parent, nodepath)

	def find_cond_pattern_base(self,node_name, headerTable):
		'''
		根据节点名字，找出所有条件模式基
		'''
		treeNode = headerTable[node_name][1]
		cond_pat_base = {}#保存所有条件模式基
		while treeNode != None:
			nodepath = []
			self.find_path(treeNode, nodepath)
			if len(nodepath) > 1:
				cond_pat_base[frozenset(nodepath[:-1])] = treeNode.count 
			treeNode = treeNode.nodeLink 
		return cond_pat_base

	def create_cond_fptree(self,headerTable, min_support, temp, freq_items,support_data):
		# 最开始的频繁项集是headerTable中的各元素
		freqs = [v[0] for v in sorted(headerTable.items(), key=lambda p:p[1][0])] # 根据频繁项的总频次排序
		for freq in freqs: # 对每个频繁项
			freq_set = temp.copy()
			freq_set.add(freq)
			freq_items.add(frozenset(freq_set))
			if frozenset(freq_set) not in support_data:#检查该频繁项是否在support_data中
				support_data[frozenset(freq_set)]=headerTable[freq][0]
			else:
				support_data[frozenset(freq_set)]+=headerTable[freq][0]

			cond_pat_base = self.find_cond_pattern_base(freq, headerTable)#寻找到所有条件模式基
			cond_pat_dataset=[]#将条件模式基字典转化为数组
			for item in cond_pat_base:
				item_temp=list(item)
				item_temp.sort()
				for i in range(cond_pat_base[item]):
					cond_pat_dataset.append(item_temp)
			#创建条件模式树
			cond_tree, cur_headtable = self.create_fptree(cond_pat_dataset, min_support)
			if cur_headtable != None:
				self.create_cond_fptree(cur_headtable, min_support, freq_set, freq_items,support_data) # 递归挖掘条件FP树

	def generate_L(self,data_set,min_support):
		freqItemSet=set()
		support_data={}
		tree_header,headerTable=self.create_fptree(data_set,min_support,flag=True)#创建数据集的fptree
		#创建各频繁一项的fptree，并挖掘频繁项并保存支持度计数
		self.create_cond_fptree(headerTable, min_support, set(), freqItemSet,support_data)
		
		max_l=0
		for i in freqItemSet:#将频繁项根据大小保存到指定的容器L中
			if len(i)>max_l:max_l=len(i)
		L=[set() for _ in range(max_l)]
		for i in freqItemSet:
			L[len(i)-1].add(i)
		for i in range(len(L)):
			print("frequent item {}:{}".format(i+1,len(L[i]))) 
		return L,support_data 

	def generate_R(self,data_set, min_support, min_conf):
		L,support_data=self.generate_L(data_set,min_support)
		rule_list = []
		sub_set_list = []
		for i in range(0, len(L)):
			for freq_set in L[i]:
				for sub_set in sub_set_list:
					if sub_set.issubset(freq_set) and freq_set-sub_set in support_data:#and freq_set-sub_set in support_data
						conf = support_data[freq_set] / support_data[freq_set - sub_set]
						big_rule = (freq_set - sub_set, sub_set, conf)
						if conf >= min_conf and big_rule not in rule_list:
						    # print freq_set-sub_set, " => ", sub_set, "conf: ", conf
							rule_list.append(big_rule)
				sub_set_list.append(freq_set)
		rule_list = sorted(rule_list,key=lambda x:(x[2]),reverse=True)
		return rule_list

#---------------------------------------------------------------------------------#
#Apriori_compress 算法
class Apriori_compress():
	def create_c1(self,dataset):#遍历整个数据集生成c1候选集
		c1=set()
		for i in dataset:
			for j in i:
				item = frozenset([j])
				c1.add(item)
		return c1

	def create_ck(self,Lk_1,size):#通过频繁项集Lk-1创建ck候选项集
		Ck = set()
		l = len(Lk_1)
		lk_list = list(Lk_1)
		for i in range(l):
			for j in range(i+1, l):#两次遍历Lk-1，找出前n-1个元素相同的项
				l1 = list(lk_list[i])
				l2 = list(lk_list[j])
				l1.sort()
				l2.sort()
				if l1[0:size-2] == l2[0:size-2]:#只有最后一项不同时，生成下一候选项
					Ck_item = lk_list[i] | lk_list[j]
					if self.has_infrequent_subset(Ck_item, Lk_1):#检查该候选项的子集是否都在Lk-1中
						Ck.add(Ck_item)
		return Ck

	def has_infrequent_subset(self,Ck_item, Lk_1):#检查候选项Ck_item的子集是否都在Lk-1中
		for item in Ck_item: 
			sub_Ck = Ck_item - frozenset([item])
			if sub_Ck not in Lk_1:
				return False
		return True

	#事务压缩，上次不包含频繁项的事务这次不遍历
	def generate_lk_by_ck(self,data_set,ck,min_support,support_data,flag):#通过候选项ck生成lk，并将各频繁项的支持度保存到support_data字典中
		item_count={}#用于标记各候选项在数据集出现的次数
		Lk = set()
		index=-1
		for t in tqdm(data_set):
			index+=1
			if not flag[index]: continue#上次迭代时不包含频繁项，这次迭代选择跳过
			item_flag=False#标记该事务是否包含频繁项
			for item in ck:
				if item.issubset(t):
					item_flag=True#该事务中含有频繁项
					if item not in item_count:
						item_count[item] = 1
					else:
						item_count[item] += 1
			#不包含频繁项，flag相应位置置为False，下次遍历时跳过	
			if not item_flag:flag[index]=False
		t_num = float(len(data_set))
		for item in item_count:#将满足支持度的候选项添加到频繁项集中
			if item_count[item] >= min_support:
				Lk.add(item)
				support_data[item] = item_count[item]
		return Lk
		

	def generate_L(self,data_set, min_support):#用于生成所有频繁项集的主函数，k为最大频繁项的大小
		support_data = {} #用于保存各频繁项的支持度
		flag=[True for _ in range(len(data_set))]#用于事务压缩的标记数组
		C1 = self.create_c1(data_set) #生成C1
		L1 = self.generate_lk_by_ck(data_set, C1, min_support, support_data,flag)#根据C1生成L1
		Lksub1 = L1.copy() #初始时Lk-1=L1
		L = []
		L.append(Lksub1)
		i=2
		while(True):
			Ci = self.create_ck(Lksub1, i)  #根据Lk-1生成Ck
			Li = self.generate_lk_by_ck(data_set, Ci, min_support, support_data,flag) #根据Ck生成Lk
			if len(Li)==0:break
			Lksub1 = Li.copy()  #下次迭代时Lk-1=Lk
			L.append(Lksub1)
			i+=1
		for i in range(len(L)):
			print("frequent item {}：{}".format(i+1,len(L[i])))
		return L, support_data

	def generate_R(self,dataset, min_support, min_conf):
		L,support_data=self.generate_L(dataset,min_support)#根据频繁项集和支持度生成关联规则
		rule_list = []#保存满足置信度的规则
		sub_set_list = []#该数组保存检查过的频繁项
		for i in range(0, len(L)):
			for freq_set in L[i]:#遍历Lk
				for sub_set in sub_set_list:#sub_set_list中保存的是L1到Lk-1
					if sub_set.issubset(freq_set):#检查sub_set是否是freq_set的子集
						#检查置信度是否满足要求，是则添加到规则
						conf = support_data[freq_set] / support_data[freq_set - sub_set]
						big_rule = (freq_set - sub_set, sub_set, conf)
						if conf >= min_conf and big_rule not in rule_list:
							rule_list.append(big_rule)
				sub_set_list.append(freq_set)
		rule_list = sorted(rule_list,key=lambda x:(x[2]),reverse=True)
		return rule_list

#---------------------------------------------------------------------------------#
#Apriori_hash 算法
class Apriori_hash():
    ##散列技术在此实现
    ##基于散列技术一次遍历数据，即可生成l1，l2，l3
    ##不生成l4是因为迭代生成候选项时导致可能性太多，数据量大时占用内存太大
    def create_l1_l3(self,data_set,support_data,min_support):#基于散列技术一次遍历数据集生成L1,L2,L3
        L=[set() for i in range(3)]#用于保存频繁项
        item_count={}
        for i in tqdm(data_set):#一次遍历数据集
            l=len(i)
            for j in range(1,4):##生成大小从1到3的候选项，暂时保存到item_count
                self.increase_ck_item(i,[],l,j,0,item_count)
        for item in item_count:#判断各候选项是否满足最小支持度min_support
            if item_count[item] >= min_support:
                L[len(item)-1].add(item)#满足条件，添加到指定的频繁项集中
                support_data[item] = item_count[item]
        return L

    def increase_ck_item(self,item,temp,l,size,index,item_count):#递归生成候选项(dfs方法)
        if len(temp)==size:
            ck_item=frozenset(temp)
            if ck_item not in item_count:
                item_count[ck_item]=1
            else:
                item_count[ck_item]+=1
            return
        for i in range(index,l):
            temp.append(item[i])
            self.increase_ck_item(item,temp,l,size,i+1,item_count)
            temp.pop()

    def create_ck(self,Lk_1,size):#通过频繁项集Lk-1创建ck候选项集
        Ck = set()
        l = len(Lk_1)
        lk_list = list(Lk_1)
        for i in range(l):
            for j in range(i+1, l):#两次遍历Lk-1，找出前n-1个元素相同的项
                l1 = list(lk_list[i])
                l2 = list(lk_list[j])
                l1.sort()
                l2.sort()
                if l1[0:size-2] == l2[0:size-2]:#只有最后一项不同时，生成下一候选项
                    Ck_item = lk_list[i] | lk_list[j]
                    if self.has_infrequent_subset(Ck_item, Lk_1):#检查该候选项的子集是否都在Lk-1中
                        Ck.add(Ck_item)
        return Ck

    def has_infrequent_subset(self,Ck_item, Lk_1):#检查候选项Ck_item的子集是否都在Lk-1中
        for item in Ck_item: 
            sub_Ck = Ck_item - frozenset([item])
            if sub_Ck not in Lk_1:
                return False
        return True

    def generate_lk_by_ck(self,data_set,ck,min_support,support_data):#通过候选项ck生成lk，并将各频繁项的支持度保存到support_data字典中
        item_count={}#用于标记各候选项在数据集出现的次数
        Lk = set()
        for t in tqdm(data_set):#遍历数据集
            for item in ck:#检查候选集ck中的每一项是否出现在事务t中
                if item.issubset(t):
                    if item not in item_count:
                        item_count[item] = 1
                    else:
                        item_count[item] += 1
        t_num = float(len(data_set))
        for item in item_count:#将满足支持度的候选项添加到频繁项集中
            if item_count[item] >= min_support:
                Lk.add(item)
                support_data[item] = item_count[item]
        return Lk
        
    def generate_L(self,data_set, min_support):#用于生成所有频繁项集的主函数，k为最大频繁项的大小
        support_data = {} #用于保存各频繁项的支持度
        L=self.create_l1_l3(data_set,support_data,min_support)
        Lksub=L[-1].copy() #初始时Lk-1=L3
        i=4
        while(True):
            Ci = self.create_ck(Lksub, i)  #根据Lk-1生成Ck
            Li = self.generate_lk_by_ck(data_set, Ci, min_support, support_data) #根据Ck生成Lk
            if len(Li)==0:break
            Lksub = Li.copy()  #下次迭代时Lk-1=Lk
            L.append(Lksub)
            i+=1
        for i in range(len(L)):
            print("frequent item {}：{}".format(i+1,len(L[i])))
        return L, support_data

    def generate_R(self,dataset, min_support, min_conf):
        L,support_data=self.generate_L(dataset,min_support)#根据频繁项集和支持度生成关联规则
        rule_list = []#保存满足置信度的规则
        sub_set_list = []#该数组保存检查过的频繁项
        for i in range(0, len(L)):
            for freq_set in L[i]:#遍历Lk
                for sub_set in sub_set_list:#sub_set_list中保存的是L1到Lk-1
                    if sub_set.issubset(freq_set):#检查sub_set是否是freq_set的子集
                        #检查置信度是否满足要求，是则添加到规则
                        conf = support_data[freq_set] / support_data[freq_set - sub_set]
                        big_rule = (freq_set - sub_set, sub_set, conf)
                        if conf >= min_conf and big_rule not in rule_list:
                            rule_list.append(big_rule)
                sub_set_list.append(freq_set)
        rule_list = sorted(rule_list,key=lambda x:(x[2]),reverse=True)
        return rule_list

#---------------------------------------------------------------------------------#
#Apriori_plus 算法
class Apriori_plus():

    #数据集压缩
    def data_compress(self,data_set):
        ans={}
        for i in data_set:
            if frozenset(i) not in ans:
                ans[frozenset(i)]=1
            else:
                ans[frozenset(i)]+=1
        return ans

    ##散列技术在此实现
    ##基于散列技术一次遍历数据，即可生成l1，l2，l3
    ##不生成l4是因为迭代生成候选项时导致可能性太多，数据量大时占用内存太大
    def create_l1_l3(self,data_dic,support_data,min_support):#基于散列技术一次遍历数据集生成L1,L2,L3
        L=[set() for i in range(3)]#用于保存频繁项
        item_count={}
        for i in tqdm(data_dic):#一次遍历数据集
            l=len(i)
            item=list(i)
            item.sort()
            for j in range(1,4):##生成大小从1到3的候选项，暂时保存到item_count
                self.increase_ck_item(data_dic[i],item,[],l,j,0,item_count)
        for item in item_count:#判断各候选项是否满足最小支持度min_support
            if item_count[item] >= min_support:
                L[len(item)-1].add(item)#满足条件，添加到指定的频繁项集中
                support_data[item] = item_count[item] 
        return L

    def increase_ck_item(self,count,item,temp,l,size,index,item_count):#递归生成候选项(dfs方法)
        if len(temp)==size:
            ck_item=frozenset(temp)
            if ck_item not in item_count:
                item_count[ck_item]=count
            else:
                item_count[ck_item]+=count
            return
        for i in range(index,l):
            temp.append(item[i])
            self.increase_ck_item(count,item,temp,l,size,i+1,item_count)
            temp.pop()

    def create_ck(self,Lk_1,size):#通过频繁项集Lk-1创建ck候选项集
        Ck = set()
        l = len(Lk_1)
        lk_list = list(Lk_1)
        for i in range(l):
            for j in range(i+1, l):#两次遍历Lk-1，找出前n-1个元素相同的项
                l1 = list(lk_list[i])
                l2 = list(lk_list[j])
                l1.sort()
                l2.sort()
                if l1[0:size-2] == l2[0:size-2]:#只有最后一项不同时，生成下一候选项
                    Ck_item = lk_list[i] | lk_list[j]
                    if self.has_infrequent_subset(Ck_item, Lk_1):#检查该候选项的子集是否都在Lk-1中
                        Ck.add(Ck_item)
        return Ck

    def has_infrequent_subset(self,Ck_item, Lk_1):#检查候选项Ck_item的子集是否都在Lk-1中
        for item in Ck_item: 
            sub_Ck = Ck_item - frozenset([item])
            if sub_Ck not in Lk_1:
                return False
        return True

    def generate_lk_by_ck(self,data_dic,ck,min_support,support_data,flag):#通过候选项ck生成lk，并将各频繁项的支持度保存到support_data字典中
        item_count={}#用于标记各候选项在数据集出现的次数
        Lk = set()
        index=-1
        for t in tqdm(data_dic):
            index+=1
            temp_flag=False
            if not flag[index]:continue
            for item in ck:
                if item.issubset(t):
                    temp_flag=True
                    if item not in item_count:
                        item_count[item] = data_dic[t]
                    else:
                        item_count[item] += data_dic[t]
            flag[index]=temp_flag
        t_num = float(len(data_dic))
        for item in item_count:#将满足支持度的候选项添加到频繁项集中
            if item_count[item] >= min_support:
                Lk.add(item)
                support_data[item] = item_count[item]
        return Lk
        
    def generate_L(self,data_set, min_support):#用于生成所有频繁项集的主函数，k为最大频繁项的大小
        data_dic=self.data_compress(data_set)
        support_data = {} #用于保存各频繁项的支持度
        L=self.create_l1_l3(data_dic,support_data,min_support)
        Lksub=L[-1].copy() #初始时Lk-1=L3
        i=4
        flag=[True for _ in range(len(data_dic))]
        while(True):
            Ci = self.create_ck(Lksub, i)  #根据Lk-1生成Ck
            Li = self.generate_lk_by_ck(data_dic, Ci, min_support, support_data,flag) #根据Ck生成Lk
            if len(Li)==0:break
            Lksub = Li.copy()  #下次迭代时Lk-1=Lk
            L.append(Lksub)
            i+=1
        for i in range(len(L)):
            print("frequent item {}：{}".format(i+1,len(L[i])))
        return L, support_data

    def generate_R(self,data_set, min_support, min_conf):
        L,support_data=self.generate_L(data_set,min_support)#根据频繁项集和支持度生成关联规则
        rule_list = []#保存满足置信度的规则
        sub_set_list = []#该数组保存检查过的频繁项
        for i in range(0, len(L)):
            for freq_set in L[i]:#遍历Lk
                for sub_set in sub_set_list:#sub_set_list中保存的是L1到Lk-1
                    if sub_set.issubset(freq_set):#检查sub_set是否是freq_set的子集
                        #检查置信度是否满足要求，是则添加到规则
                        conf = support_data[freq_set] / support_data[freq_set - sub_set]
                        big_rule = (freq_set - sub_set, sub_set, conf)
                        if conf >= min_conf and big_rule not in rule_list:
                            rule_list.append(big_rule)
                sub_set_list.append(freq_set)
        rule_list = sorted(rule_list,key=lambda x:(x[2]),reverse=True)
        return rule_list

#---------------------------------------------------------------------------------#
#Fp_growth_plus 算法
class Node:
	def __init__(self, node_name,count,parentNode):
		self.name = node_name
		self.count = count
		self.nodeLink = None#根据nideLink可以找到整棵树中所有nodename一样的节点
		self.parent = parentNode#父亲节点
		self.children = {}#子节点{节点名字:节点地址}

class Fp_growth_plus():

	def data_compress(self,data_set):
	    data_dic={}
	    for i in data_set:
	        if frozenset(i) not in data_dic:
	            data_dic[frozenset(i)]=1
	        else:
	            data_dic[frozenset(i)]+=1
	    return data_dic

	def update_header(self,node, targetNode):#更新headertable中的node节点形成的链表
		while node.nodeLink != None:
			node = node.nodeLink
		node.nodeLink = targetNode

	def update_fptree(self,items, count,node, headerTable):#用于更新fptree
		if items[0] in node.children:
			# 判断items的第一个结点是否已作为子结点
			node.children[items[0]].count+=count
		else:
			# 创建新的分支
			node.children[items[0]] = Node(items[0],count,node)
			# 更新相应频繁项集的链表，往后添加
			if headerTable[items[0]][1] == None:
				headerTable[items[0]][1] = node.children[items[0]]
			else:
				self.update_header(headerTable[items[0]][1], node.children[items[0]])
			# 递归
		if len(items) > 1:
			self.update_fptree(items[1:],count, node.children[items[0]], headerTable)

	def create_fptree(self,data_dic, min_support,flag=False):#建树主函数
		'''
		根据data_dic创建fp树
		header_table结构为
		{"nodename":[num,node],..} 根据node.nodelink可以找到整个树中的所有nodename
		'''
		item_count = {}#统计各项出现次数
		for t in data_dic:#第一次遍历，得到频繁一项集
			for item in t:
				if item not in item_count:
					item_count[item]=data_dic[t]
				else:
					item_count[item]+=data_dic[t]
		headerTable={}
		for k in item_count:#剔除不满足最小支持度的项
			if item_count[k] >= min_support:
				headerTable[k]=item_count[k]
		
		freqItemSet = set(headerTable.keys())#满足最小支持度的频繁项集
		if len(freqItemSet) == 0:
			return None, None
		for k in headerTable:
			headerTable[k] = [headerTable[k], None] # element: [count, node]
		tree_header = Node('head node',1,None)
		if flag:
			ite=tqdm(data_dic)
		else:
			ite=data_dic
		for t in ite:#第二次遍历，建树
			localD = {}
			for item in t:
				if item in freqItemSet: # 过滤，只取该样本中满足最小支持度的频繁项
					localD[item] = headerTable[item][0] # element : count
			if len(localD) > 0:
				# 根据全局频数从大到小对单样本排序
				order_item = [v[0] for v in sorted(localD.items(), key=lambda x:x[1], reverse=True)]
				# 用过滤且排序后的样本更新树
				self.update_fptree(order_item,data_dic[t],tree_header, headerTable)
		return tree_header, headerTable

	def find_path(self,node, nodepath):
		'''
		递归将node的父节点添加到路径
		'''
		if node.parent != None:
			nodepath.append(node.parent.name)
			self.find_path(node.parent, nodepath)

	def find_cond_pattern_base(self,node_name, headerTable):
		'''
		根据节点名字，找出所有条件模式基
		'''
		treeNode = headerTable[node_name][1]
		cond_pat_base = {}#保存所有条件模式基
		while treeNode != None:
			nodepath = []
			self.find_path(treeNode, nodepath)
			if len(nodepath) > 1:
				cond_pat_base[frozenset(nodepath[:-1])] = treeNode.count 
			treeNode = treeNode.nodeLink 
		return cond_pat_base

	def create_cond_fptree(self,headerTable, min_support, temp, freq_items,support_data):
		# 最开始的频繁项集是headerTable中的各元素
		freqs = [v[0] for v in sorted(headerTable.items(), key=lambda p:p[1][0])] # 根据频繁项的总频次排序
		for freq in freqs: # 对每个频繁项
			freq_set = temp.copy()
			freq_set.add(freq)
			freq_items.add(frozenset(freq_set))
			if frozenset(freq_set) not in support_data:#检查该频繁项是否在support_data中
				support_data[frozenset(freq_set)]=headerTable[freq][0]
			else:
				support_data[frozenset(freq_set)]+=headerTable[freq][0]

			cond_pat_base = self.find_cond_pattern_base(freq, headerTable)#寻找到所有条件模式基
			#创建条件模式树
			cond_tree, cur_headtable = self.create_fptree(cond_pat_base, min_support)
			if cur_headtable != None:
				self.create_cond_fptree(cur_headtable, min_support, freq_set, freq_items,support_data) # 递归挖掘条件FP树

	def generate_L(self,data_set,min_support):
		data_dic=self.data_compress(data_set)
		freqItemSet=set()
		support_data={}
		tree_header,headerTable=self.create_fptree(data_dic,min_support,flag=True)#创建数据集的fptree
		#创建各频繁一项的fptree，并挖掘频繁项并保存支持度计数
		self.create_cond_fptree(headerTable, min_support, set(), freqItemSet,support_data)
		
		max_l=0
		for i in freqItemSet:#将频繁项根据大小保存到指定的容器L中
			if len(i)>max_l:max_l=len(i)
		L=[set() for _ in range(max_l)]
		for i in freqItemSet:
			L[len(i)-1].add(i)
		for i in range(len(L)):
			print("frequent item {}:{}".format(i+1,len(L[i]))) 
		return L,support_data 

	def generate_R(self,data_set, min_support, min_conf):
		L,support_data=self.generate_L(data_set,min_support)
		rule_list = []
		sub_set_list = []
		for i in range(0, len(L)):
			for freq_set in L[i]:
				for sub_set in sub_set_list:
					if sub_set.issubset(freq_set) and freq_set-sub_set in support_data:#and freq_set-sub_set in support_data
						conf = support_data[freq_set] / support_data[freq_set - sub_set]
						big_rule = (freq_set - sub_set, sub_set, conf)
						if conf >= min_conf and big_rule not in rule_list:
						    # print freq_set-sub_set, " => ", sub_set, "conf: ", conf
							rule_list.append(big_rule)
				sub_set_list.append(freq_set)
		rule_list = sorted(rule_list,key=lambda x:(x[2]),reverse=True)
		return rule_list
		
#---------------------------------------------------------------------------------#

if __name__=="__main__":
	##config

	# filename="药方.xls"
	# min_support=600#最小支持度
	# min_conf=0.9#最小置信度
	# size=8#频繁项最大大小

	filename="groceries.csv"
	min_support=25#最小支持度   min_support不应该是个百分数吗  这里直接使用出现的次数 其实也是一样的  如果是百分数，则要出现的次数/交易次数
	min_conf=0.7#最小置信度
	size=5#频繁项最大大小 	
	current_path=os.getcwd()#获取当前文件路径   'C:\\Users\\lenovo\\Desktop\\data_mine-master'

	#if not os.path.exists(current_path+"/log"):
		#os.mkdir("log")


	path=current_path+"\\dataset\\"+filename#获取需要加载的文件名称
	save_path=current_path+"/log/"+filename.split(".")[0]+"_apriori.txt"#设置存储的log文件名称

	#加载处理数据
	data=load_data(path)#去重  list列表

	apriori=Apriori()

	rule_list=apriori.generate_R(data,min_support=15,min_conf=0.7)

	save_rule(rule_list,save_path)

