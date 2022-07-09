from ipaddress import ip_address
import docker
import json
import sqlite3
def get_db():
    conn=sqlite3.connect('db_for_flask.db',isolation_level=None)
    return conn

def make_index_table():
    conn = get_db()
    cursor=conn.cursor()
    """Clear existing data and create new table for index_ip_addresses"""
    sql = "DROP TABLE IF EXISTS ip_index"
    cursor.execute(sql)
    sql="CREATE TABLE ip_index (c_id TEXT NOT NULL, c_name TEXT NOT NULL, c_ip TEXT NOT NULL)"
    cursor.execute(sql)
    return cursor
    
def if_table_exists(cursor,table_name):
    sql="SELECT name FROM sqlite_master WHERE type='table' AND name='"+table_name+"'; "
    listOfTables = cursor.execute(sql).fetchall()
    if listOfTables == []:
        return False
    else:
        return True

def get_name_and_id_from_ip(ip):
    conn=get_db()
    cursor=conn.cursor()
    sql="SELECT c_name,c_id FROM ip_index WHERE c_ip='"+ip+"'; "
    if if_table_exists(cursor,'ip_index'):
        cursor.execute(sql)
        args=cursor.fetchall()
    else:
        args=0
        print("No data exists in database table ipindex")
    cursor.close()
    conn.close()
    return args

def write_ip_index_table(client):
    conn=get_db()
    cursor=conn.cursor()
    make_index_table()

    for container in client.containers.list():
        ip_address=client.api.inspect_container(container.id)['NetworkSettings']['Networks']['rfsim5g-oai-public-net']['IPAddress']
        print(ip_address)
        if ip_address!= "":
            try:
                cursor.execute("INSERT INTO ip_index (c_name,c_id,c_ip) VALUES ( ?, ?, ?)", (container.name, container.id, ip_address) )
            except :
                print ("ip_index insert not executing")
    return
