import docker
from flask import Flask, request, jsonify
import sys, os
import time

app= Flask(__name__)


list_nfs=['nrf','amf','upf','gnb','ue','udm','udr','smf','ausf','nssf','pcf','n3iwf']    

def count_NFs(client):
    counts=0
    no_UEs=0
    no_gNBs=0
    no_UPFs=0
    for container in client.containers.list():
        print(container.name)
        match = next((x for x in list_nfs if x in container.name), False)
        if match==False:
            continue        
        if "free5gc" in str(container.image):
            print(container.name)
            counts+=1
        if 'ue' in str(container.name):
            no_UEs+=1
        if 'gnb' in str(container.name):
            no_gNBs+=1
        if 'upf' in str(container.name):
            no_UPFs+=1            
    print(counts)
    print(no_UEs)
    print(no_gNBs)
    print(no_UPFs)
    return counts, no_UEs, no_gNBs, no_UPFs

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
    "State":'',
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
        state= 'active'
        client=docker.from_env()
        CN_Data["no_NFs"], RAN_Data["no_UEs"], RAN_Data["no_gNBs"], CN_Data["no_UPFs"]=count_NFs(client)
        CN_Data["no_conn_gNBs"]=RAN_Data["no_gNBs"]
        CN_Data["State"]=state
        RAN_Data["State"]=state
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
        CN_Data["State"]=state
        RAN_Data["State"]=state
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
        CN_Data["State"]=state
        RAN_Data["State"]=state
        Data["CN_data"]=CN_Data
        Data["RAN_data"]=RAN_Data
        return jsonify(Data),200



#start flask app
if __name__=='__main__':
    app.run(host = '0.0.0.0',port=sys.argv[1])

#docker_deploy('OAI','OAI')