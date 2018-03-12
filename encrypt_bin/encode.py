#ord(chr) 字符转整型
#chr(int) 整性转字符
#str.encode(s)    str to bytes  
#bytes.decode(b)  bytes to str  

#$m%PINNET*+*@MCBV20#.CCUXX.U29211.1711.00.04
#$m%PINNET*+*@MCBV20#.CCUXX.U29211.1711.00.04171100042017-11-23 11:07:18

import time, sys
prompt "V1.0"
FILENAME = 'app_once'

def convert_file(file_name=FILENAME):
    """对一个文件进行添加76个字节的头文件"""
    try:
        with open(file_name, 'rb') as f:
            context = f.read()
    except FileNotFoundError:
        print('only support app_once')
        return

    pinnet = []
    for i in range(len(context)):
        #查找$m%
        if chr(context[i]) == '$' and chr(context[i + 1]) == 'm' and chr(context[i + 2]) == '%':
            #判断后面是否是'PINNET*+*@'
            for j in range(3, 13):   
                pinnet.append(chr(context[i + j]) )                      #把整数转成字符添加到列表
            
            if ''.join(pinnet) == 'PINNET*+*@':                          #把列表连接成字符串
                #获取必要的信息
                orgin_str = bytes.decode(context[i:i+44])                #bin文件里的原始字符，共44个,并转成字符串
                new_file_name = orgin_str[-10:].replace('.','')          #通过版本号转成文件名，不含后缀名
                cur_time = time.strftime('%Y-%m-%d %H:%M:%S')            #获取年月日时分秒
                head_str = orgin_str + new_file_name + cur_time          #构造文件头
                reverse = b'\x00\x00\x00'                                #三个字节预留
                crc16 = b'\x00\x00'                                      #两个字节crc16预留
                #写入新文件
                new_file = open(new_file_name + '.CCU', 'wb')
                new_file.write(str.encode(head_str) + reverse + crc16 + context)
                new_file.close()
                print('Conver file %s success,new file name %s'%(file_name + '.CCU', new_file_name) )
                break
    else:
        print("It is not a right file")

if __name__ == "__main__":
    import sys
    print(prompt)
    convert_file(FILENAME)
    input("Enter any key exit....")
    sys.exit()
