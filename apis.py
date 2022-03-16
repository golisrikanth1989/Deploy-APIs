#import docker
#from flask import Flask, request, jsonify
import sys, os

#app= Flask(__name__)
#client=docker.from_env()
#stop=0

#@app.route('/deploy_Scenario/<CN>/<RAN>')
def docker_deploy(CN,RAN):
    # select scenario of CN and RAN and then deploy the scenario
    if CN == 'free5gc' and RAN == 'UERANSIM':
        print("free5gc and UERANSIM")
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
        pwd=os.getcwd()
        print(pwd)
        #return "success",200
    elif CN == 'free5gc' and RAN == 'OAI':
        print("free5gc and OAI RAN")
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
 


#start flask app
#if __name__=='__main__':
#    app.run(host = '0.0.0.0',port=sys.argv[1])

docker_deploy('free5gc','OAI')