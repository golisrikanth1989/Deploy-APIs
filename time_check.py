from datetime import datetime
dt_utcnow = datetime.utcnow()
print(dt_utcnow.date())

# current dateTime
#now = datetime.now()

# convert to string
date_time_str = dt_utcnow.strftime("%Y/%m/%d %H:%M:%S.%f")

print(type(date_time_str))
print(date_time_str)

time_now = '2023/03/29 12:14:37'

date_time_obj = datetime.strptime(time_now, '%Y/%m/%d %H:%M:%S')
#date_time_str1 = time_now.strftime("%d-%m-%y %H:%M:%S")
print(date_time_obj)