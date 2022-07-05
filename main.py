import docker
from fastapi import FastAPI, HTTPException, Form, Path, Query
from enum import Enum
# import packets
from flask import Flask, request, jsonify
import urllib, json
#from fastapi.exception_handlers import (
#    http_exception_handler,
#    request_validation_exception_handler,
#)
#from pydantic import ValidationError
#from fastapi.exceptions import RequestValidationError
#from fastapi.responses import PlainTextResponse
import uvicorn
import sys, os
import subprocess as sp
import time
import random
from pydantic import BaseModel

import threading
import measurements

################################################################################################################################################################
#                                                                Defining Dictionaries for List of Elements                                                    #
################################################################################################################################################################
CN_List = [
    {"name" : "OAI", "status" : True},
    {"name" : "free5GC", "status" : True},
    {"name" : "Azure Private 5G Core", "status" : False},
    {"name" : "free5GC", "status" : False}
]
RAN_List = [
    {"name" : "OAI", "status" : True},
    {"name" : "UERANSIM", "status" : True},
    {"name" : "Baicells", "status" : False},
    {"name" : "Nokia", "status" : False}
]
UE_List = [
    {"name" : "OAI", "status" : True},
    {"name" : "UERANSIM", "status" : True},
    {"name" : "srsRAN", "status" : False},
]
Network_List = [
    {"name" : "All", "ID":0,"status" : True},
    {"name" : "Network1","ID":1, "status" : True},
    {"name" : "Network2", "ID":2,"status" : True},
    {"name" : "Network3", "ID":3,"status" : False},
    {"name" : "Network4", "ID":4,"status" : False},
    {"name" : "Network5", "ID":5,"status" : False}
]
App_Hosted_List = [
    {"name" : "Cloud", "status" : True},
    {"name" : "Internal", "status" : True},
    {"name" : "External", "status" : True}
]
App_Details = [
    {"Application Name" : "Pick-N-Pack", "status" : True},
    {"Input1" : "Weight Sensor", "Input2":"Video Stream","status" : True},
    {"Output1" : "Video Analytics/Dashboard", "Output2":"Actuator","status" : True}
]

################################################################################################################################################################
#                                                                        Input Options for APIs                                                                #
################################################################################################################################################################
class Item(BaseModel):
    id: str
    value: str

class Message(BaseModel):
    message: str

class CN_options(str, Enum):
    free5gc = "free5gc"
    OAI = "OAI"
    Azure = "Azure Private 5GCore"
    Nokia = "Nokia"

class RAN_options(str, Enum):
    UERANSIM = "UERANSIM"
    OAI = "OAI"
    AirSpan = "AirSpan"
    Baicells = "Balicells"

class UE_options(str, Enum):
    free5gc = "UERANSIM"
    OAI = "OAI"
    Nokia = "srsRAN"

class APP_options(str, Enum):
    free5gc = "Cloud"
    OAI = "Internal"
    Nokia = "External"

################################################################################################################################################################
#                                                                             Tags for APIs                                                                    #
################################################################################################################################################################
tags_metadata = [
    {
        "name": "Get Core Networks List",
        "description": "List of Core Network (CN) Available.",
    },
    {
        "name": "Get Access Points List",
        "description": "List of Access Points Available.",
    },
    {
        "name": "Get Devices List",
        "description": "List of Devices Available.",
    },
    {
        "name": "Deploy a Network",
        "description": "Deploy a network with Core Network (CN) and Radio Access Network (RAN) stack of your choice.",
    },
    {
        "name": "Stop a Network",
        "description": "Stop the network with Core Network (CN) and Radio Access Network (RAN) stack of your choice.",
    },
    {
        "name": "Get CN details",
        "description": "Get information about the Core Network (CN) of the deployed network.",
    },    
    {
        "name": "Get RAN details",
        "description": "Get information about the Radio Access Network (RAN) of the deployed network.",
    },    
    {
        "name": "Get gNB details",
        "description": "Get information about the gNBs deployed in the network.",
    },   
    {
        "name": "Get UE details",
        "description": "Get information about the UEs in the network.",
    },
    {
        "name": "Get Network Summary",
        "description": "Get Network Statistics such as Latency, Packet Loss, Throughput and Mobility",
    },
    {
        "name": "Get Network Statistics",
        "description": "Get Network Statistics such as Latency, Packet Loss, Throughput and Mobility",
    },
    {
        "name": "Get Network Lists",
        "description": "Get List of Deployed Networks",
    },  
    {
        "name": "Get Network Inspect Details",
        "description": "Get Network Functions Terminals, Logs and Packets",
    },     
    {
        "name": "Get Logs",
        "description": "Get logs of the container with containerid mentioned.",
    },
    {
        "name": "Get Console",
        "description": "Get Console of the container with containerid mentioned.",
    },
    {
        "name": "Get Packets",
        "description": "Get Packets of the container with containerid mentioned.",
    },  
    {
        "name": "Get Network Issues and Resolving Actions",
        "description": "Get Packets of the container with containerid mentioned.",
    },               
]                        

