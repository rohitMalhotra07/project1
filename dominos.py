from collections import OrderedDict
from random import randint

import threading
import Queue
import time
import json

OrderList=[]
Orders={}
pizzaQueue=Queue.Queue() #queue used by pizza cook using lock on the queue in case there are more than 1 pizza cook
sideQueue=Queue.Queue() #similar to pizza cook
exitCookPizzaFlag=0  # flag to signal every pizza cook to exit
exitCookSideFlag=0
exitPackerFlag=0 
exitDeliveryFlag=0 # flag to signal every delivery man to exit
packerQueue=Queue.Queue() # queue used by packer and using lock on this queue if there are more than 1 packer
deliveryQueue=Queue.Queue()
packLock=threading.Lock()
deliveryLock=threading.Lock()

class cookPizza (threading.Thread):

	def __init__(self , pizzaQueue,name):
		threading.Thread.__init__(self)
		self.q = pizzaQueue
		self.name=name

	def run(self):
		#print "Starting cook pizza"
		cook_pizza(self.q,self.name)
		#print "Exiting cook pizza"

class cookSides (threading.Thread):
	def __init__(self,sideQueue,name):
		threading.Thread.__init__(self)
		self.q=sideQueue
		self.name=name
	def run(self):
		#print "Starting cook sides"
		cook_side(self.q,self.name)
		#print "Exiting cook sides"

class packer (threading.Thread):
	def __init__(self,packerQueue,name):
		threading.Thread.__init__(self)
		self.q=packerQueue
		self.name=name
	def run(self):
		packer_process(self.q,self.name)

class deliveryMan (threading.Thread):
	def __init__(self,deliveryQueue,name):
		threading.Thread.__init__(self)
		self.q=deliveryQueue
		self.name=name
	def run(self):
		delivery_process(self.q,self.name)

def delivery_process(q,name):
	global exitDeliveryFlag
	while exitDeliveryFlag!=3: #because there are 2 packers
		deliveryLock.acquire()
		if not q.empty():
			temp=q.get()
			time.sleep(randint(4,8))
			print 'delivered {0} by {1}'.format(temp['orderID'],name)
			deliveryLock.release()
		else:
			deliveryLock.release()

	print 'exiting delivery'


def packer_process(q,name):
	global exitPackerFlag
	global deliveryQueue
	global deliveryLock
	global exitDeliveryFlag
	while exitPackerFlag !=4: # four because there are 3 cooks currently running 2 pizza and 1 side
		packLock.acquire()
		if not q.empty():
			#print q.qsize()
			temp=q.get()
			id=temp['orderID']
			for item in OrderList:
				if item['orderID']==id:
					item['total']-=1
					if item['total']==0:
						print 'order with orderid {0} is packed by {1}'.format(id,name)
						deliveryLock.acquire()
						deliveryQueue.put(temp)
						deliveryLock.release()

						
			packLock.release()
		else:
			packLock.release()
	exitDeliveryFlag+=1
	print 'done packing'

def cook_pizza(q,name):
	global exitCookPizzaFlag
	global exitPackerFlag
	global packerQueue
	while not exitCookPizzaFlag:
		cookPizzaLock.acquire()
		if not q.empty():
			pizza=q.get()
			print 'preparing pizza({0})of orderId {1} by {2}'.format(pizza['name'],pizza['orderID'],name)
			cookPizzaLock.release()
			time.sleep(pizza['time_in_seconds']/100)
			pizza['status']='done'
			packLock.acquire()
			#print 'pack lock acquired pizza'
			packerQueue.put(pizza)
			packLock.release()
			#print 'pack lock released pizza'
			
		else:
			cookPizzaLock.release()
	exitPackerFlag=exitPackerFlag+1
	print "done cooking pizza"

def cook_side(q,name):
	global exitCookSideFlag
	global exitPackerFlag
	global packerQueueSide
	while not exitCookSideFlag:
		cookSideLock.acquire()
		if not q.empty():			
			side=q.get()
			print 'preparing side ({0}) of orderId {1} by {2}'.format(side['name'],side['orderID'],name)
			cookSideLock.release()
			time.sleep(side['time_in_seconds']/100)
			side['status']='done'
			packLock.acquire()
			#print 'pack lock acquired side'
			packerQueue.put(side)
			packLock.release()
			#print 'pack lock released side'
			
		else:
			cookSideLock.release()
	exitPackerFlag=exitPackerFlag+1
	print "done cooking side"


def OrderTaker():
	global pizzaQueue
	global sideQueue
	global OrderList
	global packLock
	global packerQueue
	

	for order in OrderList:
		temp=0
		for pizza in order['pizzas']:
			pizzaInfo={}
			pizzaInfo['name']=pizza['name']
			pizzaInfo['time_in_seconds']=pizza['time_in_seconds']
			pizzaInfo['orderID']=order['orderID']
			pizzaInfo['status']='undone'
			temp=temp+1
			pizzaQueue.put(pizzaInfo)
		for side in order['sides']:
			sideInfo={}
			sideInfo['name']=side['name']
			sideInfo['time_in_seconds']=side['time_in_seconds']
			sideInfo['orderID']=order['orderID']
			sideInfo['status']='undone'
			temp=temp+1
			sideQueue.put(sideInfo)
		for beverage in order['beverages']:
			beverageInfo={}
			beverageInfo['name']=beverage['name']
			beverageInfo['quantity']=beverage['quantity']
			beverageInfo['orderID']=order['orderID']
			temp=temp+1
			packLock.acquire()
			packerQueue.put(beverageInfo)
			packLock.release()

		order['total']=temp
	#print OrderList

def Client():
	json_data=open("order.json")
	global Orders
	Orders=json.load(json_data,object_pairs_hook=OrderedDict)
	global OrderList
	orderID=0
	for order in Orders["orders"]:
		orderID=orderID+1
		order['orderID']=orderID
		order['total']=0
		OrderList.append(order)
		
	#print OrderList


if __name__ == '__main__':
	Client()
	OrderTaker()
	cookPizzaLock=threading.Lock()
	cookSideLock=threading.Lock()
	cook1=cookPizza(pizzaQueue,"cook1")
	cook11=cookPizza(pizzaQueue,"cook11")
	cook2=cookSides(sideQueue,"cook2")
	packer1=packer(packerQueue,"packer1")
	packer2=packer(packerQueue,"packer2")
	deliveryMan1=deliveryMan(deliveryQueue,"deliveryMan1")
	deliveryMan2=deliveryMan(deliveryQueue,"deliveryMan2")
	cook1.start()
	cook2.start()
	cook11.start()
	packer1.start()
	packer2.start()
	deliveryMan1.start()
	deliveryMan2.start()
	while not pizzaQueue.empty():
		pass
	exitCookPizzaFlag=1
	while not sideQueue.empty():
		pass
	exitCookSideFlag=1
	while exitPackerFlag<3:
		pass
	exitPackerFlag=4 #packer should exit only when all the cooks are done cooking and all items are packed 
	while  exitDeliveryFlag<2:
		pass
	exitDeliveryFlag=3 # delivery man should exit when all the packers have exit and all deliveries are done 
	