"""
    对7KW交流充电桩log中的SM4解密，目前仅对发送的帧进行解密
    V1.0：
        1、修复原始数据丢失第24个字节的问题
	V1.1:
		1、修改对GPRS发送帧的正则表达式规则
"""

import re
import sm4

ver = 'V1.1'

#sm4密钥
key_data = [0x01,0x23,0x45,0x67,0x89,0xab,0xcd,0xef,0xfe,0xdc,0xba,0x98,0x76,0x54,0x32,0x10]
dec_file_name = "dec_log"                 #新文件名
log_name = "LOG"                          #原始日志文件名

def parse_log(file_name=log_name):
    """ 对LOG进行SM4解密 """
    try:
        with open(file_name) as f:
            context = f.readlines()       #读取日志文件的所有行，context是一个列表
    except:
        print("Please make sure exits %s file"% file_name)
        return

    new_file = open(dec_file_name, 'w')   #新文件，从头开始写
    sm4_d = sm4.Sm4()                     #构建一个Sm4对象
    sm4_d.sm4_setkey(key_data, sm4.SM4_DECRYPT)    #设置密钥跟加解码模式
    #对列表的每个表项进行正则表达式搜索
    regex = re.compile(r'.+Send ID\s*=\s*(0x\d{4}):\[([\dA-Fa-f]+)\].*', re.DOTALL)
    for i in range(len(context)):         #遍历所有行
        result = regex.search(context[i]) #搜索每一行
        if not result:
            new_file.write(context[i])    #把该行原样写入到新文件
        else: #符合正则表达式
            new_data = []
            out_data = ''
            sm4_input_data = result.group(2)
            for i in range(0, len(sm4_input_data), 2):
                new_data.append(int(sm4_input_data[i:i+2], 16))
            dec_data = sm4_d.sm4_crypt_ecb(new_data[24:-4])      #进行一次解密,只对加密部分解密，其他部分保持不变
            new_data = new_data[:24] + dec_data + new_data[-4:]  #构造该行完整的数据，是一个整型列表
            for j in range(len(new_data)):
                out_data += '%02X '% new_data[j]                 #对列表的所有项都转成字符串形成一个字符串行
            out_data = out_data.rstrip()                         #去掉字符串尾部的空格
            new_file.write(result.group().replace(result.group(2), out_data)) #对该行进行替换，并写入文件
    new_file.close()
    print("Parse file %s success"% file_name)


if __name__ == '__main__':
    """ parse_log.py [log_file]"""
    import sys
    print("Ver：" + ver)
    if len(sys.argv) > 1:
        parse_log(sys.argv[1])
    else:
        parse_log()
    input('Enter any key to exit')
    sys.exit()