app = FastAPI(
    title="5-Fi APIs",
    description="APIs for 5-Fi Console",
    version="1.0.0",
    contact={
        "name": "5-Fi",
        "url": "http://5-fi.net/",
        "email": "5-fi@dolcera.com",
    },
    openapi_tags=tags_metadata,
)

################################################################################################################################################################
#                                                                       Functions for APIs                                                                     #
################################################################################################################################################################

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
        if 'oai' in container[0].name:
            run = container[0].exec_run(['sh', '-c', 'echo $RFSIMULATOR'])
            out=(run.output.decode("utf-8")).split("\n")
            return out[0]
        else:
            run = container[0].exec_run(['sh', '-c', 'echo $GNB_HOSTNAME'])
            out=(run.output.decode("utf-8")).split("\n")
            return out[0]
    except: 
        print ("Error in running exec_run")    
        return


def ues_served(client, container1):
    #print("ues_served")
    list_ue_containers=[]
    for container in client.containers.list():
        try:
            if 'ue' in container.name:
                if 'oai' in container.name:
                    run = container.exec_run(['sh', '-c', 'echo $RFSIMULATOR'])
                    out=(run.output.decode("utf-8")).split("\n")
                    ip = get_IPaddress(client,container1.id)
                    if ip == out[0]:
                        list_ue_containers.append(container)
                else:
                    run = container.exec_run(['sh', '-c', 'echo $GNB_HOSTNAME'])
                    out=run.output.decode("utf-8")
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
    #print("display_gNBDetails")
    List_gNBs=[]
    gNB_details = {}
    for container in client.containers.list():
        gNB_details = {}
        if 'gnb' in container.name:
            #print(container.name)
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


def get_logs(client,id):
    for container in client.containers.list():
        if id in str(container.id):
            logs = container.logs().decode("utf-8")
            return logs

def get_console(client,id):
    for container in client.containers.list():
        if id in str(container.id):
            console = container.logs().decode("utf-8")
            return console


#@app.route('/monitor_nf_packets/<id>')
def get_packets(client,id):
    #dictionaries for json
    monitor_nf={"NF_packets":''}
    container=client.containers.list(filters={"id":id})
    monitor_nf["NF_packets"]=packets.get_packets(container[0].name)
    return jsonify(monitor_nf),200

def get_network_attention(tag_issue,CMessage,CSite,CSwitch,CPort,CID):
    network_attention = [{"Tag":tag_issue,"Message" : CMessage, "Site" : CSite,"Switch":CSwitch, "Port": CPort,"ID":CID}]      
    return network_attention

def get_resolved_action(tag_issue,CID,CMessage,CSite):
    resolved_action = [{"Tag":tag_issue,"ID":CID,"Message" : CMessage, "Site" : CSite}]      
    return resolved_action



################################################################################################################################################################
#                                                                     List of Elements APIs                                                                    #
################################################################################################################################################################
###############################################################
# Exception Handler
#@app.exception_handler(ValidationError)
#def validation_exception_handler(request, exc):
#    return PlainTextResponse(str(exc), status_code=400)

#@app.exception_handler(RequestValidationError)
#async def validation_exception_handler(request, exc):
#    print(f"OMG! The client sent invalid data!: {exc}")
#    return await request_validation_exception_handler(request, exc)

# @app.get("/models/{model_name}")
# async def get_model(model_name: ModelName):
#      print('get_model')
#      print(model_name)
###############################################################

@app.get('/CN_list', tags = ["Get Core Networks List"], status_code=200)

def get_cn_List()-> dict:
    return {"CN_List": CN_List}

###############################################################

@app.get('/RAN_list', tags = ["Get Access Points List"],status_code=200)

