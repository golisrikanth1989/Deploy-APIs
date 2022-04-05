import docker
from flask import Flask, request, jsonify
import sys, os
import time

app= Flask(__name__)

def num_PDUsessions(client,id):
    for container in client.containers.list():
        if id in str(container.id):
            run=container.exec_run('nr-cli --dump')
            temp1=(run.output.decode("utf-8")).split("\n")
            ue_imsi=temp1[0]
            temp1=container.exec_run('nr-cli ' + ue_imsi + ' -e ps-list')
            temp2=(temp1.output.decode("utf-8")).split("PDU Session")
            st = "state: PS-ACTIVE"
            res = [i for i in temp2 if st in i]
            return len(res)

def get_IPaddress(client,id):
    #print("get_IPaddress")
    container=client.containers.list(filters={"id":id})
    #print(container)
    if len(container)==0:
        print ("no container running with given id")
        return
    try:
        if 'rfsim' in container[0].name:
            run = container[0].exec_run(['sh', '-c', 'hostname -i'])
            ip_add=(run.output.decode("utf-8")).split("\n")
            return ip_add[0]
        else:    
            ip_add = container[0].attrs["NetworkSettings"]["Networks"]["free5gc-compose_privnet"]["IPAddress"]
            return ip_add
    except: 
        print ("Error in getting IP address")
        return    


def get_gNB(client, id): # get gNB for the UE with container id = id
    #print("get_gnb")
    container=client.containers.list(filters={"id":id})
    if len(container)==0:
        print ("no container running with given id")
        return
    try:
        #if 'oai' in container[0].name:
        run = container[0].exec_run(['sh', '-c', 'echo $RFSIMULATOR'])
        out=(run.output.decode("utf-8")).split("\n")
        return out[0]
        #else:
        #    run = container[0].exec_run(['sh', '-c', 'echo $GNB_HOSTNAME'])
        #    out=run.output.decode("utf-8")
        #    return out
    except: 
        print ("Error in running exec_run")    
        return


def ues_served(client, container1):
    print("ues_served")
    print(container1.id)
    list_ue_containers=[]
    for container in client.containers.list():
        try:
            if 'ue' in container.name:
                print(container.name)
                if 'oai' in container.name:
                    run = container.exec_run(['sh', '-c', 'echo $RFSIMULATOR'])
                    out=(run.output.decode("utf-8")).split("\n")
                    print(out)
                    ip = get_IPaddress(client,container1.id)
                    if ip == out[0]:
                        list_ue_containers.append(container)
                else:
                    run = container.exec_run(['sh', '-c', 'echo $GNB_HOSTNAME'])
                    out=run.output.decode("utf-8")
                    print(out)
                    print(type(out))
                    print(container1.name)
                    if container1.name in str(out):
                        list_ue_containers.append(container)
        except: 
            print ("Error in ues_served")    
        
    return list_ue_containers

list_valid=['nrf','amf','upf','gnb','ue','udm','udr','smf','ausf','nssf','pcf','n3iwf','spgwu']  
list_nfs=['nrf','amf','upf','udm','udr','smf','ausf','nssf','pcf','n3iwf','spgwu']  

def count_NFs(client):
    counts=0
    no_UEs=0
    no_gNBs=0
    no_UPFs=0
    for container in client.containers.list():
        match = next((x for x in list_valid if x in container.name), False)
        if match==False:
            continue        
        if "free5gc" in str(container.image):
            counts+=1
        elif "oai" in str(container.name):
            match1 = next((x for x in list_nfs if x in container.name), False)
            if match1!=False:
                counts+=1   
        if 'ue' in str(container.name):
            no_UEs+=1
        if 'gnb' in str(container.name):
            no_gNBs+=1
        if "free5gc" in str(container.image) and 'upf' in str(container.name):
            no_UPFs+=1
        elif "oai" in str(container.name) and 'spgwu' in str(container.name):    
            no_UPFs+=1      
    #print(counts)
    #print(no_UEs)
    #print(no_gNBs)
    #print(no_UPFs)
    return counts, no_UEs, no_gNBs, no_UPFs

