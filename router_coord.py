import os
import numpy as np

mapping = dict()
mapping["C1"] = (-1, 1)
mapping["C2"] = (0, 1)
mapping["C3"] = (1, 1)
mapping["C4"] = (-1, 0)
mapping["C5"] = (0, 0)
mapping["C6"] = (1, 0)
mapping["C7"] = (-1, -1)
mapping["C8"] = (0, -1)
mapping["C9"] = (1, -1)

def getCoor():
    router1 = []
    router2 = []
    router3 = []
    for i in range(3):
        cmd = "sudo iwlist wlan0 scan"
        strDbm = os.popen(cmd).read()
        r1r1 = strDbm[strDbm.find('ESSID:"ROUTER1"')-100:strDbm.find('ESSID:"ROUTER1"')+100]
        r2r2 = strDbm[strDbm.find('ESSID:"ROUTER2"')-100:strDbm.find('ESSID:"ROUTER2"')+100]
        r3r3 = strDbm[strDbm.find('ESSID:"ROUTER3"')-100:strDbm.find('ESSID:"ROUTER3"')+100]
        q1 = r1r1[3:16]
        #print 'Router1 Quality: ' + q1
        ss1 = r1r1[18:38]
        #print 'Router1 Signal Strength: ' + ss1 + '\n'
        router1.append(int(ss1[14:16], 10))
        q2 = r2r2[3:16]
        #print 'Router2 Quality: ' + q2
        ss2 = r2r2[18:38]
        #print 'Router2 Signal Strength: ' + ss2 + '\n'
        router2.append(int(ss2[14:16], 10))
        q3 = r3r3[3:16]
        #print 'Router3 Quality: ' + q3
        ss3 = r3r3[18:38]
        #print 'Router3 Signal Strength: ' + ss3 + '\n'
        router3.append(int(ss3[14:16], 10))
    router1 = removeOutliers(router1)
    router2 = removeOutliers(router2)
    router3 = removeOutliers(router3)
    #print 'Router 1 Mean: ', np.mean(router1)
    #print 'Router 1 Std: ', np.std(router1)
    #print 'Router 2 Mean: ', np.mean(router2)
    #print 'Router 2 Std: ', np.std(router2)
    #print 'Router 3 Mean: ', np.mean(router3)
    #print 'Router 3 Std: ', np.std(router3)
    r1 = np.mean(router1)
    r2 = np.mean(router2)
    r3 = np.mean(router3)
    curr_grid = ""
    # check the value and map it to a grid
    if ((r1 <= 28) and (r1 >= 27) and (r2 <= 32) and (r2 >= 31) and (r3 >= 28) and (r3 <= 30)):
        # C1
        curr_grid = "C1"
    elif ((r1 <= 31) and (r1 >= 30) and (r2 <= 44) and (r2 >= 40) and (r3 >= 16) and (r3 <= 17)):
        # C2
        curr_grid = "C2"
    elif ((r1 <= 34) and (r1 >= 33) and (r2 <= 44) and (r2 >= 41) and (r3 >= 28) and (r3 <= 30)):
        # C3
        curr_grid = "C3"
    elif ((r1 <= 32) and (r1 >= 30) and (r2 <= 35) and (r2 >= 33) and (r3 >= 45) and (r3 <= 46)):
        # C4
        curr_grid = "C4"
    elif ((r1 <= 50) and (r1 >= 47) and (r2 <= 37) and (r2 >= 35) and (r3 >= 28) and (r3 <= 29)):
        # C5
        curr_grid = "C5"
    elif ((r1 <= 38) and (r1 >= 36) and (r2 <= 38) and (r2 >= 36) and (r3 >= 41) and (r3 <= 45)):
        # C6
        curr_grid = "C6"
    elif ((r1 <= 37) and (r1 >= 36) and (r2 <= 42) and (r2 >= 40) and (r3 >= 36) and (r3 <= 38)):
        # C7
        curr_grid = "C7"
    elif ((r1 <= 28) and (r1 >= 27) and (r2 <= 32) and (r2 >= 31) and (r3 >= 28) and (r3 <= 30)):
        # C8
        curr_grid = "C8"
    elif ((r1 <= 28) and (r1 >= 27) and (r2 <= 32) and (r2 >= 31) and (r3 >= 36) and (r3 <= 38)):
        # C9
        curr_grid = "C8"
    else:
        # unknown value
        curr_grid = "XX"
    return curr_grid

