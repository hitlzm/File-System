# -*- coding: utf-8 -*-
"""
# management.py
# (c) Zhiming & Rongpeng
"""

import hashlib
import math
import pickle
#import cloud    # cloud.py 文件
import time

'''
磁盘信息操作
'''
# 初始化磁盘磁道、扇区信息
def initDiskLst():
    hashDigit = 32 # 检验位为32位

    trackNum = 20  # 磁道数
    sectorNum = 10  # 每个磁道的扇区数
    sectorSize = 4096  # 扇区大小
    sectorDateSize = 4096 - hashDigit

    diskLst = []    # 磁盘磁道扇区参数表
    diskLst.append(trackNum)
    diskLst.append(sectorNum)
    diskLst.append(sectorSize)
    diskLst.append(sectorDateSize)
    return diskLst

# 获取磁盘信息表（磁盘扇区编号以及占用情况）
def getDiskTable(diskTablePath, diskLst):
    # 磁盘磁道扇区参数
    trackNum = diskLst[0]  # 磁道数
    sectorNum = diskLst[1]  # 每个磁道的扇区数
    # sectorSize = diskLst[2]  # 扇区大小

    fp = open(diskTablePath, "r")  # 默认磁盘第一个扇区存放磁盘信息表
    strlst = fp.read()
    fp.close()

    count = 0
    for count in range(len(strlst)):
        if strlst[count] == "$":
            break
    strlst = strlst[:count]
    strlst = strlst.split(";")

    diskTable = [[[] for i in range(sectorNum)] for j in range(trackNum)]
    k = 0
    for i in range(0, trackNum * sectorNum, sectorNum):
        for j in range(sectorNum):
            sectorState = strlst[i + j].split(",")
            diskTable[k][j].append(sectorState[0])
            diskTable[k][j].append(sectorState[1])
        k += 1
    return diskTable

# 更新磁盘信息表
def updateDiskTable(diskTablePath, diskTable, diskLst, sectorLst, sectorNeed):
    # 磁盘磁道扇区参数
    trackNum = diskLst[0]   # 磁道数
    sectorNum = diskLst[1]  # 每个磁道的扇区数

    print "sectorLst", sectorLst
    for i in range(sectorNeed):
        diskTable[int(sectorLst[i][:3])][int(sectorLst[i][3:])][1] = "F"   #相应扇区更新为已占用

    fp = open(diskTablePath, "w")
    for j in range(trackNum):
        for k in range(sectorNum):
            fp.write(diskTable[j][k][0] + "," + diskTable[j][k][1] + ";")
    fp.close()

# 获取扇区状态
def getSectorState(diskTable, diskLst, trackID, sectorID):
    # 磁盘磁道扇区参数
    trackNum = diskLst[0]  # 磁道数
    sectorNum = diskLst[1]  # 每个磁道的扇区数
    # sectorSize = diskLst[2]  # 扇区大小

    if (0 <= int(trackID) < trackNum) and (0 <= int(sectorID) < sectorNum):
        if diskTable[int(trackID)][int(sectorID)][1] == "F":
            return False
        return True
    return -1  # 编号超出磁盘范围


# 计算扇区数据部分hash
def sectorDataCheckout(data):
    dataMD5 = hashlib.md5(data).hexdigest()
    return dataMD5

#地址翻译
def pathTranslate(disk,track,sector):
    disk = "disk"
    return disk + "/" + track + "/" + sector + ".txt"

# 将空闲扇区表转换为路径
def sectorLstToSectorPath(sectorLst):
    sectorPathLst = []
    for sector in sectorLst:
        path = pathTranslate('',sector[:3],sector[3:])
        sectorPathLst.append(path)
    return sectorPathLst

'''
磁盘读写操作
'''
# 顺序查找空闲扇区
def findFreeSector(diskTable, diskLst, sectorNeed):
    trackNum = diskLst[0]   # 磁道数
    sectorNum = diskLst[1]  # 每个磁道的扇区数

    sectorLst = []  # 空闲扇区编码(6位):磁道+扇区
    count = 0
    for i in range(trackNum):
        for j in range(sectorNum):
            if count < sectorNeed:
                if diskTable[i][j][1] == "T":
                    sectorLst.append(diskTable[i][j][0])
                    count += 1
            else:
                return sectorLstToSectorPath(sectorLst)
    return False

# 磁盘扇区写接口
def sectorWrite(sectorPath, data):
    sectorData = data + sectorDataCheckout(data)
    fp = open(sectorPath, 'w')
    if fp:
        fp.write(sectorData)
        fp.close()
        return True
    return False

