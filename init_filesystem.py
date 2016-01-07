# -*- coding: utf-8 -*-
from management import sectorWrite
import pickle
root_list = {}
root_list['list'] = {}
root_list['info'] = {}
list_ordered = pickle.dumps(root_list)
sectorWrite("disk/000/001.txt",list_ordered)
#sectorWrite("backup/000/001.txt",list_ordered)
