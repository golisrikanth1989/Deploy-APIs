import docker
from flask import Flask, request, jsonify
import sys, os

app= Flask(__name__)
client=docker.from_env()
stop=0

#@app.route('/deploy_Scenario/<CN>/<RAN>'')
def docker_deploy(CN,RAN):
    # select scenario of CN and RAN and then deploy the scenario
    if (CN=="free5gc") and (RAN=="UERANSIM")
        print("free5gc and UERANSIM")
        pwd=os.getcwd()
        print(pwd)
        #os.chdir('../free5gc-compose')
        #os.system('docker-compose up -d')
        #os.chdir(pwd)
        #return "success",200
    else
        print("No input")



#start flask app
#if __name__=='__main__':
#    app.run(host = '0.0.0.0',port=sys.argv[1])

docker_deploy(free5gc,UERANSIM)