def get_ran_List()-> dict:
    return {"RAN_List": RAN_List}
###############################################################

@app.get('/UE_list', tags = ["Get Devices List"],status_code=200)

def get_ue_List()-> dict:
    return {"UE_List": UE_List}
###############################################################

@app.get('/Network_List', tags = ["Get Network Lists"],status_code=200)

def get_Network_List()-> dict:
    return {"Network_List": Network_List}

@app.get('/ApplicationDetails/', tags = ["Get Application Details"],status_code=200)

def get_Application_Details()-> dict:
    return {"Application Details": App_Details}    

################################################################################################################################################################
#                                                                Network Deploy & Undeploy APIs                                                                #
################################################################################################################################################################

@app.get(
    "/deploy_scenario/", 
    tags=["Deploy a Network"], 
    responses={
        404: {
            "description": "The requested resource was not found",
            "content": {
                "application/json": {
                    "example": {"response":"The requested resource was not found"}
                }
            },
        },    
        200: {
            "description": "Successful response.",
            "content": {
                "application/json": {
                    "example": {"response":"Success! Network deployed!"}
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {"response":"Invalid parameters! Please use valid parameters."}
                }
            },
        },        
    },
)

####################################################################################################################

def deploy_Scenario(CN_Make: CN_options,CN_Quantity,RAN_Make: RAN_options,RAN_Quantity,Cameras_Make: UE_options,Cameras_Quantity,Sensors_Make: UE_options,Sensors_Quantity,AGVs_Make:UE_options,AGVs_Quantity,Actuators_Make:UE_options,Actuators_Quantity,Others_Make:UE_options, Other_Quantity):
    if CN_Make == 'OAI' and RAN_Make == 'OAI':
        print("OAI CN and OAI RAN")
        os.chdir('../')
        #check if directory already exists
        if os.path.isdir('openairinterface-5g'):
            print('True')
        else:
            print('False')    
            os.system('git clone https://github.com/golisrikanth1989/openairinterface-5g')
        os.chdir('openairinterface-5g')
        os.system('git checkout develop')
        os.system('git pull')
        os.chdir('ci-scripts/yaml_files/5g_rfsimulator')
        os.system('docker ps -aq | xargs docker rm -f')
        time.sleep(30)
        for i in range(int(CN_Quantity)):
            cn_str = "cn" + str(i+1)
            cmd = 'docker-compose -f docker-compose.yaml up -d  mysql oai-nrf oai-amf oai-smf oai-spgwu oai-ext-dn'
            os.system(cmd)
            time.sleep(10)

            cmd = 'docker-compose -f docker-compose.yaml up -d oai-gnb1'
            print(cmd)
            os.system(cmd)
            time.sleep(10)

            cmd = 'docker-compose -f docker-compose.yaml up -d oai-gnb2'
            print(cmd)
            os.system(cmd)
            time.sleep(10)
            
            # For First gNB
            cmd = 'docker-compose -f docker-compose.yaml up -d oai-nr-ue1' 
            print(cmd)
            os.system(cmd)
            time.sleep(10)

            cmd = 'docker-compose -f docker-compose.yaml up -d oai-nr-ue2' 
            print(cmd)
            os.system(cmd)
            time.sleep(10)
            
            # For Second gNB  
            cmd = 'docker-compose -f docker-compose.yaml up -d oai-nr-ue3' 
            print(cmd)
            os.system(cmd)
            time.sleep(10)
            
            cmd = 'docker-compose -f docker-compose.yaml up -d oai-nr-ue4' 
            print(cmd)
            os.system(cmd)
            time.sleep(10)
            print('OAI CN and OAI RAN with UEs are Deployed')
    elif CN_Make == 'OAI' and RAN_Make == 'UERANSIM':
        print("Selected OAI CN and UERANSIM Make")
        os.chdir('../')
        os.chdir('oai-cn5g-fed')
#        os.system('git checkout develop')
#        os.system('git pull')
        os.chdir('docker-compose')
