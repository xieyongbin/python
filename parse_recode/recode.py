""" 7KW交流桩交易记录解析
    V1.1：
        修复V1.0使用time.mktime()转成了UTC时间，而非本地时间
    V1.2:
        支持5个时间段的交易记录，不再支持4个时间段
"""

import os
import time
from enum import Enum

#声明
prompt = """
7KW交流桩交易记录程序V1.2
支持最多5个时间段，交易记录只有4个时间段的请使用V1.1，V1.2不再支持
"""
#生成的文件名
new_file_name = 'recode_list'

#交易记录文件预留的时间段个数
recode_time_seq_num = 5

class Start_Mode(Enum):
    """ 定义一个枚举,启动方式 """
    mode_start_device = 1   #充电系统启动
    mode_start_platform = 2 #运行平台发送启动
    mode_start_other = 3    #其他方式启动

class Bill_Status(Enum):
    """ 定义一个枚举,结算状态 """
    recode_undefine = 0     #未定义
    recode_settlement = 1   #已结算
    recode_unsettlement = 2 #未结算

class Start_Fail_Type(Enum):
    """ 充电失败原因 """
    start_fail_not = 0       #启动未失败
    start_fail_period = 1    #充电机检测错误
    start_fail_demanderr = 2 #需求错误
    start_fail_car = 3       #车子未准备好

class Stop_Reason(Enum):
    """ 停止原因 """
    stop_undefined = 0       #未定义
    stop_initiative = 1      #界面手动停止
    stop_car_chargefull = 2  #车充满停止
    stop_electric_reach = 3  #设置电量达到停止
    stop_money_reach = 4     #设置金额达到停止
    stop_time_reach = 5      #设置时间达到通知
    stop_emergency_err = 6   #急停按钮状态
    stop_spd_err = 7         #防雷器状态
    stop_door_err = 8        #门开关状态
    stop_cp_unconnect = 9    #（cp）状态是否连接
    stop_demand_err = 10     #需求错误
    stop_car_err = 11        #车子故障
    stop_cardmoney_reach = 12#卡内余额用完停止
    stop_cur_oversize = 13   #电流过大停止
    stop_cur_toolittle = 14  #电流过小
    stop_vol_oversize = 15   #电压过大停止
    stop_vol_under = 16      #电压过小
    stop_meter_abnormal = 17 #电表通信异常
    stop_sd_notdetected = 18 #sd卡未检测到
    stop_else_err = 19       #其他原因

class Start_Time_Seq(Enum):
    """ 开始时间段 """
    timequan_undefine = 0    #未定义
    timequan_jian = 1        #尖
    timequan_feng = 2        #峰
    timequan_ping = 3        #平
    timequan_gu = 4          #谷


#交易流水号
charge_serial_num_dict = {
    'uid_low' : 0,          #芯片uid低4字节
    'uid_mid' : 0,          #芯片uid中间4字节
    'uid_high': 0,          #芯片uid高字节
    'end_charge_time': 0,   #1970年到结束充电时间的秒数(结束充电时间)，4字节
    'charge_use_num' : 0    #充电枪使用次数，4字节
}

#时间段信息
time_seg_info_dict = {
    'start_timestamp' : 0,  #充电时间段 N 开始时间,1970 年到开始时间的秒数，4字节
    'end_timestamp': 0,     #充电时间段 N 结束时间,1970 年到开始时间的秒数，4字节
    'power': 0,             #充电时间段 N 电量，比例 0.01 单位kWh，4字节
    'service_price': 0,     #充电时间段 N 服务费单价，比例0.0001，单位元，4字节
    'price':0,              #充电时间段 N 单价，比例0.0001，单位元，4字节
    'service':0,            #充电时间段 N 服务费金额，比例 0.01 单位 元，4字节
    'momey':0               #充电时间段 N 充电金额，比例 0.01 单位 元，4字节
}

def get_int32u_le(n):
    """" 对列表n转成一个INT32U小端的整型 """
    if len(n) < 4:
        print("Should be a list contain 4 items,now %s" % len(n))
        return
    return (n[0] | (n[1] << 8) | (n[2] << 16) | (n[3] << 24) )

def get_int16u_le(n):
    """" 对列表n转成一个INT16U小端的整型 """
    if len(n) < 2:
        print("Should be a list contain 2 items,now %s" % len(n))
        return
    return (n[0] | (n[1] << 8) )

