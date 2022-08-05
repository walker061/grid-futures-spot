# -*- coding: utf-8 -*-
from app.BinanceAPI import BinanceAPI
from app.authorization import api_key,api_secret
from data.runBetData import RunBetData
from app.dingding import Message
import time
# import os
# import heartrate; 
# heartrate.trace(browser=True)

# os.environ["http_proxy"] = "http://127.0.0.1:7890"
# os.environ["https_proxy"] = "http://127.0.0.1:7890"


binan = BinanceAPI(api_key,api_secret)
runbet = RunBetData()
msg = Message()

class Run_Main():

    def __init__(self):
        self.coinType = runbet.get_cointype()  # 交易币种
        self.profitRatio = runbet.get_profit_ratio() # 止盈比率
        self.doubleThrowRatio = runbet.get_double_throw_ratio() # 补仓比率
        pass


    def loop_run(self):
        while True:
            cur_market_price = binan.get_future_price(runbet.get_cointype()) # 当前合约交易对市价
            grid_sell_price = runbet.get_sell_price() # 网格开仓价
            future_quantity = runbet.get_future_quantity()   # 做空币数
            future_step = runbet.get_future_step() # 当前做空次数
            total_step = runbet.get_total_step() #总执行次数
            print("当前合约市价:",cur_market_price,           
            "网格开仓价",grid_sell_price,
            "设定做空币数",future_quantity,
            "当前做空仓位",future_step,
            "当前总执行次数",total_step
            )
            cur_info = "当前合约市价:{a1},网格开仓价:{a2},设定做空数量:{a3},当前做空仓位:{a4},当前总执行次数:{a5},".format(a1=cur_market_price,a2=grid_sell_price,a3=future_quantity,a4=future_step,a5=total_step)
            msg.dingding_warn(cur_info)           

            if grid_sell_price >= cur_market_price:   # 网格开仓价>=市场价，需对冲，开空单
                print("1.网格开仓价>=市场价，需对冲，准备开空单")
                # 说明当前已有空单,不执行 
                if future_step != 0: 
                    print("2.当前仓位",future_step,"无需操作")
                    time.sleep(10*1)    
                # 当前没空单，开仓
                else:               
                    print("2.当前仓位",future_step,"执行开空操作")
                    #市价开空
                    future_res = msg.sell_market_future_msg(self.coinType, future_quantity) 
                    if future_res['orderId']:                    
                        runbet.set_future_step(future_step+1) 
                        runbet.set_total_step(total_step+1)
                        # 挂单后，停止运行1分钟
                        time.sleep(50*1) 
                
            elif grid_sell_price < cur_market_price:  # 网格开仓价<市场价，无需对冲，平空单
                print("1.网格开仓价<市场价，无需对冲，平空单")
                # 有仓位，执行平仓
                if future_step != 0:
                    print("2.当前仓位",future_step,"执行平仓操作")
                    msg.cancel_all_orders_msg(self.coinType, future_quantity) 
                    runbet.set_future_step(future_step-1) 
                    runbet.set_total_step(total_step+1)
                    # 挂单后，停止运行1分钟
                    time.sleep(50*1) 
                # 如果没仓位，退出
                else:
                    print("2.当前仓位",future_step,"无需操作")
                    time.sleep(10*1)      
            else:
                print("当前市价：{market_price}。未能满足交易,继续运行".format(market_price = cur_market_price))
                time.sleep(20*1) # 为了不被币安api请求次数限制
# 运行
if __name__ == "__main__":       
   instance = Run_Main()    
   instance.loop_run()
