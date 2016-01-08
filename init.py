# -*- coding: utf-8 -*-

import os

# 设置磁盘磁道、扇区信息
def initDiskLst():
	hashDigit = 32

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


# 模拟磁盘的初始化
def initDisk(diskLst, diskType):
	# 磁盘磁道扇区参数
	trackNum = diskLst[0]  # 磁道数
	sectorNum = diskLst[1]  # 每个磁道的扇区数
	sectorSize = diskLst[2]  # 扇区大小

	# 磁盘初始化
	sectorPos = [[] for i in range(trackNum)]   # 扇区位置
	for i in range(trackNum):
		trackID = "00" + str(i)
		trackPath = diskType + "/" + trackID[-3:]
		os.makedirs(trackPath)
		for j in range(sectorNum):
			sectorID = "00" + str(j)
			sectorPath = trackPath + "/" + sectorID[-3:] + ".txt"
			sectorPos[i].append(trackID[-3:] + sectorID[-3:])    # 存储每个扇区的唯一编号:磁道号(3位)+扇区号(3位)
			fp = open(sectorPath, "w")
			if (i == 0) and (j == 1):
				continue
			else:
				for k in range(sectorSize):
					fp.write("$")
				fp.close()

	# 构建磁盘映射表
	diskTable = ""
	for i in range(trackNum):
		for j in range(sectorNum):
			state = "T" #扇区为空
			if i == 0 and (j == 0 or j == 1):
				state = "F" #扇区不空
			diskTable = diskTable + sectorPos[i][j] + "," + state + ";"
	path = diskType + "/000/000.txt"
	fp = open(path, "w")
	tableLen = len(diskTable)
	for i in range(sectorSize):
		if i < tableLen:
			fp.write(diskTable[i])
		else:
			fp.write("$")
	fp.close()


def main():
	diskLst = initDiskLst()

	diskName = ["disk", "backup"]
	initDisk(diskLst, diskName[0])
	#initDisk(diskLst, diskName[1])
	return 0;

main()