#        os.system('docker ps -aq | xargs docker rm -f')
        time.sleep(30)
        for i in range(int(CN_Quantity)):
            cn_str = "cn" + str(i+1)
            cmd = 'docker-compose -p '+ cn_str + ' -f docker-compose-basic-vpp-nrf.yaml up -d oai-nrf'
            os.system(cmd)
            time.sleep(10)

            cmd = 'docker-compose -p '+ cn_str + ' -f docker-compose1.yaml up -d mysql'
            os.system(cmd)
            time.sleep(10)
            cont_name = cn_str + '_oai-nrf_1'
            cmd = 'docker inspect -f \'{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}\' ' + cont_name
            nrf_ipaddr = os.system(cmd)
            cont_name = cn_str + '_mysql_1'
            cmd = 'docker inspect -f \'{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}\' ' + cont_name
            mysql_ipaddr = os.system(cmd)

            cmd = 'echo \"mysql_ipaddr='+ str(mysql_ipaddr) +'\" \"nrf_ipaddr='+str(nrf_ipaddr)+'\" > .env' + ' && docker-compose -p '+ cn_str + ' -f docker-compose1.yaml up -d oai-amf'
            os.system(cmd)
            time.sleep(10)

            cmd = 'echo \"nrf_ipaddr1='+str(nrf_ipaddr)+'\" > .env' + ' && docker-compose -p '+ cn_str + ' -f docker-compose1.yaml up -d oai-smf'
            os.system(cmd)
            time.sleep(10)
            
            cont_name = cn_str + '_oai-smf_1'
            cmd = 'docker inspect -f \'{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}\' ' + cont_name
            smf_ipaddr = os.system(cmd)
            
            cmd = 'echo \"nrf_ipaddr2='+ str(nrf_ipaddr) +'\" \"smf_ipaddr='+str(smf_ipaddr)+'\" > .env' + ' && docker-compose -p '+ cn_str + ' -f docker-compose1.yaml up -d oai-spgwu' # oai-ext-dn'
            os.system(cmd)
            time.sleep(15)
            print("OAI ",cn_str," is UP")
            print("Connecting OAI-RAN Access Points for ",cn_str)
            
            cont_name = cn_str + '_oai-amf_1'
            cmd = 'docker inspect -f \'{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}\' ' + cont_name
            amf_ipaddr = os.system(cmd)
            print(str(amf_ipaddr))
            cmd = 'echo \"amf_ipaddr='+ str(amf_ipaddr) +'\" > .env' + ' && docker-compose -p '+ cn_str + ' -f docker-compose1.yaml up -d --scale oai-gnb='+str(RAN_Quantity)
            os.system(cmd)
            time.sleep(10)   

            for i in range(int(RAN_Quantity)):
                pr_name = cn_str
                cmd = 'echo \"amf_ipaddr='+ str(amf_ipaddr) +'\" > .env' + ' && docker-compose -p '+ pr_name + ' -f docker-compose1.yaml up -d oai-gnb'
                os.system(cmd)
                cont_name = pr_name + '_oai-gnb_1'
                print(cont_name)
                cmd = 'docker inspect -f \'{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}\' ' + cont_name
                gnb_ipaddr = os.system(cmd)
                nUEs = random.randint(1,4)
                cmd = 'echo \"gnb_ipaddr1='+ str(gnb_ipaddr) +'\" > .env' + ' && docker-compose -p '+ pr_name + ' -f docker-compose1.yaml up -d --scale oai-nr-ue='+str(nUEs)
                os.system(cmd)
                time.sleep(10)
    else :
        return {"Choose Approproiate Option"}


""" def deploy_Scenario(CN: CN_options, CN_Quantity, RAN: RAN_options, RAN_Quantity):
    #try:
    # select scenario of CN and RAN and then deploy the scenario
    if CN == 'free5gc' and RAN == 'UERANSIM':
        print("free5gc CN and UERANSIM RAN")
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
        return {"response":"Success! Network deployed!"}
    elif CN == 'free5gc' and RAN == 'OAI':
        print("free5gc CN and OAI RAN")
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
        return {"response":"Success! Network deployed!"}
    elif CN == 'OAI' and RAN == 'OAI':
        print("OAI CN and OAI RAN")
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
        os.system('docker-compose up -d oai-gnb2')
        time.sleep(20)
        os.system('docker-compose ps -a')
        time.sleep(20)          
        os.system('docker-compose ps -a')
        os.system('docker-compose up -d oai-nr-ue1')
        time.sleep(20)     
        os.system('docker-compose ps -a')
        time.sleep(20)     
        os.system('docker-compose ps -a')
        os.system('docker-compose up -d oai-nr-ue2')
        time.sleep(20)     
        os.system('docker-compose ps -a')
        os.chdir('../../../..')      
        os.chdir('Deploy-APIs')
        pwd=os.getcwd()
        print(pwd)
        return {"response":"Success! Network deployed!"} 
    else: 
        print("Inside ELSE")
        #except ValidationError as err:
        raise HTTPException(status_code=422, detail="Please enter valid parameter values.")
        #raise RequestValidationError(exc="Please enter valid parameter values.") """