# 磁盘扇区读接口
def sectorRead(diskLst, sectorPath):
    hashDigit = diskLst[2] - diskLst[3]
    fp = open(sectorPath, 'r')
    sectorData = fp.read()
    fp.close()

    data = sectorData[:-hashDigit]
    dataMD5 = sectorData[-hashDigit:]
    result = sectorDataCheckout(data)
    if dataMD5 == result:
        return data
    return False

# 删除文件(只修改索引表)
def removeFile(sectorPath):
	diskTablePath = "disk/000/000.txt"
	diskLst = initDiskLst()
	diskTable = getDiskTable(diskTablePath, diskLst)
	sid = sectorPath[-11:-8] + sectorPath[-7:-4]
	sectorLst.append(sid)
	sectorNeed = 1
	updateDiskTable(diskTablePath, diskTable, diskLst, sectorLst, sectorNeed, True)


# 删除文件(完全删除数据)
def removeFileComplete(sectorPath):
	diskTablePath = "disk/000/000.txt"
	diskLst = initDiskLst()
	diskTable = getDiskTable(diskTablePath, diskLst)
	sid = sectorPath[-11:-8] + sectorPath[-7:-4]
	sectorLst.append(sid)
	sectorNeed = 1

	fp = open(sectorPath, 'w')
	for i in range(diskLst[2]):
		fp.write("$")
	fp.close()

	updateDiskTable(diskTablePath, diskTable, diskLst, sectorLst, sectorNeed, True)

	
'''
文件操作
'''
# 计算文件需要的扇区数
def getSectorNeed(fileData, sectorDataSize):
    dataLen = len(fileData) # 文件字节数
    need = int(math.ceil(float(dataLen) / sectorDataSize)) # 存储文件需要的扇区数
    sectorNeed = need * 2
    return sectorNeed

# 将文件根据扇区分成块
def dataSegmentation(sectorDataSize, fileData, sectorNeed):
    dataLst = ["" for i in range(sectorNeed)] # 文件块
    key = 0
    for i in fileData:
        if (len(dataLst[key]) + len(i)) <= sectorDataSize:
            dataLst[key] = dataLst[key] + i
        else:
            key += 1
    return dataLst

#建立索引层级关系
def build_level(current_level,level):
    if level:
        current_level.extend([[],[],[],[]])
        for x in current_level:
            build_level(x,level-1)

#建立树叶的索引，即文件实际内容的索引
def build_sector_index(current_pointer,sectorID,sectorID_2):
    if len(current_pointer) <4:#小于4时必为叶节点
        current_pointer.append((sectorID,sectorID_2))
        return True
    else:#项目数等于4时，若为中间节点则继续往下查找
        if type(current_pointer[0]) == list:
            for x in current_pointer:
                if build_sector_index(x,sectorID):
                    return True

#  写文件
def fileWrite(diskTable, diskLst, data, file_pointer):
    sectorNeed = (len(data)-1)/4064 + 1
    sector_path_Lst = findFreeSector(diskTable, diskLst, sectorNeed*2)#由于分散冗余储存，需要两倍扇区
    if sector_path_Lst:
        file_pointer['info']['size'] = len(data)#记录文件大小
        file_pointer['info']['time'] = time.strftime( '%Y-%m-%d %X', time.localtime() )#记录文件创建时间

        index_level = int(math.ceil(math.log(sectorNeed)/math.log(4)))#索引层数
        build_level(file_pointer['sector_index'],index_level)#建立索引层级关系
        #建立树叶的索引，指向扇区，并写数据
        data_seged = dataSegmentation(diskLst[-1], data, sectorNeed)
        for i in range(sectorNeed):
            sectorWrite(sector_path_Lst[i], data_seged[i])#写数据
            sectorWrite(sector_path_Lst[i+sectorNeed], data_seged[i])#写数据
            build_sector_index(file_pointer['sector_index'],sector_path_Lst[i],sector_path_Lst[i+sectorNeed])#建索引
    else:
        print('磁盘容量不足。')

#还原数据
def restore(diskLst, file_pointer):
    data = ''
    if file_pointer and type(file_pointer[0]) == list:#若top是索引节点
        for x in file_pointer:
            data = data + shensou(x)
    elif file_pointer and type(file_pointer[0]) == tuple:#top是叶节点
        for x in file_pointer:
            data = data + sectorRead(diskLst, x[0])
            if data == False:#若第一份出错则读第二份数据
                data = data + sectorRead(diskLst, x[1])
                if data == False:#若第二份数据出错则从云端备份恢复扇区
                    getBackupSector(x[0])
                    getBackupSector(x[1])
                    data = data + sectorRead(diskLst, x[0])
    else:
        pass
    return data

