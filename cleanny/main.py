import schedule
import time
import datetime as dt
import django
import os
import gspread
os.environ['DJANGO_SETTINGS_MODULE'] = 'cleanny.settings'
django.setup()
import base.models as db

# print(db.Equip.objects.all())
# gs auth
gs = gspread.service_account('gspred_creds.json')
sh = gs.open('Cleanny Goddeses').worksheet('График')


def gs_sched_sync():
    employees = {}
    for e in db.Employee.objects.all():
        employees[e.id] = {'name': e.name,
                           'dob': str(e.dob.strftime('%d.%m.%Y'))}
    print(employees)
    sh.clear()
    sh.append_row(['Дата', 'Время']+[employees[e]["name"] + ' ' + employees[e]["dob"] for e in employees])
    time.sleep(5)
    today = dt.date.today()
    for i in range(7):
        day = today + dt.timedelta(days=i) # datetime_start
        sh.update_cell(i+2+i*23, 1, day.strftime('%d.%m.%Y'))
        t = dt.datetime(day.year, day.month, day.day, hour=9)
        table = []
        day_orders = db.Order.objects.filter(datetime_start__date=day, is_aborted=False)
        while t <= dt.datetime(day.year, day.month, day.day, hour=18):
            table.append([str(t.time())]+['' for _ in employees.keys()])
            t += dt.timedelta(minutes=30)
        for order in day_orders:
            el = db.Employees_list.objects.filter(order_id=order.id)
            for e_l in el:
                for row_num in range(order.datetime_start.hour * 2 - 18 + bool(order.datetime_start.minute),
                                     order.datetime_end.hour * 2 - 18 + bool(order.datetime_end.minute)+1):
                    table[row_num][e_l.employee_id.id] = order.client_id.adress
                    table[row_num][e_l.employee_id.id] = order.client_id.adress
        sh.append_rows(table, table_range='b'+str(i+2+i*23))



input()
# schedule tasks
schedule.every(5).seconds.do(gs_sched_sync)
while True:
    schedule.run_pending()
