# -*- coding: utf-8 -*-
from app.BinanceAPI import BinanceAPI
from app.authorization import api_key,api_secret,api_secret1,api_key1
from data.runBetData import RunBetData
from app.dingding import Message
import time
import datetime
from time import strftime
import os

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
            future_quantity = runbet.get_future_quantity()   # 做空币数
            future_step = runbet.get_future_step() # 当前做空次数
            total_step = runbet.get_total_step() #总执行次数
            now=datetime.datetime.now()
            bjnow = now + datetime.timedelta(hours=8)
            now_str = now.strftime("%Y-%m-%d %H:%M:%S") #洛杉矶时间   
            bjnow_str = bjnow.strftime("%Y-%m-%d %H:%M:%S") #北京时间
            balance_res = BinanceAPI(api_key1,api_secret1).get_user_data_balance() #当前账户USDT
            balance_usdt = 0
            for item in balance_res:
                if item['asset'] == 'USDT':
                    balance_usdt = item['balance']            
            profit = float(balance_usdt) - init_usdt #计算盈利 
            r_action = "1"
            #1770*1.001=1771.77
            if cur_market_price <= grid_sell_price* 1.001 and future_step == 0:   # 网格开仓价>=市场价且无仓位，需对冲，开空单
                r_action = "市场价<=网格开仓价且无仓位，需对冲，开空单"
               #市价开空
                future_res = msg.sell_market_future_msg(self.coinType, future_quantity,cur_market_price) 
                if future_res['orderId']:                    
                    runbet.set_future_step(future_step+1) 
                    runbet.set_total_step(total_step+1)
                    # 挂单后，停止运行1分钟
                    time.sleep(20*1) 
            #1770*.999=1768.23
            elif cur_market_price > grid_sell_price * 0.999 and future_step != 0 :  # 网格开仓价<市场价且有仓位，无需对冲，平空单
                r_action = "市场价>网格开仓价且有仓位，无需对冲，平空单" 
                #市价平仓
                cancel_res = msg.cancel_all_orders_msg(self.coinType, future_quantity,cur_market_price) 
                if cancel_res['orderId']:   
                    runbet.set_future_step(future_step-1) 
                    runbet.set_total_step(total_step+1)
                    # 挂单后，停止运行1分钟
                    time.sleep(20*1)            
            else:
                r_action = ("当前市价：{market_price}。未能满足交易,继续运行".format(market_price = cur_market_price))
                time.sleep(10*1) # 为了不被币安api请求次数限制            
            cur_info = "报警：当前合约市价:{a1},网格开仓价:{a2},设定做空数量:{a3},当前做空仓位:{a4},当前总执行次数:{a5},执行:{a9},当前洛杉矶服务器时间:{a6},当前服务器北京时间:{a7},当前盈亏:{a8}USDT".format(a1=cur_market_price,a2=grid_sell_price,a3=future_quantity,a4=future_step,a5=total_step,a6=now_str,a7=bjnow_str,a8=round(profit,3),a9=r_action)
            print(cur_info)
            msg.dingding_warn(cur_info)  
# 运行
if __name__ == "__main__":       
   instance = Run_Main()    
   instance.loop_run()
