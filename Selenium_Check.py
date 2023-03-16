from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
import time

from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

#service_obj = Service(executable_path="/home/dolcera/Deploy-APIs/chromedriver_linux64/chromedriver.exe")
driver = webdriver.Chrome(executable_path="/home/dolcera/5Fi_APIs/Deploy-APIs/chromedriver_linux64/chromedriver",chrome_options=chrome_options) #service=service_obj)
driver.maximize_window()
driver.get("https://panel.rapid.space/hateoas/connection/login_form?came_from=https%3A%2F%2Fpanel.rapid.space%2F%23%21login%3Fp.page%3Dslap_service_list%26p.editable%3Dtrue%7B%26n.me%7D")

############## LOGIN ########################################

# usname = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div/article/section[3]/form/div/div/div[1]/div/input")))
# usname.send_keys("manoj1919")
# time.sleep((2))
# pwd = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div/article/section[3]/form/div/div/div[2]/div/input")))
# pwd.send_keys("Dolcera@123")
# time.sleep(2)
# driver.find_element(By.XPATH, "/html/body/div[3]/div/article/section[3]/form/div/div/div[3]/input").click()
# time.sleep(5)


# element = driver.find_elements(By.CLASS_NAME, 'foo')
# driver.find_element(By.XPATH, "/html/body/div/div[9]/div/div/form/div[2]/div/div/div/div/div/div/table/tbody/tr[5]/td[1]").click()
# time.sleep(5)

#driver.find_element_by_name("__ac_name").send_keys("manoj1919")
#driver.find_element_by_name("__ac_password").send_keys("Dolcera@123")
#driver.find_element_by_name("WebSite_login:method").click()
#time.sleep(20)

#l = driver.find_elements_by_xpath ("//*[@class= 'thead']/tbody/tr")
# to get the row count len method
#print (len(l)) 
#print("Goli")
#driver.find_element(By.XPATH,"/html/body/div[1]/div[9]/div/div/form/div[2]/div/div/div/div/div/div/table/tbody/tr[8]/td[1]/a").click()
#time.sleep(20)

#driver.find_element(By.XPATH,'//input[@name="//tx_gain"]').clear()
#driver.find_element(By.XPATH,'//input[@name="//tx_gain"]').send_keys("78")



#table_body = WebDriverWait(driver,20).until(EC.presence_of_all_elements_located((By.XPATH, "/html/body/div/div[9]/div/div/form/div[2]/div/div/div/div/div/div/table/tbody/tr")))

# for i in table_body:
#     time.sleep(10)
#     data1= i.find_element(By.XPATH,"/html/body/div/div[9]/div/div/form/div[2]/div/div/div/div/div/div/table/tbody/tr[1]/td[3]/a/div/div/div/div/div[1]/div/a").text
#     print(data1)
#     data2= i.find_element(By.XPATH,"/html/body/div/div[9]/div/div/form/div[2]/div/div/div/div/div/div/table/tbody/tr[2]/td[3]/a/div/div/div/div/div[1]/div/a").text
#     print(data2)
#     data3= i.find_element(By.XPATH,"/html/body/div/div[9]/div/div/form/div[2]/div/div/div/div/div/div/table/tbody/tr[3]/td[3]/a/div/div/div/div/div[1]/div").get_attribute("class")
#     print(data3)
#     data4= i.find_element(By.XPATH,"/html/body/div/div[9]/div/div/form/div[2]/div/div/div/div/div/div/table/tbody/tr[4]/td[3]/a/div/div/div/div/div[1]/div/a").text
#     print(data4)
#     data5= i.find_element(By.XPATH,"/html/body/div/div[9]/div/div/form/div[2]/div/div/div/div/div/div/table/tbody/tr[5]/td[3]/a/div/div/div/div/div[1]/div").get_attribute("class")
#     print(data5)
#     time.sleep(5)
#     assert data5 == "ui-bar ui-corner-all first-child ui-btn-ok"
#     link_ors = driver.find_element(By.XPATH, "/html/body/div/div[9]/div/div/form/div[2]/div/div/div/div/div/div/table/tbody/tr[5]/td[1]/a")
#     link_ors.click()

#     time.sleep(10)

#     link_gnb = driver.find_element(By.XPATH, "/html/body/div/div[9]/div/div/form/div/div/div[4]/div[4]/div/div/div/table/tbody/tr[1]/td[1]/a")
#     driver.execute_script("arguments[0].scrollIntoView();", link_gnb)
#     link_gnb.click()
#     time.sleep(10)

#     break
fname = 'ORS_status_US.txt'
with open(fname) as file:
    # loop to read iterate
    # last n lines and print it
    for line in (file.readlines() [-1:]):
        if 'ok' in line:
            print('5Fi-78')
        print(line, end ='')

driver = webdriver.Chrome(executable_path="/home/dolcera/5Fi_APIs/Deploy-APIs/chromedriver_linux64/chromedriver",chrome_options=chrome_options) #service=service_obj)
driver.maximize_window()
driver.get("http://admin:LyZHtPLJ3Qo0TFlA@softinst178418.host.vifib.net/share/private/")


############## LOGIN ########################################

# usname = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div/article/section[3]/form/div/div/div[1]/div/input")))
# usname.send_keys("manoj1919")
# time.sleep((2))
# pwd = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div/article/section[3]/form/div/div/div[2]/div/input")))
# pwd.send_keys("Dolcera@123")
# time.sleep(2)
