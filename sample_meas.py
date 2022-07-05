import docker
import json
import sqlite3
import multiprocessing as mp
import datetime
import os
import time 
#import io
#import indexes
import re

# First deploy the network and run the command
# "docker exec -it rfsim5g-oai-ext-dn iperf -s -u -i 1"

# before choosing this contianer id make sure the iperf is installed on the conatiner using the below command
# "apt update; apt install -y procps iptables iproute2 iperf iputils-ping"

id = '262400d584b1e900b8e361cd82061fd21d19a2642dab80b22a72582f700b0af3' # container ID of UE1 (changes for every deployment)

#str2 = 'iperf -u -i 1 -fk -B 12.1.1.2 -b 125M -c 192.168.72.135 -t 2' # Actually Iperf Command with this we will get full iperf result

#to extract bandwidth part
t = 5
str2 = 'iperf -i 1 -fk -B 12.1.1.2 -b 125M -c 192.168.72.135 -r -t' + str(t)+ '| awk -Wi -F\'[ -]+\' \'/sec/{print $3"-"$4" "$8}\''
client=docker.from_env()
container = client.containers.get(id)
#container=client.containers.list(filters={"id":id})
print(container)
run=container.exec_run(['sh', '-c', str2])
print(type(run))
print(run)
temp1=(run.decode("utf-8"))
print(type(temp1))
print((temp1))

out1 = [int(s) for s in temp1.split() if s.isdigit() and int(s)>100]
ulTh = out1[0:t+1]
#print(ulTh)
dlTh = out1[t+1:]
#print(out1[t+1:])
out2 =sum(out1)/len(out1)
print(out2)
""" temp2=json.dumps(temp1)
print(temp2[0:12])
print(type(temp2))

temp3 = temp2.split(" ")
temp2.replace('[  3] WARNING: did not receive ack of last datagram after 10 tries.','')
 """

#print(temp3)