###############################################################
@app.get(
    '/stop_scenario/{CN}/{RAN}', 
    tags=["Stop a Network"],
    responses={
        404: {
            "description": "The requested resource was not found",
            "content": {
                "application/json": {
                    "example": {"response":"The requested resource was not found"}
                }
            },
        },    
        200: {
            "description": "Successful response.",
            "content": {
                "application/json": {
                    "example": {"response":"Success! Network deployed!"}
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {"response":"Invalid parameters! Please use valid parameters."}
                }
            },
        },        
    },
) 

def stop_scenario(CN: CN_options,RAN: RAN_options):
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
        return {"response":"Success! Network stopped."}
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
        return {"response":"Success! Network stopped."}
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
        return {"response":"Success! Network stopped."}

        

################################################################################################################################################################
#                                                                 Network Summary APIs                                                                         #
################################################################################################################################################################
@app.get(
    "/cn_details/", 
    tags=["Get CN details"],
    responses={
        404: {
            "description": "The requested resource was not found",
            "content": {
                "application/json": {
                    "example": {"response":"The requested resource was not found. Please check if network is deployed!"}
                }
            },
        },    
        200: {
            "description": "Successful response.",
            "content": {
                "application/json": {
                    "example": {"response":"Success!"}
                }
            },
        },
    },
)
def get_CN_details():
    #dictionaries for json
    CN_Data={"make_of_cn":[],
    "no_nfs":0,
    "no_connected_gnbs":0, #No of gNBs connected
    "state":'',
    "no_upfs":0,
    "cn_count":0,	
    }
    state= 'active'
    client=docker.from_env()
    CN = []    
    Count=0
    for container in client.containers.list():
        print(container.name)
        if 'webui' in container.name:
            CN.append('free5gc')
            Count = Count+1
        elif 'spgw' in container.name:
            CN.append('OAI')
            Count = Count+1        
    if CN==[]:
        raise HTTPException(status_code=404, detail="There is no network deployed. Try deploying a network first.")                     
    CN_Data["make_of_cn"]=CN
    CN_Data["no_nfs"], x, CN_Data["no_connected_gnbs"], CN_Data["no_upfs"]=count_NFs(client)
    CN_Data["state"]=state
    CN_Data["cn_count"]=Count
    return (CN_Data)

###########################################################################
@app.get(
    '/ran_details/', 
    tags=["Get RAN details"],
    responses={
        404: {
            "description": "The requested resource was not found",
            "content": {
                "application/json": {
                    "example": {"response":"The requested resource was not found. Please check if network is deployed!"}
                }
            },
        },    
        200: {
            "description": "Successful response.",
            "content": {
                "application/json": {
                    "example": {"response":"Success!"}
                }
            },
        },
    },    
)
def get_RAN_details():
    #dictionaries for json
    RAN_Data={"make_of_ran":[],
    "no_ues":0,
    "no_gnbs":0,
    "gnb_list":[],
    "ue_list":[],
    }
    state= 'active'
    client=docker.from_env()
    RAN=[]
    for container in client.containers.list():
        if 'gnb' in container.name:
            if 'oai' in container.name:
                RAN.append('OAI')
            else:
                RAN.append('UERANSIM')  
    if RAN==[]:
        raise HTTPException(status_code=404, detail="There is no network deployed. Try deploying a network first.")                                  
    RAN_Data["make_of_ran"]=RAN
    x, RAN_Data["no_ues"], RAN_Data["no_gnbs"], y=count_NFs(client)
    gnb_List = display_gNBDetails(client)
    UE_List = display_UEDetails(client)
    RAN_Data["gnb_List"]=gnb_List
    RAN_Data["ue_List"]=UE_List
    return RAN_Data


