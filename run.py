# -*- coding: utf-8 -*-
# from locale import ABDAY_1
from warnings import catch_warnings
from app.BinanceAPI import BinanceAPI
from app.authorization import api_key,api_secret,api_secret1,api_key1
from data.runBetData import RunBetData
from app.dingding import Message
import time
import datetime
from time import strftime
# import os

# os.environ["http_proxy"] = "http://127.0.0.1:7890"
# os.environ["https_proxy"] = "http://127.0.0.1:7890"


binan = BinanceAPI(api_key,api_secret)
runbet = RunBetData()
msg = Message()

class Run_Main():

    def __init__(self):
        self.coinType = runbet.get_cointype()  # 交易币种
        pass

    def loop_run(self):
        while True:
            cur_market_price = binan.get_future_price(runbet.get_cointype()) # 当前合约交易对市价
            init_usdt= runbet.get_initial_usdt_balance() #初始USDT            
            grid_sell_price = runbet.get_sell_price() # 网格开仓价
            grid_sell_price1 = round(grid_sell_price* 1.0005 ,2)
            grid_sell_price2 = round(grid_sell_price* 0.999 ,2)
            future_quantity = runbet.get_future_quantity()   # 做空币数
            future_step = runbet.get_future_step() # 当前做空次数
            total_step = runbet.get_total_step() #总执行次数
            now=datetime.datetime.now()
            bjnow = now + datetime.timedelta(hours=8)
            now_str = now.strftime("%Y-%m-%d %H:%M:%S") #洛杉矶时间   
            bjnow_str = bjnow.strftime("%Y-%m-%d %H:%M:%S") #北京时间
            balance_res = BinanceAPI(api_key1,api_secret1).get_user_data_balance() #当前账户USDT            
            account_res = BinanceAPI(api_key1,api_secret1).get_user_data_account() #当前账户状态    
            totalUnrealizedProfit = account_res['totalUnrealizedProfit'] #持仓未实现盈亏总额, 仅计算usdt资产
            
            #设置订单号
            try: 
                #有订单                
                open_orders = BinanceAPI(api_key1,api_secret1).get_future_openOrders(self.coinType) #当前账户挂单 
                # print(open_orders) 
                # print(open_orders[0]['orderId'])             
                runbet.set_cur_sell_orderid(open_orders[0]['orderId'])
            except BaseException as e:
                #无订单
                runbet.set_cur_sell_orderid(0)
            cur_sell_orderid = runbet.get_cur_sell_orderid() #开仓合约ID
            
            # print(totalUnrealizedProfit)
            # print(cur_sell_orderid)

            #设置仓位
            if abs(float(totalUnrealizedProfit)) > 0:
                runbet.set_future_step(1)#已吃单,当前对冲持仓为1                           
            else:
                runbet.set_future_step(0)#已强平,无持仓     
            future_step = runbet.get_future_step() # 仓位重新获取
            
            # print("当前仓位",future_step)
            # delete_all_open_orders = BinanceAPI(api_key1,api_secret1).delete_all_open_orders(self.coinType) #关闭所有挂单
            # print("取消所有挂单",delete_all_open_orders)

            balance_usdt = 0
            for item in balance_res:
                if item['asset'] == 'USDT':
                    balance_usdt = item['balance']            
            profit = float(balance_usdt) - init_usdt #计算盈利 
            r_action = "1"
           
            if cur_market_price <= grid_sell_price and cur_sell_orderid == 0:   # 市场价<=网格开仓价且无挂单，需对冲，开空单
                r_action = "市场价{a1}<=网格价{a2}且无仓位，需对冲，开空单".format(a1=cur_market_price,a2=grid_sell_price)
                cur_info = "报警：当前市价:{a1},网格价:{a2},做空价{b1},平仓价{a2},浮盈浮亏{b3},订单号{b4},设定做空数量:{a3},当前做空仓位:{a4},当前总执行次数:{a5},执行操作:|{a9}|,当前洛杉矶服务器时间:{a6},当前服务器北京时间:{a7},当前盈亏:|{a8}USDT|".format(a1=cur_market_price,a2=grid_sell_price,a3=future_quantity,a4=future_step,a5=total_step,a6=now_str,a7=bjnow_str,a8=round(profit,3),a9=r_action,b1=grid_sell_price1,b3=totalUnrealizedProfit,b4=cur_sell_orderid)
                print(cur_info)
                msg.dingding_warn(cur_info)   
                #市价开空
                # future_res = msg.sell_market_future_msg(self.coinType, future_quantity,cur_market_price) 
                # if future_res['orderId']:                    
                #     runbet.set_future_step(future_step+1) 
                #     runbet.set_total_step(total_step+1)
                #     # 挂单后，停止运行1分钟
                #     time.sleep(20*1)
                #更新为 限价开空
                future_res = msg.sell_limit_future_msg(self.coinType, future_quantity,grid_sell_price1) 
                if future_res['orderId']:                    
                    runbet.set_future_step(future_step+1) 
                    runbet.set_total_step(total_step+1)
                    # 挂单后，停止运行1分钟
                    time.sleep(5*1)
           
            elif cur_market_price > grid_sell_price2 and future_step != 0 :  # 网格开仓价<市场价且有仓位，无需对冲，平空单
                r_action = "市价{a1}>平仓价{a2}且有仓位，无需对冲，平空单".format(a1=cur_market_price,a2=grid_sell_price2)
                cur_info = "报警：当前市价:{a1},网格价:{a2},做空价{b1},平仓价{a2},浮盈浮亏{b3},订单号{b4},设定做空数量:{a3},当前做空仓位:{a4},当前总执行次数:{a5},执行操作:|{a9}|,当前洛杉矶服务器时间:{a6},当前服务器北京时间:{a7},当前盈亏:|{a8}USDT|".format(a1=cur_market_price,a2=grid_sell_price,a3=future_quantity,a4=future_step,a5=total_step,a6=now_str,a7=bjnow_str,a8=round(profit,3),a9=r_action,b1=grid_sell_price1,b3=totalUnrealizedProfit,b4=cur_sell_orderid)
                print(cur_info)
                msg.dingding_warn(cur_info)   
                #市价平仓
                cancel_res = msg.cancel_all_orders_msg(self.coinType, future_quantity,cur_market_price) 
                if cancel_res['orderId']:   
                    runbet.set_future_step(future_step-1) 
                    runbet.set_total_step(total_step+1)
                    # 挂单后，停止运行1分钟
                    time.sleep(5*1)            
            else:
                r_action = ("市价{a1},做空价{a2},平仓价{a3},无需操作,继续运行").format(a1=cur_market_price,a2=grid_sell_price1,a3=grid_sell_price)
                cur_info = "报警：当前市价:{a1},网格价:{a2},做空价{b1},平仓价{a2},浮盈浮亏{b3},订单号{b4},设定做空数量:{a3},当前做空仓位:{a4},当前总执行次数:{a5},执行操作:|{a9}|,当前洛杉矶服务器时间:{a6},当前服务器北京时间:{a7},当前盈亏:|{a8}USDT|".format(a1=cur_market_price,a2=grid_sell_price,a3=future_quantity,a4=future_step,a5=total_step,a6=now_str,a7=bjnow_str,a8=round(profit,3),a9=r_action,b1=grid_sell_price1,b3=totalUnrealizedProfit,b4=cur_sell_orderid)
                print(cur_info)
                msg.dingding_warn(cur_info)  
                time.sleep(5*1) # 为了不被币安api请求次数限制          
# 运行
if __name__ == "__main__":       
   instance = Run_Main()    
   instance.loop_run()
