# -*- coding: utf-8 -*-
import pickle
import hashlib

# 计算扇区数据部分hash
def sectorDataCheckout(data):
    dataMD5 = hashlib.md5(data).hexdigest()
    return dataMD5

# 磁盘扇区写接口
def sectorWrite(sectorPath, data):
    sectorData = data + sectorDataCheckout(data)
    fp = open(sectorPath, 'w')
    if fp:
        fp.write(sectorData)
        fp.close()
        return True
    return False

root_list = {}
root_list['list'] = {}
root_list['info'] = {}
list_ordered = pickle.dumps(root_list)
sectorWrite("disk/000/001.txt",list_ordered)
#sectorWrite("backup/000/001.txt",list_ordered)