###########################################################################
@app.get(
    '/gnb_details/', 
    tags=["Get gNB details"],
    responses={
        404: {
            "description": "The requested resource was not found",
            "content": {
                "application/json": {
                    "example": {"response":"The requested resource was not found. Please check if network is deployed!"}
                }
            },
        },    
        200: {
            "description": "Successful response.",
            "content": {
                "application/json": {
                    "example": {"response":"Success!"}
                }
            },
        },
    },    
)
def get_gNB_details():
    #dictionaries for json
    gNB_Data={
    "gnb_list":[],
    }
    client=docker.from_env()  
    gnb_List = display_gNBDetails(client)
    if gnb_List==[]:
        raise HTTPException(status_code=404, detail="There is no network deployed. Try deploying a network first.")                                   
    gNB_Data["gnb_list"]=gnb_List
    return gNB_Data


###########################################################################
@app.get(
    '/ue_details/', 
    tags=["Get UE details"],
    responses={
        404: {
            "description": "The requested resource was not found",
            "content": {
                "application/json": {
                    "example": {"response":"The requested resource was not found. Please check if network is deployed!"}
                }
            },
        },    
        200: {
            "description": "Successful response.",
            "content": {
                "application/json": {
                    "example": {"response":"Success!"}
                }
            },
        },
    },    
)
def get_UE_details():
    #dictionaries for json
    UE_Data={
    "ue_list":[],
    }
    client=docker.from_env()
    UE_List = display_UEDetails(client)
    if UE_List==[]:
        raise HTTPException(status_code=404, detail="There is no network deployed. Try deploying a network first.")
    UE_Data["ue_list"]=UE_List
    return UE_Data


###########################################################################

@app.get(
    '/get_NetworkSummary/', 
    tags=["Get Network Summary"],
    responses={
        404: {
            "description": "The requested resource was not found",
            "content": {
                "application/json": {
                    "example": {"response":"The requested resource was not found. There is no container running with the given id."}
                }
            },
        },    
        200: {
            "description": "Successful response.",
            "content": {
                "application/json": {
                    "example": {"response":"Success!"}
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {"response":"Invalid parameters! Please use valid parameters."}
                }
            },
        },               
    },    
)

def get_NetworkSummary():
    #dictionaries for json
    Net_Sum={"Number of Cells Available":3000,
    "Number of Cells Active":2400,
    "Percentage Utilization": '80%',
    }
    state= 'active'
    
    return Net_Sum


###########################################################################

@app.get(
    '/get_NetworkStats/', 
    tags=["Get Network Statistics"],
    responses={
        404: {
            "description": "The requested resource was not found",
            "content": {
                "application/json": {
                    "example": {"response":"The requested resource was not found. There is no container running with the given id."}
                }
            },
        },    
        200: {
            "description": "Successful response.",
            "content": {
                "application/json": {
                    "example": {"response":"Success!"}
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {"response":"Invalid parameters! Please use valid parameters."}
                }
            },
        },               
    },    
)


#@app.route('/monitor_nf_stats/<id>')
#def monitor_nf_stats(id):
def get_NetworkStats(id):
    Net_Stat={"Successful Connects":'80%',
    "Throughput":[],
    "Latency":'10ms',
    "Packet Loss":'13%',
    "Mobility":'80%',
    }
    state= 'active'
    #sucess = 'ok goli'
    str2 = 'iperf -u -i 1 -fk -B 12.1.1.2 -b 200M -c 192.168.72.135 -t 15 | awk -Wi -F\'[ -]+\' \'/sec/{print $3"-"$4" "$8}\''
    client=docker.from_env()
    container = client.containers.get(id)
    run=container.exec_run(['sh', '-c', str2])
    temp1=(run.decode("utf-8"))
    print(temp1)
    temp2 = json.dumps(temp1)
    out1 = [int(s) for s in temp1.split() if s.isdigit() and int(s)>100]
    out2 =sum(out1)/(len(out1)*1000)
    print(out2)
    #IPaddr = measurements.get_IPaddressOfUE(client,id)
    #print(IPaddr) 
    
    
    #meas=measurements.get_measurements(client)
    ##print(meas)
    #meas1 = measurements.read()
    """     ul_dict={}
        dl_dict={}
        lat_dict={}
        for row in meas:
            if row[3] not in ul_dict.keys():
                ul_dict[row[3]]=[row[4]]
                dl_dict[row[3]]=[row[5]]
                lat_dict[row[3]]=[row[6]]
            else:
                ul_dict[row[3]].append(row[4])
                dl_dict[row[3]].append(row[5])
                lat_dict[row[3]].append(row[6])
        for key in ul_dict.keys():
            chart1_dict["data"].append({key:((sum(ul_dict[key])/len(ul_dict[key]))/100000)})
            chart2_dict["data"].append({key:((sum(dl_dict[key])/len(dl_dict[key]))/100000)})
            chart3_dict["data"].append({key:((sum(lat_dict[key])/len(lat_dict[key]))/100000)})
    monitor_nf["NF_stats"]={"chart1":chart1_dict,"chart2":chart2_dict,"chart3":chart3_dict}
     """
    Net_Stat["Throughput"] = "{:.2f}".format(out2) + 'Mbps'
    #return jsonify(monitor_nf),200
    return Net_Stat