def parse_stop_reason(stop, recode):
    """ 解析停止原因 """
    if stop == Stop_Reason.stop_initiative.value:
        recode['stop_reason'] = '用户主动停止'
    elif stop == Stop_Reason.stop_car_chargefull.value:
        recode['stop_reason'] = '汽车充满停止'
    elif stop == Stop_Reason.stop_electric_reach.value:
        recode['stop_reason'] = '达到设定电量'
    elif stop == Stop_Reason.stop_money_reach.value:
        recode['stop_reason'] = '达到设定金额'
    elif stop == Stop_Reason.stop_time_reach.value:
        recode['stop_reason'] = '达到设定充电时间'
    elif stop == Stop_Reason.stop_emergency_err.value:
        recode['stop_reason'] = '急停'
    elif stop == Stop_Reason.stop_spd_err.value:
        recode['stop_reason'] = '防雷'
    elif stop == Stop_Reason.stop_door_err.value:
        recode['stop_reason'] = '门打开'
    elif stop == Stop_Reason.stop_cp_unconnect.value:
        recode['stop_reason'] = 'CP断开'
    elif stop == Stop_Reason.stop_demand_err.value:
        recode['stop_reason'] = '需求错误'
    elif stop == Stop_Reason.stop_car_err.value:
        recode['stop_reason'] = '汽车故障'
    elif stop == Stop_Reason.stop_cardmoney_reach.value:
        recode['stop_reason'] = '余额不足'
    elif stop == Stop_Reason.stop_cur_oversize.value:
        recode['stop_reason'] = '过流'
    elif stop == Stop_Reason.stop_cur_toolittle.value:
        recode['stop_reason'] = '欠流'
    elif stop == Stop_Reason.stop_vol_oversize.value:
        recode['stop_reason'] = '过压'
    elif stop == Stop_Reason.stop_vol_under.value:
        recode['stop_reason'] = '欠压'
    elif stop == Stop_Reason.stop_meter_abnormal.value:
        recode['stop_reason'] = '电表通信异常'
    elif stop == Stop_Reason.stop_sd_notdetected.value:
        recode['stop_reason'] = '无SD卡'
    elif stop == Stop_Reason.stop_else_err.value:
        recode['stop_reason'] = '其他原因'
    else:
        recode['stop_reason'] = '未定义(%s)' % stop

def parse_start_mode(mode, recode):
    """ 解析启动方式 """
    if mode == Start_Mode.mode_start_device.value:
        recode['start_method'] = '充电系统启动'
    elif mode == Start_Mode.mode_start_platform.value:
        recode['start_method'] = '平台启动'
    elif mode == Start_Mode.mode_start_other.value:
        recode['start_method'] = '其他方式启动'
    else:
        recode['start_method'] = '未定义(%s)' % mode

def parse_err_reason(err_reason, recode):
    """ 充电失败原因 """
    if err_reason == Start_Fail_Type.start_fail_not.value:
        recode['start_fail'] = '无'
    elif err_reason == Start_Fail_Type.start_fail_period.value:
        recode['start_fail'] = '充电机检测错误'
    elif err_reason == Start_Fail_Type.start_fail_demanderr.value:
        recode['start_fail'] = '需求错误'
    elif err_reason == Start_Fail_Type.start_fail_car.value:
        recode['start_fail'] = '汽车未准备好'
    else:
        recode['start_fail'] = '未定义(%s)' % err_reason

