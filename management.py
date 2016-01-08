# -*- coding: utf-8 -*-
"""
# management.py
# (c) Zhiming & Rongpeng
"""

import hashlib
import math
import pickle
import cloud    # cloud.py 文件
import time

'''
磁盘信息操作
'''
# 初始化并返回磁盘磁道、扇区信息
def initDiskLst():
    hashDigit = 32 # 检验位为32位

    trackNum = 20  # 磁道数
    sectorNum = 10  # 每个磁道的扇区数
    sectorSize = 4096  # 扇区大小
    sectorDataSize = 4096 - hashDigit #数据区大小

    diskLst = []    # 磁盘磁道扇区参数表
    diskLst.append(trackNum)
    diskLst.append(sectorNum)
    diskLst.append(sectorSize)
    diskLst.append(sectorDataSize)
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
def updateDiskTable(diskTablePath, diskTable, diskLst, sectorLst, sectorNeed, key):
    # 磁盘磁道扇区参数
    trackNum = diskLst[0]   # 磁道数
    sectorNum = diskLst[1]  # 每个磁道的扇区数

    for i in range(sectorNeed):
        if key == False:
            diskTable[int(sectorLst[i][:3])][int(sectorLst[i][3:])][1] = "F"   #相应扇区更新为已占用
        else:
            diskTable[int(sectorLst[i][:3])][int(sectorLst[i][3:])][1] = "T"   #相应扇区更新为已释放

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


'''
磁盘读写操作
'''
# 计算扇区数据部分hash
def sectorDataCheckout(data):
    dataMD5 = hashlib.md5(data).hexdigest()
    return dataMD5


# 地址翻译
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


# 顺序查找空闲扇区
def findFreeSector(sectorNeed):
    diskTablePath = "disk/000/000.txt"
    diskLst = initDiskLst()
    diskTable = getDiskTable(diskTablePath, diskLst)

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
def sectorRead(sectorPath):
    diskLst = initDiskLst()

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


# 删除扇区文件(只修改磁盘扇区占用表)
def removeSector(sectorPath):
    diskTablePath = "disk/000/000.txt"
    diskLst = initDiskLst()
    diskTable = getDiskTable(diskTablePath, diskLst)
    sid = sectorPath[-11:-8] + sectorPath[-7:-4]
    sectorLst = []
    sectorLst.append(sid)
    sectorNeed = 1
    updateDiskTable(diskTablePath, diskTable, diskLst, sectorLst, sectorNeed, True)


# 删除文件(完全删除数据)
def removeSectorComplete(sectorPath):
    diskTablePath = "disk/000/000.txt"
    diskLst = initDiskLst()
    diskTable = getDiskTable(diskTablePath, diskLst)
    sid = sectorPath[-11:-8] + sectorPath[-7:-4]
    sectorLst = []
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
# 将文件根据扇区分成块
def dataSegmentation(fileData, sectorNeed):
    dataLst = initDiskLst()
    sectorDataSize = dataLst[-1]
    dataLst = ["" for i in range(sectorNeed)] # 文件块
    key = 0
    for i in fileData:
        if (len(dataLst[key]) + len(i)) <= sectorDataSize:
            dataLst[key] = dataLst[key] + i
        else:
            key += 1
    return dataLst


# 建立索引层级关系
def build_level(current_level,level):
    if level:
        current_level.extend([[],[],[],[]])
        for x in current_level:
            build_level(x,level-1)


# 建立树叶的索引，即文件实际内容的索引
def build_sector_index(current_pointer,sectorID,sectorID_2):
    if len(current_pointer) <4:#小于4时必为叶节点
        current_pointer.append((sectorID,sectorID_2))
        return True
    else:#项目数等于4时，若为中间节点则继续往下查找
        if type(current_pointer[0]) == list:
            for x in current_pointer:
                if build_sector_index(x,sectorID):
                    return True


# 还原数据索引成一维链表
def get_index_list(file_pointer):
    list = []
    if len(file_pointer)!=0 and type(file_pointer[0]) == list:#若top是索引节点
        for x in file_pointer:
            list.extend(get_index_list(x))
    elif len(file_pointer)!=0 and type(file_pointer[0]) == tuple:#top是叶节点
        list.extend(file_pointer)
    else:
        pass
    return list