""" def get_NetworkStats():
    #dictionaries for json
    Net_Stat={"Successful Connects":'80%',
    "Throughput":'8.1 Gbps',
    "Latency":'10ms',
    "Packet Loss":'13%',
    "Mobility":'80%',
    }
    state= 'active'

    
    return Net_Stat
 """
################################################################################################################################################################
#                                                                 Inspect Screen APIs                                                                          #
################################################################################################################################################################
@app.get(
    "/Inspect_Details/", 
    tags=["Get Network Inspect Details"],
    responses={
        404: {
            "description": "The requested resource was not found",
            "content": {
                "application/json": {
                    "example": {"response":"The requested resource was not found. Please check if network is deployed!"}
                }
            },
        },    
        200: {
            "description": "Successful response.",
            "content": {
                "application/json": {
                    "example": {"response":"Success!"}
                }
            },
        },
    },
)
def get_Inspect_details():
    #dictionaries for json
    Inspect_List={"Inspect_List":[],
    "CID":[],
    "no_containers":0,
    }
    #state= 'active'
    client=docker.from_env()
    Inspect = [] #client.containers.list()#[]
    Cid = []    
    Count=0
    print(client.containers.list())
    for container in client.containers.list():
        print(container.name)
        if 'mysql' in container.name:
            continue
        elif 'webui' in container.name:
            continue
        elif 'ext-dn' in container.name:
            continue
        else:
            Inspect.append(container.name[12:])
            Cid.append(container.id)
            Count = Count+1        
    if Inspect==[]:
        raise HTTPException(status_code=404, detail="There is no network deployed. Try deploying a network first.")                     
    Inspect_List["Inspect_List"]=Inspect
    Inspect_List["CID"]=Cid
    Inspect_List["no_containers"]=Count
    return (Inspect_List)

######################################################################################################################################################
@app.get(
    '/get_logs/<id>', 
    tags=["Get Logs"],
    responses={
        404: {
            "description": "The requested resource was not found",
            "content": {
                "application/json": {
                    "example": {"response":"The requested resource was not found. There is no container running with the given id."}
                }
            },
        },    
        200: {
            "description": "Successful response.",
            "content": {
                "application/json": {
                    "example": {"response":"Success!"}
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {"response":"Invalid parameters! Please use valid parameters."}
                }
            },
        },               
    },    
)
def get_Logs(id):
    #dictionaries for json    
    Logs={ "nf_logs":''
   }
    client=docker.from_env()
    container=client.containers.list(filters={"id":id})
    if len(container)==0:
        print ("no container running with given id")
        raise HTTPException(status_code=404, detail="There is no container running with the given id.")
        return   
    Logs["nf_logs"]=get_logs(client,id)
    return Logs
######################################################################################################################################################

@app.get(
    '/get_console/<id>', 
    tags=["Get Console"],
    responses={
        404: {
            "description": "The requested resource was not found",
            "content": {
                "application/json": {
                    "example": {"response":"The requested resource was not found. There is no container running with the given id."}
                }
            },
        },    
        200: {
            "description": "Successful response.",
            "content": {
                "application/json": {
                    "example": {"response":"Success!"}
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {"response":"Invalid parameters! Please use valid parameters."}
                }
            },
        },               
    },    
)
def get_Console(id):
    #dictionaries for json    
    Console={ "nf_console":''
   }
    client=docker.from_env()
    container=client.containers.list(filters={"id":id})
    if len(container)==0:
        print ("no container running with given id")
        raise HTTPException(status_code=404, detail="There is no container running with the given id.")
        return   
    Console["nf_console"]=get_console(client,id)
    return Console


