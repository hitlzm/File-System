# -*- coding: utf-8 -*-
"""
# management.py
# (c) Zhiming & Rongpeng
"""

import hashlib
import math
import pickle
import cloud 	# cloud.py 文件


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


def pathTranslate(disk,track,sector):
	disk = "disk"
	return disk + "/" + track + "/" + sector + ".txt"


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
	return "False"


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
				return sectorLst
	return False


# 建立文件索引
def createFileIndex(fileName, fileData, sectorNeed, sectorLst, diskType):
	fileDataMD5 = hashlib.sha1(fileData).hexdigest()
	fileIndex = fileDataMD5 + "," + fileName
	for i in range(sectorNeed):
		fileIndex = fileIndex + "," + sectorLst[i]
	fileIndex = fileIndex + ";\n"
	path = diskType + "/000/001.txt"
	fp = open(path, "a")
	fp.writelines(fileIndex)
	fp.close()
	return True


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


# 文件写入
def fileWrite(diskTablePath, diskTable, diskLst, fileName, fileData, diskType):
    # 磁盘磁道扇区参数
    trackNum = diskLst[0]   # 磁道数
    sectorNum = diskLst[1]  # 每个磁道的扇区数
    sectorSize = diskLst[2] # 扇区大小
    sectorDataSize = diskLst[3] # 扇区数据区大小

    sectorNeed = getSectorNeed(fileData, sectorDataSize) # 需要扇区数目
    dataLst = dataSegmentation(sectorDataSize, fileData, sectorNeed) # 将文件根据扇区分成块
    sectorLst = findFreeSector(diskTable, diskLst, sectorNeed) # 顺序查找空闲扇区

    # 文件内容写入相应扇区
    for i in range(sectorNeed):
        sectorPath = diskType + "/" + sectorLst[i][:3] +"/" + sectorLst[i][-3:] + ".txt"
        key = i % (sectorNeed / 2)
        sectorWrite(sectorPath, dataLst[key])
        cloudBackupSector(sectorPath)	# 云端备份

    createFileIndex(fileName, fileData, sectorNeed, sectorLst, diskType) # 建立文件索引

    updateDiskTable(diskTablePath, diskTable, diskLst, sectorLst, sectorNeed) # 更新磁盘信息表(diskTable)


# 文件读取
def fileRead(fileIndexPath, diskLst, fileName, diskType):
	fileMessage = ""
	fp = open(fileIndexPath, "r")
	for line in fp.readlines():
		if line.find(fileName) == -1:
			continue
		else:
			fileMessage = fileMessage + line
			break;
	fp.close()
	fileMessage = fileMessage.split(",")

	sectorLst = []
	for i in range(2, len(fileMessage)):
		sectorLst.append(fileMessage[i][:6])

	fileData = ""
	sectorNum = len(fileMessage) - 2
	for i in range(sectorNum / 2):
		trackID = sectorLst[i][:3]
		sectorID = sectorLst[i][-3:]
		sectorPath = diskType + "/" + trackID + "/" + sectorID + ".txt"

		data = sectorRead(diskLst, sectorPath)
		if data == "False":
			trackID = sectorLst[i + sectorNum / 2][:3]
			sectorID = sectorLst[i + sectorNum / 2][-3:]
			sectorPath = diskType + "/" + trackID + "/" + sectorID + ".txt"
			data = sectorRead(diskLst, sectorPath)
			if data = "False":
				getBackupSector(sectorPath) #从云端备份恢复扇区
				data = sectorRead(diskLst, sectorPath)
				fileData = fileData + data	
			else:
				fileData = fileData + data
		else:
			fileData = fileData + data

	return fileData


# 获取文件索引表
def getFileIndex(fileIndexPath):
	fileIndex = []
	fp = open(fileIndexPath, "r")
	for line in fp.readlines():
		fileIndex.append(line)
	fp.close()

	return fileIndex


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
		if order == 'dir':#列出文件/文件夹
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
	        list_ordered = pickle.dumps(root_list)
	        if sectorWrite(pathTranslate('','000','001'),list_ordered):
	            exit()
	        else:
	            print("磁盘发生错误，请再次操作。")
	    elif order[0:3] == 'md ':#新建文件夹
	        new_foldername = order[3:]
	        if new_foldername:
	            for x in new_foldername:#文件名是否合法
	                if x == '/' or x == '\\' or x == '*' or x == '?' or x == ':' or  x == '\"' or  x == '<' or  x == '>':
	                    print("文件不能包含下列任何字符：\n\\/*?:<>")
	                    break
	                else:
	                    current_list['list'][new_foldername] = {}
	                    current_list['list'][new_foldername]['info'] = {}
	                    current_list['list'][new_foldername]['list'] = {}
	        else:
	            print("命令语法不正确。")
	    else:#无效命令
	        print("\'"+order+"\'"+"不是内部或外部命令，也不是可运行的程序或批处理文件。")

    '''
    diskName = ["disk", "backup"]
    
    fp = open("test.txt", "r")
    fileName = "test.txt"
    fileData = fp.read()
    fp.close()

    #文件存入
    fileWrite(diskTablePath, diskTable, diskLst, fileName, fileData, diskName[0])
    
    #文件备份
    #fileWrite(diskTablePath, diskTable, diskLst, fileName, fileData, diskName[1])
    
    
    fileIndexPath = "disk/000/001.txt"
    fileName = "test.txt"

    print getFileIndex(fileIndexPath)

    #print fileRead(fileIndexPath, diskLst, fileName, diskName[0])
    '''

    return 0
