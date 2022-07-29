from datetime import datetime, timedelta


now = datetime.now()
now_plus_10 = now + timedelta(minutes = 10)

print(now < now_plus_10)