#  写文件
def fileWrite(data, file_pointer):
    diskLst = initDiskLst()
    dataSectorSize = diskLst[-1]
    sectorNeed = (len(data)-1)/dataSectorSize + 1
    
    sector_path_Lst = findFreeSector(sectorNeed*2)#由于分散冗余储存，需要两倍扇区
    if sector_path_Lst:
        file_pointer['info']['size'] = str(len(data))#记录文件大小
        file_pointer['info']['time'] = time.strftime( '%Y-%m-%d %X', time.localtime() )#记录文件创建时间

        index_level = int(math.ceil(math.log(sectorNeed)/math.log(4)))#索引层数
        build_level(file_pointer['sector_index'],index_level)#建立索引层级关系
        #建立树叶的索引，指向扇区，并写数据
        data_seged = dataSegmentation(data, sectorNeed)
        for i in range(sectorNeed):
            sectorWrite(sector_path_Lst[i], data_seged[i])#写数据
            sectorWrite(sector_path_Lst[i+sectorNeed], data_seged[i])#写数据
            build_sector_index(file_pointer['sector_index'],sector_path_Lst[i],sector_path_Lst[i+sectorNeed])#建索引
    else:
        print('磁盘容量不足。')


# 读文件
def fileRead(file_pointer):
    list = get_index_list(file_pointer['sector_index'])
    data = ''
    for x in list:
        temp = sectorRead(x[0])
        if temp == False:#若第一份出错则读第二份数据
            temp = sectorRead(x[1])
            if temp == False:#若第二份数据出错则从云端备份恢复扇区
                getBackupSector(x[0])
                getBackupSector(x[1])
                temp = sectorRead(x[0])
            else:#第二份数据没错则用第二份数据恢复第一份数据
                sectorWrite(x[0], temp)
        data = data + str(temp)
    if  str(len(data)) == file_pointer['info']['size']:
        return data
    else:
        return False


# 储存文件系统到磁盘
def save_list(root_list):
    list_ordered = pickle.dumps(root_list)
    if not sectorWrite(pathTranslate('','000','001'),list_ordered):
        print("磁盘发生错误，请再次操作。")
        return False
    else:
        return True

        
# 磁盘碎片整理
def dfrg(current_list):
    if current_list.has_key('sector_index'):#若x是文件
        old_list = get_index_list(current_list['sector_index'])
        #需要存冗余备份,所以共两份
        new_list1 = findFreeSector(len(old_list))
        new_list2 = findFreeSector(len(old_list))
        for i in range(len(old_list)):
            sectorWrite(new_list1[i],sectorRead(old_list[i][0]))
            removeSector(old_list[i][0])
            sectorWrite(new_list2[i],sectorRead(old_list[i][1]))
            removeSector(old_list[i][1])
            old_list[i] = (new_list1[i],new_list2[i])

    else:#若x是目录
        for x in current_list['list']:
            dfrg(current_list['list'][x])


# 删除文件，注:在索引中删除未删除，调用时需要在目录中pop掉这个文件,parameterw只是是否完全删除
def removeFile(pointer, parameter):
    sector_list = get_index_list(pointer['sector_index'])
    if parameter:#parameter=1,标记删除
        for x in sector_list:
            removeSector(x[0])
            removeSector(x[1])
    else:#parameter=1,彻底删除
        for x in sector_list:
            removeSectorComplete(x[0])
            removeSectorComplete(x[1])


# 删除文件夹
def removeFolder(pointer, parameter):#pointer是['list']的内容
    keys = pointer.keys()
    for x in keys:
        current = pointer[x]
        if current.has_key('sector_index'):#是文件的话
            removeFile(current,parameter)
        else:#是文件夹的话
            removeFolder(current['list'], parameter)
        pointer.pop(x)

        
# 文件名是否合法
def name_is_legal(name):
    for x in name:
        if x == '/' or x == '\\' or x == '*' or x == '?' or x == ':' or  x == '\"' or  x == '<' or  x == '>' or  x == '|':
            return False
    return True
      
      