######################################################################################################################################################
@app.get(
    '/get_packets/<id>', 
    tags=["Get Packets"],
    responses={
        404: {
            "description": "The requested resource was not found",
            "content": {
                "application/json": {
                    "example": {"response":"The requested resource was not found. There is no container running with the given id."}
                }
            },
        },    
        200: {
            "description": "Successful response.",
            "content": {
                "application/json": {
                    "example": {"response":"Success!"}
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {"response":"Invalid parameters! Please use valid parameters."}
                }
            },
        },               
    },    
)
#@app.route('/monitor_nf_packets/<id>')
def get_packets(id):
    #dictionaries for json
    monitor_nf={"NF_packets":''}
    client=docker.from_env()
    container=client.containers.list(filters={"id":id})
    monitor_nf["NF_packets"]=packets.get_packets(container[0].name)
    return jsonify(monitor_nf)
######################################################################################################################################################
@app.get(
    '/get_NetworkAttentions/', 
    tags=["Get Network Issues and Resolving Actions"],
    responses={
        404: {
            "description": "The requested resource was not found",
            "content": {
                "application/json": {
                    "example": {"response":"The requested resource was not found. There is no container running with the given id."}
                }
            },
        },    
        200: {
            "description": "Successful response.",
            "content": {
                "application/json": {
                    "example": {"response":"Success!"}
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {"response":"Invalid parameters! Please use valid parameters."}
                }
            },
        },               
    },    
)
def get_NetworkAttentions():
    #dictionaries for json
    NetworkAttentions = []
    Tag = "CN"
    Message = 'SMF is unhealthy'
    Site = "Irvine,CA"
    Switch = "9a9bea"
    Port = "3000"
    ID = "CN12"
    NetworkAttentions.append(get_network_attention(Tag,Message,Site,Switch,Port,ID))

    Tag = "AP"
    Message = 'AP2025 has refused connection issue'
    Site = "Peru,LA"
    Switch = "10ab612"
    Port = "9001"
    ID = "AP025"
    NetworkAttentions.append(get_network_attention(Tag,Message,Site,Switch,Port,ID))
    
    Tag = "Resolved Action"
    ID = "Device23"
    Message = "Battery Replaced"
    Site = "Irvine,CA"
    NetworkAttentions.append(get_resolved_action(Tag,ID,Message,Site))
    
    
    Tag = "Resolved Action"
    ID = "CN12"
    Message = "AMF Redeployed"
    Site = "Sweden,EU"
    NetworkAttentions.append(get_resolved_action(Tag,ID,Message,Site))
    

    Tag = "CN"
    Message = 'AMF is unhealthy'
    Site = "Hyderabad,IND"
    Switch = "9a9bcd"
    Port = "3000"
    ID = "CN5"
    NetworkAttentions.append(get_network_attention(Tag,Message,Site,Switch,Port,ID))

    Tag = "Device"
    Message = 'Needed Battery Replacement'
    Site = "Irvine,CA"
    Switch = "9a9bea"
    Port = "3000"
    ID = "Device23"
    NetworkAttentions.append(get_network_attention(Tag,Message,Site,Switch,Port,ID))

    return NetworkAttentions

######################################################################################################################################################
@app.get(
    '/get_traffic/', 
    tags=["Get UL/DL Traffic"],
    responses={
        404: {
            "description": "The requested resource was not found",
            "content": {
                "application/json": {
                    "example": {"response":"The requested resource was not found. There is no container running with the given id."}
                }
            },
        },    
        200: {
            "description": "Successful response.",
            "content": {
                "application/json": {
                    "example": {"response":"Success!"}
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {"response":"Invalid parameters! Please use valid parameters."}
                }
            },
        },               
    },    
)
#@app.route('/monitor_nf_packets/<id>')
def get_traffic():
    #dictionaries for json
    monitor_traffic={"UL":'',"DL":''}
#    client=docker.from_env()
 #   container=client.containers.list(filters={"id":id})
    monitor_traffic["UL"]=90.25
    monitor_traffic["DL"]=270.75
    
    return monitor_traffic


######################################################################################################################################################



#uvicorn.run(app)
#uvicorn.run(app, host = "0.0.0.0", port = 3001, log_level = "debug", debug = True)

#docker_deploy('OAI','OAI')
#client=docker.from_env()
#id="d477c3f6c800"
#container=client.containers.list(filters={"id":id})
#container[0].exec_run(['sh', '-c', 'echo $GNB_HOSTNAME'])
#ues_served(client)