import docker
import json
import sqlite3
import multiprocessing as mp
import datetime
import os
import time 
import indexes

stop=0

# 1. Data Volume measurement separately for DL and UL, per QCI per UE, by eNB
# 2. Throughput separately for DL and UL, per RAB per UE and per UE for the DL, per UE for the UL, by eNB
# 3. Packet Delay measurement, separately for DL and UL, per QCI per UE
# 4. Packet Loss rate measurement, separately for DL and UL per QCI per UE, by the eNB
# 5. Number of active UEs in RRC_CONNECTED

def get_num_servedUEs(client,id):
    container=client.containers.list(filters={"id":id})
    if len(container)==0:
        print ("no container running with given id")
        return
    logs = container[0].logs().decode("utf-8")
    st = 'Total number of UEs'
    res = logs.rfind(st)
    return logs[res+21]
def kill_meas_collection():
    global stop
    stop=1

def get_num_ActiveUEs(client,id):
    Num_ActiveUEs=[]
    container=client.containers.list(filters={"id":id})
    if len(container)==0:
        print ("no container running with given id")
        return
    run=container[0].exec_run('nr-cli --dump')
    temp1=(run.output.decode("utf-8")).split("\n")
    gnb_id=temp1[0]
    temp1=container[0].exec_run('nr-cli ' + gnb_id + ' -e ue-list')
    temp2=temp1.output.decode("utf-8")
    st = "ue-id:"
    res = [i for i in range(len(temp2)) if temp2.startswith(st, i)]
    Num_ActiveUEs.append(len(res)) 
    sum=0
    for i in Num_ActiveUEs:
        sum = sum + i
    return(sum)  

def get_db():
    conn=sqlite3.connect('db_for_flask.db',isolation_level=None)
    return conn

def make_meas_table():
    conn = get_db()
    cursor=conn.cursor()
    """Clear existing data and create new table for measurements"""
    sql = "DROP TABLE IF EXISTS measurements"
    cursor.execute(sql)
    sql="CREATE TABLE measurements (ue_name TEXT NOT NULL, id TEXT NOT NULL, gnb_name TEXT NOT NULL, time_stamp TEXT NOT NULL, DL_Thp REAL, UL_Thp REAL, Latency REAL, Tx_Bytes REAL, Rx_Bytes REAL)"
    cursor.execute(sql)
    return cursor
    
def if_table_exists(cursor,table_name):
    sql="SELECT name FROM sqlite_master WHERE type='table' AND name='"+table_name+"'; "
    listOfTables = cursor.execute(sql).fetchall()
    if listOfTables == []:
        return False
    else:
        return True

def get_IPaddressOfUE(client,id):
    container=client.containers.list(filters={"id":id})
    if len(container)==0:
        print ("no container running with given id")
        return
    run=container[0].exec_run('ip -j a')
    ipraw=run.output.decode("utf-8")
    ipjson=json.loads(ipraw)
    ip=""
    for dicts in ipjson:
        if dicts['ifname']=='oaitun_ue1':
            for subdicts in dicts['addr_info']: 
                if subdicts['label']=='oaitun_ue1':
                    ip=subdicts['local']
    return ip

def get_measurements(client):
    indexes.write_ip_index_table(client)
    global stop
    cursor = make_meas_table()
    while True:
        if stop ==1:
            stop=0
            break
        ts = datetime.datetime.now()
        processes =[ mp.Process(target=write_measurements, args=(client,server,cursor,str(ts))) for server in client.containers.list() if 'ue' in server.name]
        # Run processes
        for p in processes:
            p.start()
            time.sleep(90)

        # Exit the completed processes
        for p in processes:
            p.join()


def write_measurements(client,container,cursor,ts):
    IPaddr = get_IPaddressOfUE(client,container.id)
    print(IPaddr)
    if IPaddr != "":
        ue_listen_iperf = 'iperf -s -i 1 -B '+ IPaddr
        ext_ping_iperf= 'iperf -u -i 1 -fk -b 125M -c '+IPaddr+' -t 10 | awk -Wi -F\'[ -]+\' \'/sec/{print $3"-"$4" "$8}\''
        ue_ping_cmd="ping -I oaitun_ue1 192.168.72.135 -c 10"
        ext_container=client.containers.list(filters={"name":"rfsim5g-oai-ext-dn"})
        #'iperf -u -i 1 -fk -B'+ IPaddr+ '-b 125M -c 192.168.72.135 -t 10 | awk -Wi -F\'[ -]+\' \'/sec/{print $3"-"$4" "$8}\''
        gnb_name = get_gNB(client,container.id)
        print("GNB name",gnb_name)
        gnb_Container = client.containers.list(filters={"name":gnb_name.strip()})
        
        if len(container.name)==0:
            print ("UE container not found with given name")
            return
        try:
            ue_iperf_run=container.exec_run(['sh', '-c', ue_listen_iperf])
            ext_iperf_run=ext_container[0].exec_run(['sh', '-c', ext_ping_iperf])
            temp1=(ext_iperf_run.output.decode("utf-8"))
            temp2 = [int(s) for s in temp1.split() if s.isdigit() and int(s)>100]
            temp2 =sum(temp2)/len(temp2)
            ue_ping_run=container.exec_run(['sh', '-c', ue_ping_cmd])
            result=ue_ping_run.output.decode("utf-8")
            lat=[int(r.split(' ms')[0]) for r in result.split('time=') if r[0].is_digit()]      
            dl_thp = temp2 # bits per second
            ul_thp = 0#temp2['upload']
            latency = sum(lat)/len(lat)#temp2['server']['latency']
            #tx_byte,rx_byte=get_TxRx_Bytes(client,container.name)
            print("Reached here")
        except Exception as e:
            print ("Error in running speedtest "+str(e))
        try:
            cursor.execute("INSERT INTO measurements (ue_name,id,gnb_name,time_stamp,DL_Thp,UL_Thp,latency) VALUES ( ?, ?, ?, ?, ?, ?, ?)", (container.name, container.id, gnb_Container[0].name, ts, dl_thp, ul_thp, latency) )
        except :
            print ("measurements insert not executing")
        time.sleep(90)