def display_gNBDetails(client):
    print("display_gNBDetails")
    List_gNBs=[]
    gNB_details = {}
    for container in client.containers.list():
        gNB_details = {}
        if 'gnb' in container.name:
            print(container.name)
            gNB_details["Name_of_gNB"]=container.name
            #no_PDUsessions = 0
            ues = ues_served(client,container)
            gNB_details["no_UEs"] = len(ues)
            #for ue in ues:
            #    no_PDUsessions += num_PDUsessions(client,ue.id)
            #gNB_details["no_PDUsess"] =  no_PDUsessions   
            gNB_details["Management_IP"] = get_IPaddress(client,container.id)
            state= 'Active'
            gNB_details["State"] = state
            List_gNBs.append(gNB_details)
    return List_gNBs        


def display_UEDetails(client):
    #print("display_UEDetails")
    List_UEs=[]
    for container in client.containers.list():
        UE_details = {}
        if 'ue' in container.name:
            #print(container.name)
            UE_details["Name_of_UE"]=container.name
            UE_details["Connected to gNB"] =  get_gNB(client,container.id)   
            UE_details["Management_IP"] = get_IPaddress(client,container.id)
            state= 'Connected'
            UE_details["State"] = state
            List_UEs.append(UE_details)
    return List_UEs 

###############################################################
@app.route('/stop_Scenario/<CN>/<RAN>')
def stop_Scenario(CN,RAN):
    # select scenario of CN and RAN and then deploy the scenario
    if CN == 'free5gc' and RAN == 'UERANSIM':
        print("free5gc CN and UERANSIM RAN")
        pwd=os.getcwd()
        print(pwd)
        os.chdir('../')
        os.chdir('5-fi-docker')
        os.chdir('free5gc-compose')
        os.system('docker-compose down')
        os.chdir('../..')
        os.chdir('Deploy-APIs')
        pwd=os.getcwd()
        print(pwd)         
        return jsonify({"response":"success"}), 200
    elif CN == 'free5gc' and RAN == 'OAI':
        print("free5gc CN and OAI RAN")
        pwd=os.getcwd()
        print(pwd)
        os.chdir('../')
        os.chdir('5-fi-docker-oai')
        os.chdir('free5gc-compose')
        os.system('docker-compose down')
        os.chdir('../..')
        os.chdir('Deploy-APIs')
        pwd=os.getcwd()
        print(pwd)    
        return jsonify({"response":"success"}), 200
    elif CN == 'OAI' and RAN == 'OAI':
        print("OAI CN and OAI RAN")
        pwd=os.getcwd()
        print(pwd)
        os.chdir('../')
        os.chdir('openairinterface-5g')
        os.chdir('ci-scripts/yaml_files/5g_rfsimulator')
        os.system('docker-compose down')
        os.chdir('../../../..')
        os.chdir('Deploy-APIs')
        pwd=os.getcwd()
        print(pwd)
        return jsonify({"response":"success"}), 200 