#储存文件目录
def save_list(root_list):
    list_ordered = pickle.dumps(root_list)
    return sectorWrite(pathTranslate('','000','001'),list_ordered)
        
# 文件读取
def fileRead(diskLst, file_pointer):
    data = restore(diskLst, file_pointer)
    if len(data) == file_pointer['info']['size']:
        return data
    else:
        return False

def main():
    diskTablePath = "disk/000/000.txt"
    diskLst = initDiskLst()
    diskTable = getDiskTable(diskTablePath, diskLst)


    #获取根文件目录
    list_ordered = sectorRead(diskLst, pathTranslate('','000','001'))
    if not list_ordered:
        print("磁盘发生错误，请重新运行。")
        exit()
    root_list = pickle.loads(list_ordered)

    current_list = root_list
    path_back = []
    path_name = 'Disk:'
    while (1):
        order = raw_input(path_name+'>')
        if order == 'dir' or order == 'ls':#列出文件/文件夹
            file_num = len(current_list['list'].keys())
            if file_num:
                print(' '+path_name+"下共"+str(file_num)+"个文件/文件夹...")
                for x in current_list['list']:
                    print '     '+x
            else:
                print("共0个文件/文件夹")
        elif order[0:3] == 'cd ' and order[3:] != '..':#进入文件夹
            for x in order[3:].split('\\'):
                if current_list['list'].has_key(x):
                    path_back.append(current_list)#将当前目录压栈，用于回退
                    path_name = path_name + '\\' + x#记录路径名用于打印
                    current_list = current_list['list'][x]#进入指定目录
                else:
                    print("系统找不到指定的路径。")
                    break
        elif order == 'cd..' or order == 'cd ..':#返回上一级
            if path_back:
                path_name = path_name[:path_name.rfind('\\')]#删除路径名
                current_list = path_back.pop()#返回上一级
        elif order == 'exit':#退出
            #储存文件目录
            if save_list(root_list):
                exit()
            else:
                print("磁盘发生错误，请再次操作。")
        elif order[0:3] == 'md ':#新建文件夹
            new_foldername = order[3:]
            if new_foldername:
                for x in new_foldername:#文件名是否合法
                    if x == '/' or x == '\\' or x == '*' or x == '?' or x == ':' or  x == '\"' or  x == '<' or  x == '>' or  x == '|':
                        print("文件名不能包含下列任何字符：\n\\/*?:<>|")
                        break
                if current_list['list'].has_key(new_foldername):#文件名重复  ！！！需要添加多层级的创建
                    print("子目录 "+new_foldername+" 已经存在。")
                else:
                    current_list['list'][new_foldername] = {'info':{},'list':{}}
                    #储存文件目录
                    if not save_list(root_list):
                        print("磁盘发生错误，请再次操作。")
            else:
                print("命令语法不正确。")
        elif order[0:3] == 'mf ':#新建文件
            new_filename = order[3:]
            if new_filename:
                for x in new_filename:#文件名是否合法
                    if x == '/' or x == '\\' or x == '*' or x == '?' or x == ':' or  x == '\"' or  x == '<' or  x == '>' or  x == '|':
                        print("文件名不能包含下列任何字符：\n\\/*?:<>|")
                        break
                if current_list['list'].has_key(new_filename):#文件名重复    ！！！需要添加多层级的创建
                    print("此位置已经包含同名文件。")
                else:
                    current_list['list'][new_filename] = {'info':{},'sector_index':[]}
                    #储存文件内容
                    data = raw_input('输入文件内容：>')
                    if data:#输入数据不为空时储存内容，创建索引，为空时'sector_index'的链表为空
                        file_pointer = current_list['list'][new_filename]
                        fileWrite(diskTable, diskLst, data, file_pointer)
                    #储存文件目录
                    if not save_list(root_list):
                        print("磁盘发生错误，请再次操作。")
        elif order[0:3] == 'vi ':#读文件
            filename = order[3:]
            if filename:
                if current_list['list'].has_key(filename):#找到文件    ！！！需要添加多层级的查找
                    file_pointer = current_list['list'][filename]
                    filecontent = fileRead(diskLst, file_pointer)
                else:
                    print("找不到 "+path_name+filename)
            else:
                print("命令语法不正确。")
        elif order[0:3] == 'mv ':#移动文件
            pass
        else:#无效命令
            print("\'"+order+"\'"+"不是内部或外部命令，也不是可运行的程序或批处理文件。")

main()