def get_gNB(client,id):
    #print("get_gnb")
    container=client.containers.list(filters={"id":id})
    if len(container)==0:
        print ("no container running with given id")
        return
    try:
        if 'oai' in container[0].name:
            run = container[0].exec_run(['sh', '-c', 'echo $RFSIMULATOR'])
            out=(run.output.decode("utf-8")).split("\n")
            print("out[0]", out[0])
            gnb_details=indexes.get_name_and_id_from_ip(out[0])
            print(gnb_details)
            return gnb_details[0][0]
        else:
            run = container[0].exec_run(['sh', '-c', 'echo $GNB_HOSTNAME'])
            out=(run.output.decode("utf-8")).split("\n")
            return out[0]
    except: 
        print ("Error in running exec_run")    
        return     
    

def read():
    conn=get_db()
    cursor=conn.cursor()
    sql="SELECT * FROM measurements; "
    if if_table_exists(cursor,'measurements'):
        cursor.execute(sql)
        args=cursor.fetchall()
    else:
        args=0
        print("No data exists in database table measurements")
    cursor.close()
    conn.close()
    return args

def get_TxRx_Bytes(client,name):
    container=client.containers.list(filters={"name":name})
    if len(container)==0:
        print ("no container running with given name")
        return
    try:
        run=container[0].exec_run(['sh', '-c', 'ifconfig uesimtun0 | grep RX'])
        temp1=(run.output.decode("utf-8")).split('bytes ')
        m = temp1[1].split(' ')
        rx_bytes=m[0]
        run=container[0].exec_run(['sh', '-c', 'ifconfig uesimtun0 | grep TX'])
        temp2=(run.output.decode("utf-8")).split('bytes ')
        n = temp2[1].split(' ')
        tx_bytes=n[0]
    except: 
        rx_bytes=0
        tx_bytes=0
        print ("Error in running exec_run")
    return tx_bytes,rx_bytes


def get_Health(shortid):
    run=os.popen("docker ps -q ")
    r = run.read().replace('\n','')
    flag=0
    if shortid in r:
        flag=1
    return flag
def make_latency_table(cursor):
    sql="CREATE TABLE IF NOT EXISTS latency (sug_action_key INTEGER PRIMARY KEY AUTOINCREMENT,\
         uename TEXT UNIQUE NOT NULL, ueid TEXT NOT NULL, avg_latency TEXT NOT NULL)"
    cursor.execute(sql)
    return    
#include packet loss from png command, modify ping command
def get_PingLatency(client,name):
    latency_values=[]
    avg_latency=0
    container=client.containers.list(filters={"name":name})
    #print(container[0].name)
    if len(container)==0:
        print ("no container running with given name")
        return
    try:
        run=container[0].exec_run('ping -I uesimtun0 142.250.183.206 -c 10')
        temp=run.output.decode("utf-8")
        temp1=temp.split('rtt ')
        temp2=temp1[1].split('=')
        temp3=temp2[1].split('/')
        tmp=temp.split('time=')
        for i in range(1,len(tmp)):
            tmp1=tmp[i].split('ms')
            if i != len(tmp):
                latency_values.append(tmp1[0])
        #avg_latency=int(''.join([i for i in temp3[1] if (i.isdigit() or i=='.')]))
        avg_latency=float(temp3[1].strip())
        if avg_latency > 50:
            conn=get_db()
            cursor=conn.cursor()
            make_latency_table(cursor)
            cursor.execute("INSERT INTO latency (uename,ueid,avg_latency) VALUES(?,?,?)",(container[0].name,container[0].id,avg_latency))
    except: 
        print ("Error in running Ping command")
    return latency_values,avg_latency

def read_actions():
    output={'action_button':'no',"action_button_text":''}
    conn=get_db()
    cursor=conn.cursor()
    list_of_tables=cursor.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='latency'; """).fetchall()
    if len(list_of_tables)==0:
        output['action_button']='no'
        output['action_button_text']=''
    else:
        sql="SELECT * FROM latency"
        actions=cursor.execute(sql).fetchall()
        if len(actions)==0:
            output['action_button']='no'
            output['action_button_text']=''
        else:
            uename=actions[0][1]
            avg_latency=actions[0][3]
            output['action_button']='yes'
            output['action_button_text']=uename+' is experiencing '+avg_latency+'ms of latency. Switch the Userplane path'
    conn.close()
    return output
def pop_latency():
    conn=get_db()
    cursor=conn.cursor()
    list_of_tables=cursor.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='latency'; """).fetchall()
    if len(list_of_tables)==0:
        return
    else:
        sql="SELECT * FROM latency"
        actions=cursor.execute(sql).fetchall()
        if len(actions)==0:
            return
        else:
            action_id=actions[0][0]
            sql="DELETE FROM latency WHERE sug_action_key='"+str(action_id)+"'; "
            cursor.execute(sql)
            return

#client=docker.from_env()
#id = "19f0f29cfbc11fd4464d5dde07d8c68882e4ad41b55ed1f228ce383ebc85072a"
#get_num_ActiveUEs(client)
#res=read()
#print(res)
#get_IPaddressOfUE(client,id)
#get_TxRx_Bytes(client,'ue1')
#write(client,str(datetime.datetime.now()))
#read('ue2')
#read('ue1')
#get_Health(client,id)
#p=get_PingLatency(client,'ue1')
#print(p)