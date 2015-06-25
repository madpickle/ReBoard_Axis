import os,sys

def verifyDir(path):
    if os.path.exists(path) == False:
        os.makedirs(path)