@app.route('/deploy_Scenario/<CN>/<RAN>')
def deploy_Scenario(CN,RAN):
    #dictionaries for json
    Data={"CN_data":[], "RAN_data":[]}
    CN_Data={"Make_of_CN":'',
    "no_NFs":0,
    "no_conn_gNBs":0, #No of gNBs connected
    "State":'',
    "no_UPFs":0,
    }
    RAN_Data={"Make_of_RAN":'',
    "no_UEs":0,
    "no_gNBs":0,
    "gNB_List":[],
    "UE_List":[],
    }

    # select scenario of CN and RAN and then deploy the scenario
    if CN == 'free5gc' and RAN == 'UERANSIM':
        print("free5gc CN and UERANSIM RAN")
        CN_Data["Make_of_CN"]=CN
        RAN_Data["Make_of_RAN"]=RAN
        os.chdir('../')
        #check if directory already exists
        if os.path.isdir('5-fi-docker'):
            print('True')
        else:
            print('False')    
            os.system('git clone https://github.com/pragnyakiri/5-fi-docker')
        os.chdir('5-fi-docker')
        os.system('git pull')
        print("Pulled")            
        os.chdir('ueransim')
        os.system('make')
        print("ueransim made")
        os.chdir('../free5gc-compose')
        os.system('make base')
        print("make base")
        os.system('docker-compose build')
        os.system('docker-compose up -d')
        os.chdir('../..')
        os.chdir('Deploy-APIs')
        pwd=os.getcwd()
        print(pwd)
        state= 'Active'
        client=docker.from_env()
        CN_Data["no_NFs"], RAN_Data["no_UEs"], RAN_Data["no_gNBs"], CN_Data["no_UPFs"]=count_NFs(client)
        CN_Data["no_conn_gNBs"]=RAN_Data["no_gNBs"]
        gnb_List = display_gNBDetails(client)
        UE_List = display_UEDetails(client)
        CN_Data["State"]=state
        RAN_Data["gNB_List"]=gnb_List
        RAN_Data["UE_List"]=UE_List
        Data["CN_data"]=CN_Data
        Data["RAN_data"]=RAN_Data
        return jsonify(Data),200
    elif CN == 'free5gc' and RAN == 'OAI':
        print("free5gc CN and OAI RAN")
        CN_Data["Make_of_CN"]=CN
        RAN_Data["Make_of_RAN"]=RAN
        os.chdir('../')
        #check if directory already exists
        if os.path.isdir('5-fi-docker-oai'):
            print('True')
        else:
            print('False')    
            os.system('git clone https://github.com/pragnyakiri/5-fi-docker-oai')
        os.chdir('5-fi-docker-oai')
        os.system('git pull')
        os.chdir('free5gc-compose')
        os.system('make base')
        print("make base")        
        os.system('sudo docker-compose build')
        os.system('sudo docker-compose up -d --remove-orphans')
        os.chdir('../..')
        os.chdir('Deploy-APIs')
        pwd=os.getcwd()
        print(pwd)
        state= 'active' 
        client=docker.from_env()
        CN_Data["no_NFs"], RAN_Data["no_UEs"], RAN_Data["no_gNBs"], CN_Data["no_UPFs"]=count_NFs(client)
        CN_Data["no_conn_gNBs"]=RAN_Data["no_gNBs"]
        gnb_List = display_gNBDetails(client)
        UE_List = display_UEDetails(client)
        CN_Data["State"]=state
        RAN_Data["gNB_List"]=gnb_List
        RAN_Data["UE_List"]=UE_List
        Data["CN_data"]=CN_Data
        Data["RAN_data"]=RAN_Data
        return jsonify(Data),200
    elif CN == 'OAI' and RAN == 'OAI':
        print("OAI CN and OAI RAN")
        CN_Data["Make_of_CN"]=CN
        RAN_Data["Make_of_RAN"]=RAN
        os.chdir('../')
        #check if directory already exists
        if os.path.isdir('openairinterface-5g'):
            print('True')
        else:
            print('False')    
            os.system('git clone https://github.com/pragnyakiri/openairinterface-5g')
        os.chdir('openairinterface-5g')
        os.system('git checkout develop')
        os.system('git pull')
        os.chdir('ci-scripts/yaml_files/5g_rfsimulator')
        os.system('docker-compose up -d mysql oai-nrf oai-amf oai-smf oai-spgwu oai-ext-dn')
        print("CN is UP")   
        time.sleep(30)     
        os.system('docker-compose ps -a')
        time.sleep(10)
        os.system('docker-compose up -d oai-gnb')
        time.sleep(20)
        os.system('docker-compose ps -a')
        time.sleep(20)     
        os.system('docker-compose ps -a')
        os.system('docker-compose up -d oai-nr-ue')
        time.sleep(20)     
        os.system('docker-compose ps -a')
        os.chdir('../../../..')      
        os.chdir('Deploy-APIs')
        pwd=os.getcwd()
        print(pwd) 
        state= 'active'
        client=docker.from_env()
        CN_Data["no_NFs"], RAN_Data["no_UEs"], RAN_Data["no_gNBs"], CN_Data["no_UPFs"]=count_NFs(client)
        CN_Data["no_conn_gNBs"]=RAN_Data["no_gNBs"]
        gnb_List = display_gNBDetails(client)
        UE_List = display_UEDetails(client)
        CN_Data["State"]=state
        RAN_Data["gNB_List"]=gnb_List
        RAN_Data["UE_List"]=UE_List
        Data["CN_data"]=CN_Data
        Data["RAN_data"]=RAN_Data
        return jsonify(Data),200



#start flask app
if __name__=='__main__':
    app.run(host = '0.0.0.0',port=sys.argv[1])

#docker_deploy('OAI','OAI')
#client=docker.from_env()
#id="d477c3f6c800"
#container=client.containers.list(filters={"id":id})
#container[0].exec_run(['sh', '-c', 'echo $GNB_HOSTNAME'])
#ues_served(client)