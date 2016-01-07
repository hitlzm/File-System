# -*- coding: utf-8 -*-
"""
Created on Thu Dec 10 20:12:41 2015
@author: Zhiming
"""
import hashlib
import math

# 初始化磁盘磁道、扇区信息
def initDiskLst():
    trackNum = 20  # 磁道数
    sectorNum = 10  # 每个磁道的扇区数
    sectorSize = 4096  # 扇区大小

    diskLst = []    # 磁盘磁道扇区参数表
    diskLst.append(trackNum)
    diskLst.append(sectorNum)
    diskLst.append(sectorSize)
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


# 磁盘扇区写接口
def sectorWrite(sectorPath, data):
    fp = open(sectorPath, 'w'):
    if fp:
        fp.write(data)
        fp.close()
        return True
    return False


# 磁盘扇区读接口
def sectorRead(sectorPath):
    fp = open(sectorPath, 'r')
    if fp:
        data = fp.read()
        return data
    return False    


# 计算文件需要的扇区数
def getSectorNeed():
    dataLen = len(fileData) # 文件字节数
    sectorNeed = int(math.ceil(float(dataLen) / sectorSize)) # 存储文件需要的扇区数
    return sectorNeed


# 将文件根据扇区分成块
def dataSegmentation(sectorSize, fileData, sectorNeed):
    dataLst = ["" for i in range(sectorNeed)] # 文件块
    key = 0
    for i in fileData:
        if (len(dataLst[key]) + len(i)) <= sectorSize:
            dataLst[key] = dataLst[key] + i
        else:
            key += 1
    return dataLst


# 顺序查找空闲扇区
def findFreeSector(diskLst, sectorNeed):
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
    fileDataSHA1 = hashlib.sha1(fileData).hexdigest() 
    fileIndex = fileDataSHA1 + "," + fileName
    for i in range(sectorNeed):
        fileIndex = fileIndex + "," + sectorLst[i]
    fileIndex = fileIndex + ";\n"
    path = diskType + "/000/001.txt"
    fp = open(diskType, "a")
    fp.writelines(fileIndex)
    fp.close()
    return True


# 更新磁盘信息表
def updateDiskTable(diskTablePath, diskLst, sectorLst, sectorNeed):
    # 磁盘磁道扇区参数
    trackNum = diskLst[0]   # 磁道数
    sectorNum = diskLst[1]  # 每个磁道的扇区数

    for i in range(sectorNeed):
        diskTable[int(sectorLst[i][:2])][int(sectorLst[i][-3:])][1] = "F"   #相应扇区更新为已占用
    
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

    sectorNeed = getSectorNeed() # 需要扇区数目
    dataLst = dataSegmentation(sectorSize, fileData, sectorNeed) # 将文件根据扇区分成块
    sectorLst = findFreeSector(diskLst, sectorNeed) # 顺序查找空闲扇区

    # 文件内容写入相应扇区
    for i in range(sectorNeed):
        sectorPath = diskType + "/" + sectorLst[i][:3] +"/" + sectorLst[i][-3:] + ".txt"
        sectorWrite(sectorPath, dataLst[i])

    createFileIndex(fileName, fileData, sectorNeed, sectorLst, diskType) # 建立文件索引
    updateDiskTable(diskTablePath, diskLst, sectorLst, sectorNeed) # 更新磁盘信息表(diskTable)


# 文件读取
def fileRead(fileIndexPath, fileName, diskType):
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
    for i in range(len(fileMessage) - 2):
        trackID = sectorLst[i][:3]
        sectorID = sectorLst[i][-3:]
        sectorPath = diskType + "/" + trackID + "/" + sectorID + ".txt"

        data = sectorRead(sectorPath)
        if data != False:
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
	diskName = ["disk", "backup"]

    diskTablePath = "disk/000/000.txt"
    diskLst = initDiskLst()
    diskTable = getDiskTable(diskTablePath, diskLst)
    #getSectorState(diskTable, diskLst, 0, 0)

    
    fp = open("test.txt", "r")
    fileName = "test.txt"
    fileData = fp.read()
    fp.close()

    #文件存入
    fileWrite(diskTablePath, diskTable, diskLst, fileName, fileData, diskName[0])
    
    #文件备份
    fileWrite(diskTablePath, diskTable, diskLst, fileName, fileData, diskName[1])
    
    fileIndexPath = "disk/000/001.txt"
    fileName = "test.txt"

    print getFileIndex(fileIndexPath)

    print fileRead(fileIndexPath, fileName)

    return 0

main()