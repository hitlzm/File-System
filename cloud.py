# -*- coding: utf-8 -*-
import qiniu
from qiniu import *

access_key = 'Pv-3kPDRyhF8pzA2feqwv5WjofKxxZW9i-DtDmr4'
secret_key = 'l1Ne7qbhSV60hKUryEnf69kjHuEfRNRcgAxHGm-G'
bucket_name = 'disk'
bucket_domain = '7xpw8s.com1.z0.glb.clouddn.com'

quest = Auth(access_key, secret_key)
bucket = BucketManager(quest)


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


def upload(path, fileName):
	token = quest.upload_token(bucket_name, fileName)
	params = {'x:a': 'a'}
	progress_handler = lambda progress, total: progress
	ret, info = qiniu.put_file(token, fileName, path, params, \
								"txt", progress_handler = progress_handler)
	print "path:", path, " fileName:", fileName


def cloudBackup(diskType):
	diskLst = initDiskLst()
	for i in range(diskLst[0]):
		trackID = "00" + str(i)
		for j in range(diskLst[1]):
			sectorID = "00" + str(j)
			path = diskType + "/" + trackID[-3:] + "/" + sectorID[-3:] + ".txt"
			fileName = trackID[-3:] + sectorID[-3:] + ".txt"
			upload(path, fileName)
	return 0


cloudBackup("disk")