def parse_one_recode(recode, num):
    """ 解析一个交易记录 """
    context_str = ''
    #用字典模拟交易记录格式
    charge_recode_dict = {
        'charge_serial_num':charge_serial_num_dict, #交易流水号
        'gun_num' : 0,          #充电枪口号，1字节
        'account' : '',         #卡号, 30字节,ascii
        'bill_status': 0,       #结算标志，1：已结算，2：未结算，1字节
        'car_vin':[],           #ASCII车辆VIN，17字节
        'start_mode':0,         #1:充电系统启动 2：运营平台发送启动 3:其他方式启动 1个字节，暂时没有
        'start_timestamp':0,    #1970年到开始时间的秒数(开始充电时间)，4字节
        'end_timestamp':0,      #1970年到结束时间的秒数(开始结束时间)，4字节
        'charge_power':0,       #充电总电量,比例 0.01 单位kWh，4字节
        'service_charge':0,     #充电服务费,比例 0.01 单位 元，4字节
        'charge_momey':0,       #充电总金额,比例 0.01 单位 元，4字节
        'time_seq_num':0,       #充电经过的时间段个数
        'time_seq':[],          #时间段，time_seg_info_dict
        'start_fail': None,     #电失败原因，1字节
        'stop_reason': None,    #具体停止原因，1字节
        'start_method': None,   #启动方式，1字节
        'charge_time': 0,       #充电时间 分辨率:1分钟，2字节
        'res1': 0,              #预留1,4字节
        'res2': 0               #预留2,4字节
    }

    try:
        with open(recode, 'rb') as f:
            context = f.read()
    except:
        raise

    #1、首先将文件里的十六进制数转成文本,作为原始数据
    context_str = '<%s>文件名: ' % (num) + recode + '\n'
    context_str += '原始数据: '
    for d in context:
        context_str += '0x%02X ' % d
    context_str = context_str.rstrip() #去掉最后的空格
    context_str += '\n'  #原始数据输出格式
    #解析文件里的数据
    #生成交易流水号，共20个字节
    charge_recode_dict['charge_serial_num']['uid_low'] = '%08X' % get_int32u_le(context[0:4])
    charge_recode_dict['charge_serial_num']['uid_mid'] = '%08X' % get_int32u_le(context[4:8])
    charge_recode_dict['charge_serial_num']['uid_high'] = '%08X' % get_int32u_le(context[8:12])
    charge_recode_dict['charge_serial_num']['end_charge_time'] = '%08X' % get_int32u_le(context[12:16])
    charge_recode_dict['charge_serial_num']['charge_use_num'] = '%08X' % get_int32u_le(context[16:20])
    context_str += '交易流水号: ' \
                   + charge_recode_dict['charge_serial_num']['uid_low'] \
                   + charge_recode_dict['charge_serial_num']['uid_mid'] \
                   + charge_recode_dict['charge_serial_num']['uid_high'] \
                   + charge_recode_dict['charge_serial_num']['end_charge_time'] \
                   + charge_recode_dict['charge_serial_num']['charge_use_num'] + '\n'

    #枪号
    charge_recode_dict['gun_num'] = '%02X' % context[20]
    context_str += '枪口号: ' + charge_recode_dict['gun_num'] + '\n'

    #充电账号
    charge_recode_dict['account'] = context[21:51].decode('ascii')  #将字节码转成ascii码字符串
    context_str += '账号: ' + charge_recode_dict['account'] + '\n'

    #结算标志
    if context[51] == Bill_Status.recode_settlement.value:
        charge_recode_dict['bill_status'] = '已结算(%d)' % context[51]
    elif context[51] == Bill_Status.recode_unsettlement.value:
        charge_recode_dict['bill_status'] = '未结算(%d)' % context[51]
    else:
        charge_recode_dict['bill_status'] = '未定义(%d)' % context[51]
    context_str += '结算标志: ' + charge_recode_dict['bill_status'] + '\n'

    #车辆VIN
    charge_recode_dict['car_vin'] = context[52:69].decode('ascii') #将字节码转成ascii码字符串
    context_str += '车辆VIN: ' + charge_recode_dict['car_vin'] + '\n'

    #启动方式，后面C程序应该添加

    #开始时间戳
    index = 69
    start_time = get_int32u_le(context[index:index+4])
    charge_recode_dict['start_timestamp'] = '%d' % start_time
    #将时间戳生成 ‘年-月-日 时：分：秒’格式
    human_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time) )
    context_str += '开始时间: ' + human_time + '(%s)' % (charge_recode_dict['start_timestamp']) + '\n'

    #结束时间戳
    end_time = get_int32u_le(context[index+4:index+8])
    charge_recode_dict['end_timestamp'] = '%d' % end_time
    #将时间戳生成 ‘年-月-日 时：分：秒’格式
    human_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time) )
    context_str += '结束时间: ' + human_time + '(%s)' % (charge_recode_dict['end_timestamp']) + '\n'

    #充电总电量
    charge_recode_dict['charge_power'] = '%s' % (get_int32u_le(context[index+8:index+12]) * 0.01)
    context_str += '充电总电量: '  + charge_recode_dict['charge_power'] + '(KWh)\n'

    #充电服务费
    charge_recode_dict['service_charge'] = '%s' % (get_int32u_le(context[index+12:index+16]) * 0.01)
    context_str += '充电服务费: '  + charge_recode_dict['service_charge'] + '(元)\n'

    #充电总金额
    charge_recode_dict['charge_momey'] = '%s' % (get_int32u_le(context[index+16:index+20]) * 0.01)
    context_str += '充电总金额: '  + charge_recode_dict['charge_momey'] + '(元)\n'

    #经过的时间段个数
    charge_recode_dict['time_seq_num'] = '%s' % context[index+20]
    context_str += '时间段个数: '  + charge_recode_dict['time_seq_num'] + '\n'

    #时间段个数
    time_seq = context[index+20]
    #print("total %s time seq" % time_seq)
    if time_seq > recode_time_seq_num:
        time_seq = recode_time_seq_num #目前只支持最多recode_time_seq_num个时间段
    for i in range(time_seq):
        try:
            charge_recode_dict['time_seq'].append(time_seg_info_dict)
            context_str += '时间段' + str(i+1) + ': ' + '\n'

            #1、时间段的开始时间
            start_time = get_int32u_le(context[index+21+28*i:index+25+28*i])
            charge_recode_dict['time_seq'][i]['start_timestamp'] = '0x%08X' % start_time
            #将时间戳生成 ‘年-月-日 时：分：秒’格式
            human_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time) )
            context_str += '\t开始时间: ' + human_time + '(%d)' %(start_time) + '\n'

            #2、时间段的结束时间
            end_time = get_int32u_le(context[index+25+28*i:index+29+28*i])
            charge_recode_dict['time_seq'][i]['end_timestamp'] = '0x%08X' % end_time
            #将时间戳生成 ‘年-月-日 时：分：秒’格式
            human_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time) )
            context_str += '\t结束时间: ' + human_time + '(%d)' %(end_time) + '\n'

            #3、时间段的充电电量
            power = get_int32u_le(context[index+29+28*i:index+33+28*i]) *  0.01
            charge_recode_dict['time_seq'][i]['power'] = '%s' %(power)
            context_str += '\t电量: ' + charge_recode_dict['time_seq'][i]['power'] + '(KWh)\n'

            #4、时间段的服务费单价
            price = get_int32u_le(context[index+33+28*i:index+37+28*i]) *  0.0001
            charge_recode_dict['time_seq'][i]['service_price'] = '%s' %(price)
            context_str += '\t服务费单价: ' + charge_recode_dict['time_seq'][i]['service_price'] + '(元)\n'

            #5、时间段的单价
            price = get_int32u_le(context[index+37+28*i:index+41+28*i]) *  0.0001
            charge_recode_dict['time_seq'][i]['price'] = '%s' %(price)
            context_str += '\t单价: ' + charge_recode_dict['time_seq'][i]['price'] + '(元)\n'

            #6、时间段的服务费金额
            price = get_int32u_le(context[index+41+28*i:index+45+28*i]) *  0.01
            charge_recode_dict['time_seq'][i]['service'] = '%s' %(price)
            context_str += '\t服务费金额: ' + charge_recode_dict['time_seq'][i]['service'] + '(元)\n'

            #7、时间段的充电金额，不含服务费
            #print(context[index+44+28*i:index+48+28*i])
            price = get_int32u_le(context[index+45+28*i:index+49+28*i]) *  0.01
            charge_recode_dict['time_seq'][i]['momey'] = '%s' %(price)
            context_str += '\t充电金额: ' + charge_recode_dict['time_seq'][i]['momey'] + '(元)\n'
        except IndexError:
            print("时间段个数错误(%s)" % time_seq)
            return None
    try:
        i = recode_time_seq_num - 1  #目前交易记录里预留了recode_time_seq_num个时间段
        #8、充电失败原因 index+21+28*4
        parse_err_reason(context[index+49+28*i], charge_recode_dict)
        context_str += '启动失败原因: ' + charge_recode_dict['start_fail'] + '\n'

        #9、具体停止原因
        parse_stop_reason(context[index+50+28*i], charge_recode_dict)
        context_str += '停止原因: ' + charge_recode_dict['stop_reason'] + '\n'

        #10、启动方式
        parse_start_mode(context[index+51+28*i], charge_recode_dict)
        context_str += '启动方式: ' + charge_recode_dict['start_method'] + '\n'

        #11、充电时长
        charge_recode_dict['charge_time'] = '%s' % get_int16u_le(context[index+52+28*i:index+54+28*i])
        context_str += '充电时长: ' + charge_recode_dict['charge_time'] + '(分钟)\n'
    except IndexError:
        print("时间段后至少需要5字节(%s)")
        return None

    context_str += '\n'
    return context_str

def search_recodes(dir_name=None):
    """ 搜索一个目录下的所有充电记录 """
    recode_list = [] #充电记录文件名列表
    try:
        for root, dirs, files in os.walk('.'):  #获取指定目录的所有目录路径、目录名、文件名
            for f in files: #对所有文件进行遍历
                if os.path.splitext(f)[1] == '.DAT':          #对该文件进行文件名跟后缀名分离，此函数返回一个元组(root, ext)
                    recode_list.append(os.path.join(root, f)) #生成完整的文件名加入到链表
        #print(recode_list)
    except:
        raise
    return recode_list

if __name__ == '__main__':
    import sys
    print(prompt)
    recode_list = search_recodes()  #搜索指定目录的.DAT文件
    #print(recode_list)
    f = open(new_file_name, 'w')

    for i in range(len(recode_list)):
        f.write(parse_one_recode(recode_list[i], i+1) )
    f.close()
    print("Parse %s recodes success,cat file recode_list" % len(recode_list))
    input('Enter any key to exit: ')
    sys.exit()

