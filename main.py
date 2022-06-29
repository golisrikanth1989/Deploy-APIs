import docker
from fastapi import FastAPI, HTTPException, Form, Path, Query
from enum import Enum
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
    {"name" : "Samsung", "status" : False},
    {"name" : "Nokia", "status" : False}
]


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
    Nokia = "Nokia"

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
        "name": "Get logs",
        "description": "Get logs of the container with containerid mentioned.",
    }, 
    {
        "name": "Get Network Statistics",
        "description": "Get Successfull Connections of the Containers using Health Status.",
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

#def Choose_CN(CN: CN_options):
#    return {"Selected the Core Network"}
def get_cn_List()-> dict:
    return {"CN_List": CN_List}

###############################################################

@app.get('/RAN_list', tags = ["Get Access Points List"],status_code=200)

#def Choose_CN(CN: CN_options):
#    return {"Selected the Core Network"}
def get_ran_List()-> dict:
    return {"RAN_List": RAN_List}
###############################################################

@app.get('/UE_list', tags = ["Get Devices List"],status_code=200)

#def Choose_CN(CN: CN_options):
#    return {"Selected the Core Network"}
def get_ue_List()-> dict:
    return {"UE_List": UE_List}
#############################################################################################################

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

def deploy_Scenario(CN_Make: CN_options,CN_Quantity,RAN_Make: RAN_options,RAN_Quantity):
    if CN_Make == 'OAI' and RAN_Make == 'OAI':
        print("Selected OAI CN and RAN Make")
        os.chdir('../')
        os.chdir('openairinterface5g')
        os.system('git checkout develop')
#        os.system('git pull')
        os.chdir('ci-scripts/yaml_files/5g_rfsimulator')
        os.system('docker ps -aq | xargs docker rm -f')
        time.sleep(30)
        for i in range(int(CN_Quantity)):
            cn_str = "cn" + str(i+1)
            cmd = 'docker-compose -f docker-compose-manual.yaml up -d  mysql oai-nrf oai-amf oai-smf oai-spgwu oai-ext-dn'
            os.system(cmd)
            time.sleep(10)

            cmd = 'docker-compose -f docker-compose-manual.yaml up -d oai-gnb1'
            print(cmd)
            os.system(cmd)
            time.sleep(10)

            cmd = 'docker-compose -f docker-compose-manual.yaml up -d oai-gnb2'
            print(cmd)
            os.system(cmd)
            time.sleep(10)
            
            # For First gNB
            cmd = 'docker-compose -f docker-compose-manual.yaml up -d oai-nr-ue1' 
            print(cmd)
            os.system(cmd)
            time.sleep(10)

            cmd = 'docker-compose -f docker-compose-manual.yaml up -d oai-nr-ue2' 
            print(cmd)
            os.system(cmd)
            time.sleep(10)
            
            # For Second gNB  
            cmd = 'docker-compose -f docker-compose-manual.yaml up -d oai-nr-ue3' 
            print(cmd)
            os.system(cmd)
            time.sleep(10)
            
            cmd = 'docker-compose -f docker-compose-manual.yaml up -d oai-nr-ue4' 
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

        
###############################################################
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
    RAN_Data={"make_of_ran":'',
    "no_ues":0,
    "no_gnbs":0,
    "gnb_list":[],
    "ue_list":[],
    }
    state= 'active'
    client=docker.from_env()
    RAN=''
    for container in client.containers.list():
        if 'gnb' in container.name:
            if 'oai' in container.name:
                RAN = 'OAI'
            else:
                RAN = 'UERANSIM'  
    if RAN=='':
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
    '/get_logs/<id>', 
    tags=["Get logs"],
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
def get_NetworkStats():
    #dictionaries for json
    Net_Stat={"Sucessful Connects":'80%',
    "Throughput":'8.1 Gbps',
    "Latency":'10ms',
    "Packet Loss":'13%',
    "Mobility":'80%',
    }
    state= 'active'
    
    return Net_Stat



#uvicorn.run(app)
#uvicorn.run(app, host = "0.0.0.0", port = 3001, log_level = "debug", debug = True)

#docker_deploy('OAI','OAI')
#client=docker.from_env()
#id="d477c3f6c800"
#container=client.containers.list(filters={"id":id})
#container[0].exec_run(['sh', '-c', 'echo $GNB_HOSTNAME'])
#ues_served(client)