def getCoor(r1, r2, r3):
    router1 = []
    router2 = []
    router3 = []
    for i in range(3):
        cmd = "sudo iwlist wlan0 scan"
        strDbm = os.popen(cmd).read()
        r1 = strDbm[strDbm.find('ESSID:"ROUTER1"')-100:strDbm.find('ESSID:"ROUTER1"')+100]
        r2 = strDbm[strDbm.find('ESSID:"ROUTER2"')-100:strDbm.find('ESSID:"ROUTER2"')+100]
        r3 = strDbm[strDbm.find('ESSID:"ROUTER3"')-100:strDbm.find('ESSID:"ROUTER3"')+100]

        q1 = r1[3:16]
        #print 'Router1 Quality: ' + q1
        ss1 = r1[18:38]
        #print 'Router1 Signal Strength: ' + ss1 + '\n'
        router1.append(int(ss1[14:16], 10))
        q2 = r2[3:16]
        #print 'Router2 Quality: ' + q2
        ss2 = r2[18:38]
        #print 'Router2 Signal Strength: ' + ss2 + '\n'
        router2.append(int(ss2[14:16], 10)) 
        q3 = r3[3:16]
        #print 'Router3 Quality: ' + q3
        ss3 = r3[18:38]
        #print 'Router3 Signal Strength: ' + ss3 + '\n'
        router3.append(int(ss3[14:16], 10))
    router1 = removeOutliers(router1)
    router2 = removeOutliers(router2)
    router3 = removeOutliers(router3)
    #print 'Router 1 Mean: ', np.mean(router1)
    #print 'Router 1 Std: ', np.std(router1)
    #print 'Router 2 Mean: ', np.mean(router2)
    #print 'Router 2 Std: ', np.std(router2)
    #print 'Router 3 Mean: ', np.mean(router3)
    #print 'Router 3 Std: ', np.std(router3)
    r1 = np.mean(router1)
    r2 = np.mean(router2)
    r3 = np.mean(router3)
    curr_grid = ""
    # check the value and map it to a grid
    if ((r1 <= 28) and (r1 >= 27) and (r2 <= 32) and (r2 >= 31) and (r3 >= 28) and (r3 <= 30)):
        # C1
        curr_grid = "C1"
    elif ((r1 <= 31) and (r1 >= 30) and (r2 <= 44) and (r2 >= 40) and (r3 >= 16) and (r3 <= 17)):
        # C2
        curr_grid = "C2"
    elif ((r1 <= 34) and (r1 >= 33) and (r2 <= 44) and (r2 >= 41) and (r3 >= 28) and (r3 <= 30)):
        # C3
        curr_grid = "C3"
    elif ((r1 <= 32) and (r1 >= 30) and (r2 <= 35) and (r2 >= 33) and (r3 >= 45) and (r3 <= 46)):
        # C4
        curr_grid = "C4"
    elif ((r1 <= 50) and (r1 >= 47) and (r2 <= 37) and (r2 >= 35) and (r3 >= 28) and (r3 <= 29)):
        # C5
        curr_grid = "C5"
    elif ((r1 <= 38) and (r1 >= 36) and (r2 <= 38) and (r2 >= 36) and (r3 >= 41) and (r3 <= 45)):
        # C6
        curr_grid = "C6"
    elif ((r1 <= 37) and (r1 >= 36) and (r2 <= 42) and (r2 >= 40) and (r3 >= 36) and (r3 <= 38)):
        # C7
        curr_grid = "C7"
    elif ((r1 <= 28) and (r1 >= 27) and (r2 <= 32) and (r2 >= 31) and (r3 >= 28) and (r3 <= 30)):
        # C8
        curr_grid = "C8"
    elif ((r1 <= 28) and (r1 >= 27) and (r2 <= 32) and (r2 >= 31) and (r3 >= 36) and (r3 <= 38)):
        # C9
        curr_grid = "C8"
    else:
        # unknown value
        curr_grid = "XX"
    return curr_grid

def removeOutliers(x, outlierConstant=1.5):
    a = np.array(x)
    upper_quartile = np.percentile(a, 75)
    lower_quartile = np.percentile(a, 25)
    IQR = (upper_quartile - lower_quartile) * outlierConstant
    quartileSet = (lower_quartile - IQR, upper_quartile + IQR)
    result = a[np.where((a >= quartileSet[0]) & (a <= quartileSet[1]))]
    return result.tolist()
