'''
Author: wulong@yushu.biz wulong@yushu.biz
Date: 2023-05-02 16:21:09
LastEditors: wulong@yushu.biz wulong@yushu.biz
LastEditTime: 2023-05-02 16:22:30
FilePath: \ttfRender\dot6_util.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from ctypes import c_int32,c_uint32,c_int64

Dot6 = 1<<6

INT32_MAX= 2147483647
INT32_MIN= -2147483648

def float_to_dot6(v):
    return int(v*Dot6)
def int_to_dot6(v):
    return  v<<6