def main():
    diskTablePath = "disk/000/000.txt"
    diskLst = initDiskLst()
    diskTable = getDiskTable(diskTablePath, diskLst)

    #获取根文件目录
    list_ordered = sectorRead(pathTranslate('','000','001'))
    if not list_ordered:#文件系统目录读取失败
        print("文件系统发生错误，请初始化文件系统。")
        exit()
    root_list = pickle.loads(list_ordered)
    if not root_list:
        print("文件系统发生错误，请初始化文件系统。")
        exit()
    
    current_list = root_list
    path_back = []
    path_name = 'Disk:'
    while (1):
        order = raw_input(path_name+'>')
        if order == 'dir' or order == 'ls':#列出文件/文件夹
            file_num = len(current_list['list'].keys())
            if file_num:
                print(' '+path_name+"下共"+str(file_num)+"个文件/文件夹...")
                for x in current_list['list']:#打印目录下文件夹
                    if current_list['list'][x].has_key('sector_index'):
                        print '   '+current_list['list'][x]['info']['time'] + '     '+x+'   '+current_list['list'][x]['info']['size']+' Byte(s)'
                    else:
                        print '   '+current_list['list'][x]['info']['time'] + '     '+x
            else:
                print(' '+path_name+"下共0个文件/文件夹。")
        elif order[0:3] == 'cd ' and order[3:] != '..':#进入文件夹
            for x in order[3:].split('\\'):
                if current_list['list'].has_key(x) and current_list['list'][x].has_key('list'):
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
            if save_list(root_list):
                exit()
        elif order[0:3] == 'md ':#新建文件夹
            new_foldername = order[3:]
            if new_foldername:
                if not name_is_legal(new_foldername):
                    print("文件名不能包含下列任何字符:\n\\/*?:<>|")
                    continue
                if current_list['list'].has_key(new_foldername):#文件名重复  ！！！需要添加多层级的创建
                    print("子目录 "+new_foldername+" 已经存在。")
                else:
                    current_list['list'][new_foldername] = {'info':{'time':time.strftime('%Y-%m-%d %X', time.localtime())},'list':{}}#记录文件夹创建时间
                    save_list(root_list)
            else:
                print("命令语法不正确。")
        elif order[0:3] == 'mf ':#新建文件
            new_filename = order[3:]
            if new_filename:
                for x in new_filename:#文件名是否合法
                    if not name_is_legal(new_filename):
                        print("文件名不能包含下列任何字符:\n\\/*?:<>|")
                        continue
                if current_list['list'].has_key(new_filename):#文件名重复    ！！！需要添加多层级的创建
                    print("此位置已经包含同名文件或文件夹。")
                else:
                    current_list['list'][new_filename] = {'info':{},'sector_index':[]}
                    #储存文件内容
                    data = raw_input('输入文件内容:>')
                    if data:#输入数据不为空时储存内容，创建索引，为空时'sector_index'的链表为空
                        file_pointer = current_list['list'][new_filename]
                        fileWrite(data, file_pointer)
                    save_list(root_list)
        elif order[0:3] == 'vi ':#读文件
            filename = order[3:]
            if filename:
                if current_list['list'].has_key(filename) and current_list['list'][filename].has_key('sector_index'):#找到文件    ！！！需要添加多层级的查找
                    file_pointer = current_list['list'][filename]
                    filecontent = fileRead(file_pointer)
                    print filecontent,'\n'
                else:
                    print("找不到 "+path_name+filename)
            else:
                print("命令语法不正确。")
        elif order[0:3] == 'rm ':#删除文件/文件夹
            parameter = -1
            if order[3:6] == '-c ':#彻底删除
                name = order[6:]
                parameter = 0
            else:#标记删除
                name = order[3:]
                parameter = 1
            if name:
                if current_list['list'].has_key(name):#存在该文件/文件夹时对其进行删除
                    pointer = current_list['list'][name]
                    if pointer.has_key('sector_index'):#是文件的话
                        removeFile(pointer, parameter)
                    else:#是文件夹时，进入子目录删除所有文件
                        removeFolder(pointer['list'], parameter)
                    current_list['list'].pop(name)
                    save_list(root_list)
                else:
                    print("找不到 "+path_name+'\\'+name)
            else:
                print("命令语法不正确。")
        elif order == 'dfrg':#磁盘碎片整理
            while (1):
                confirm = raw_input("是否在当前目录下进行碎片整理：yes/no\n")
                if confirm == 'yes' or confirm == 'y' or  confirm == 'Y':
                    dfrg(current_list)
                    print("磁盘碎片整理程序运行完毕。")
                    break
                elif confirm == 'no' or confirm == 'n' or  confirm == 'N':
                    print("退出磁盘碎片整理程序。")
                    break
                else:
                    pass
        else:#无效命令
            print("\'"+order+"\'"+"不是内部或外部命令，也不是可运行的程序或批处理文件。")

main()
