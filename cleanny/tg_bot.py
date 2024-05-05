import sys
import json
import telebot
import datetime
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

# Django models import
import django
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'cleanny.settings'
django.setup()
import base.models as db
# from base.models import Employee

# print(os.getcwd())
# Example of db requestS
# print([(i.name, i.id) for i in db.Service.objects.all()])
# input()

# getting token from json.

config_path = '\\'.join(os.path.abspath(__file__).split('\\')[:-1])+'\\config.json'
with open(config_path) as file:
    data = json.load(file)

TOKEN = data['tg_token']

bot = telebot.TeleBot(TOKEN)

sessions = {'cleaners':{},
            'clients': {}
            }

cleaners_chat = data['tg_channel_id']

cash = {'to_delete': [],
        'to_edit': []}

card_template = ["Заказ №", "\n", "\nСтоимость заказа: ", "\nАдрес: ", "\nДата: ", "\nТелефон: ", "\nОборудование: "]

services_list = db.Service.objects.values_list()

# close kboard
keyb_close = InlineKeyboardMarkup()
keyb_close.add(InlineKeyboardButton("Закрыть", callback_data='close;'))

# start keyboard
keyb_start = InlineKeyboardMarkup()
keyb_start.add(InlineKeyboardButton("Мое расписание", callback_data='sched;'))

# main keyboard
start_menu_keyb = InlineKeyboardMarkup()
start_menu_keyb.add(InlineKeyboardButton('Заказать клининг', callback_data='c;cleaning'))
start_menu_keyb.add(InlineKeyboardButton('Наш сайт', url='https://cleanny.by/'))

def get_time_table(day):
    employees = {}
    for e in db.Employee.objects.all():
        employees[e.id] = {'name': e.name,
                           'dob': str(e.dob.strftime('%d.%m.%Y'))}
    employees = [employees[e]['name'] for e in employees.keys()]
    print(employees)
    t = datetime.datetime(day.year, day.month, day.day, hour=9)
    table = []
    day_orders = db.Order.objects.filter(datetime_start__date=day, is_aborted=False)
    while t <= datetime.datetime(day.year, day.month, day.day, hour=18):
        table.append([str(t.time())] + ['' for _ in employees])
        t += datetime.timedelta(minutes=30)
    for order in day_orders:
        el = db.Employees_list.objects.filter(order_id=order.id)
        for e_l in el:
            for row_num in range(order.datetime_start.hour * 2 - 18 + bool(order.datetime_start.minute),
                                 order.datetime_end.hour * 2 - 18 + bool(order.datetime_end.minute) + 1):
                table[row_num][e_l.employee_id.id] = order.client_id.adress
                table[row_num][e_l.employee_id.id] = order.client_id.adress
    for i in table:
        print(i)

    return table, employees

def time_available(pool, duration):
    rows = len(pool[0])
    cols = len(pool[0][0])
    
    check_index = duration/datetime.timedelta(minutes=30) + 1
    
    time_dict = {}
    for i in range(len(pool[1])):
        time_dict[i+1] = []
    
    for c in range(1, cols):
        for r in range(rows):
            count = 0
            for i in range(0, int(check_index)):
                if r+i <= rows-1:
                    if pool[0][r+i][c] == '':
                        count += 1
                    else:
                        break 
                else:
                    count = check_index
                    break

            if count == check_index:        
                time_dict[c].append(pool[0][r][0])  
        print(time_dict[c])            

    return time_dict

def gen_ketb_time(dicty):
    keyb = InlineKeyboardMarkup(row_width=4)
    last_time = '09:00:00'
    template = []
    unique_time = set()

    for d in dicty:
        unique_time.update(dicty[d])
    
    unique_time = sorted(list(unique_time))

    # unique_time = ['09:00:00', '09:30:00', '10:00:00', '10:30:00', '11:00:00', '11:30:00', '12:00:00', '12:30:00',  '14:00:00', '14:30:00', '15:00:00', '15:30:00', '16:00:00', '16:30:00', '17:00:00', '17:30:00', '18:00:00']

    for time in unique_time:
        while last_time != time:
            template.append('-')
            last_time = (datetime.datetime.strptime(last_time, '%H:%M:%S') + datetime.timedelta(minutes=30)).strftime('%H:%M:%S')
        template.append(time)
        last_time = (datetime.datetime.strptime(last_time, '%H:%M:%S') + datetime.timedelta(minutes=30)).strftime('%H:%M:%S')


    for i in range(0, len(template), 4):
        buttons = [InlineKeyboardButton(text=":".join(time.split(":")[:2]), 
                                        callback_data=f'c;time;{":".join(time.split(":")[:2])}') for time in template[i:i+4]]
        keyb.add(*buttons)
    return keyb


def sim_parse(call):  # chat_id, message_id, data = sim_parse(call)
    return call.message.chat.id, call.message.id, call.data


def adv_parse(call):  # chat_id, message_id, data, text, keyb = adv_parse(call)
    return call.message.chat.id, call.message.id, call.data, call.message.text, call.message.reply_markup


def gen_client_order_num_list(chat_id):
    sessions['clients'][chat_id]['order_list'] = [i[4] for i in services_list]
    sessions['clients'][chat_id]['tel'] = 0
    sessions['clients'][chat_id]['location'] = ''
    sessions['clients'][chat_id]['date_on'] = False


def gen_text_for_order(chat_id, time_send_on=False, price=False):
    text = ''
    summ = 0.0
    time = 0
    for num, item in enumerate(sessions['clients'][chat_id]['order_list']):
        if item:
            if not num:
                summ += services_list[num][2] * item
                time += (services_list[num][3].hour * 60 + services_list[num][3].minute) * item
            elif num == 1:
                summ += services_list[num][2] * item
                time += (services_list[num][3].hour * 60 + services_list[num][3].minute) * item
                text += f'Уборка квартиры с {item} жилыми'
            elif num == 2:
                summ += services_list[num][2] * item
                time += (services_list[num][3].hour * 60 + services_list[num][3].minute) * item
                text += f' и {item} ванной комнатами\n'
            else:
                summ += services_list[num][2] * item
                time += (services_list[num][3].hour * 60 + services_list[num][3].minute) * item
                text += f'Доп услуга - {services_list[num][1]} X{item}\n'
    time = time/60
    text += f'Время уборки: {time} часа\n'
    text += f'К оплате: {summ} рублей\n'
    if 'date' in sessions['clients'][chat_id]:
        if sessions['clients'][chat_id]['date_on']:
            text += f"Дата уборки: {sessions['clients'][chat_id]['date'].strftime('%d-%m-%Y %H:%M')}\n"
    if sessions['clients'][chat_id]['tel']:
        text += f"Ваш телефон: {sessions['clients'][chat_id]['tel']}\n"
    if sessions['clients'][chat_id]['location']:
        text += f"Ваш адресс: {sessions['clients'][chat_id]['location']}\n"
    if price:
        return summ
    if time_send_on:
        return text, time
    return text


def change_number_for_oder(chat_id, index, num):
    result = sessions['clients'][chat_id]['order_list'][index] + num
    if services_list[index][4] <= result <= services_list[index][5]:
        sessions['clients'][chat_id]['order_list'][index] = result


def gen_pre_final_keyb():
    keyb = InlineKeyboardMarkup()
    keyb.add(InlineKeyboardButton("Отправить заказ", callback_data='c;final'))
    keyb.add(InlineKeyboardButton("Поменять телефон", callback_data='c;phone'),
             InlineKeyboardButton("Поменять адресс", callback_data='c;adress'))
    keyb.add(InlineKeyboardButton("Поменять дату", callback_data='c;calendar'))
    keyb.add(InlineKeyboardButton("Меню", callback_data='c;main_menu'))
    return keyb


"""
    sessions['clients'][chat_id]['order_list'] = [i[4] for i in services_list]
    sessions['clients'][chat_id]['tel'] = 0
    sessions['clients'][chat_id]['location'] = ''
    sessions['clients'][chat_id]['total_price'] = total_price
    sessions['clients'][chat_id]['cleaning_time']
    sessions['clients'][chat_id]['date_on'] = False
"""


def filling_db_for_user_oder(chat_id):
    client = db.Client.objects.get(chat_id=chat_id)
    # datetime_start and datetime_end should be proper, datetime.datetime.now() for now

    time = gen_text_for_order(chat_id, time_send_on=True)[1]
    time = datetime.timedelta(hours=int(time), minutes=30*(time % 1 != 0))

    order = db.Order(client_id=client, is_finished=False, is_aborted=False,
             total_price=sessions['clients'][chat_id]['total_price'], datetime_start=sessions['clients'][chat_id]['date'],
             datetime_end=sessions['clients'][chat_id]['date'] + time)
    
    order.save()

    for num, item in enumerate(sessions['clients'][chat_id]['order_list']):
        if item:
            service = db.Service.objects.get(name=services_list[num][1])
            service_list_fill = db.Services_list(order_id=order, service_id=service, amount=item).save()

    return order
    

def gen_order_keyb(chat_id, num, fix_poz=5):
    list_ = services_list[1:]
    nums_list = sessions['clients'][chat_id]['order_list'][1:]
    keyb = InlineKeyboardMarkup()
    if len(list_) % 5 == 1:
        fix_poz = 4
    if ((num + 1) * fix_poz) < len(list_):
        end_ = ((num + 1) * fix_poz)
    else:
        end_ = len(list_)
    for x in range(num * fix_poz, end_):
        keyb.add(InlineKeyboardButton(f'{list_[x][1]}: {nums_list[x]}', callback_data=f'{x}'))
        keyb.add(InlineKeyboardButton("-", callback_data=f'с;ord;del;{str(x+1)};{str(num)}'),
                 InlineKeyboardButton("+", callback_data=f'с;ord;add;{str(x+1)};{str(num)}'))
    if num == 0 and end_ != len(list_):
        keyb.add(InlineKeyboardButton("Вперед", callback_data=f'с;ord;m;{str(num + 1)}'))
    elif num != 0 and end_ == len(list_):
        keyb.add(InlineKeyboardButton("Назад", callback_data=f'с;ord;m;{str(num - 1)}'))
    elif num != 0:
        keyb.add(InlineKeyboardButton("Назад", callback_data=f'с;ord;m;{str(num - 1)}'),
                 InlineKeyboardButton("Вперед", callback_data=f'с;ord;m;{str(num + 1)}'))
    keyb.add(InlineKeyboardButton("Меню", callback_data='c;main_menu'),
             InlineKeyboardButton("Оформить", callback_data='c;calendar'))

    return keyb


def gen_order_card(orders=None, chat_id=None):
    if chat_id is not None:
        employee_id = db.Employee.objects.get(tg_id=chat_id)
        brige = db.Employees_list.objects.filter(employee_id=employee_id.id, order_id__is_finished=False, order_id__is_aborted=False)
        order_list = [i.order_id for i in brige]
    else:
        order_list = orders

    orders_temp = []
    for i in order_list:
        services_list = [j.service_id for j in db.Services_list.objects.filter(order_id=i.id)]
        services_temp = ''
        if not services_list:
            services_temp = 'Базовая цена'
        else:
            for s in services_list:
                services_temp += s.name + ' '
        
        client = db.Client.objects.get(id=i.client_id.id)
        # Сделать проверку на вермя чтобы отправлялись только заказы на сегодня и завтра
        date = i.datetime_start.strftime("%d-%m-%Y %H:%M")

        equip = '\n'
        for s in services_list:
            equip_qs = db.Service_req.objects.filter(service_id=s.id)
            for item in equip_qs:
                equip += item.equip_id.name + ' x ' + str(item.amount) + '\n'
            # equip = db.Service_req.objects.filter(service_id=s.id).values_list().equip_id.name + ' '

        card_info = [str(i.id), services_temp, str(i.total_price), client.adress, date, str(client.tel), equip]
        orders_temp.append(card_info)
    return orders_temp

def gen_text(template):
    mes = ''
    for t in range(len(card_template)):
        mes += card_template[t] + template[t]

    return mes

def gen_keyb_order(order_id):
    keyb = InlineKeyboardMarkup()
    keyb.add(InlineKeyboardButton('Принять заказ', callback_data=f'o;{order_id};take'), 
             InlineKeyboardButton("Хмм, что-то не так", callback_data=f'o;{order_id};er'))

    return keyb

def gen_keyb_approve(order_id):
    keyb = InlineKeyboardMarkup()
    keyb.add(InlineKeyboardButton('Заказ 100% выполнен))0)', callback_data=f'o;{order_id};yes'), 
             InlineKeyboardButton("Ой что-то забыл", callback_data=f'o;{order_id};no'))
    
    return keyb

def gen_keyb_cleaner_order(order_id):
    keyb = InlineKeyboardMarkup()
    keyb.add(InlineKeyboardButton("Заказ выполнен!", callback_data=f'o;{order_id};done'))

    return keyb

@bot.message_handler(content_types=['text'])
def start(message):
    if message.text == '/start':
        bot.delete_message(message.chat.id, message.message_id)
        try:
            cleaner = db.Employee.objects.get(tg_id=message.chat.id)
        except:
            cleaner = None
        if cleaner:
            if message.chat.id not in sessions['cleaners']:
                sessions['cleaners'][message.chat.id] = {}
            bot.send_message(message.chat.id, f'Бот CleanDuty. Привет {cleaner.name}', reply_markup=keyb_start)
        else:
            if message.chat.id not in sessions['clients']:
                sessions['clients'][message.chat.id] = {}
            bot.send_message(message.chat.id, f'Чистые богини предстали перед вами', reply_markup=start_menu_keyb)

    if message.text == '/test':
        if message.chat.id not in sessions['cleaners']:
                sessions['cleaners'][message.chat.id] = {}

        bot.delete_message(message.chat.id, message.message_id)
        table = get_time_table(datetime.datetime(year=2024, month=3, day=21))
        keyboard = gen_ketb_time(time_available(table, datetime.timedelta(hours=4)))

        bot.send_message(message.chat.id, "Расписание", reply_markup=keyboard)
        # cleaner_order = [i[0] for i in db.Employees_list.objects.values_list('order_id')]
        # orders = [i for i in db.Order.objects.exclude(id__in=cleaner_order)]
        # for o in gen_order_card(orders):
        #     mes = gen_text(o)
        #     bot.send_message(cleaners_chat, mes, reply_markup=gen_keyb_order(o[0]))


@bot.callback_query_handler(func=lambda call: any(cllb in call.data for cllb in ['c;cleaning', 'c;main_menu', 'с;ord;m', 'с;ord;add', 'с;ord;del', 'c;pre_final', 'c;final', 'c;adress', 'c;phone']))
def query_handler_user_cleaning_start(call):
    bot.answer_callback_query(callback_query_id=call.id)
    chat_id, message_id, data, text, keyb = adv_parse(call)
    # log output
    print(f'[Log call.data]: {call.data}.')
    sys.stdout.flush()
    if chat_id in sessions['clients']:
        sessions['clients'][chat_id]['date_on'] = False
        # main menu generation
        if data.split(';')[1] == 'main_menu':
            print(call.from_user)
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=message_id,
                                  text='Чистые богини предстали перед вами',
                                  reply_markup=start_menu_keyb)
        # services menu generation
        elif data.split(';')[1] == 'cleaning':
            gen_client_order_num_list(chat_id)
            text = gen_text_for_order(chat_id)
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=message_id,
                                  text=text,
                                  reply_markup=gen_order_keyb(chat_id, 0))
        # pre_final step i.e. before sending info into cleaners chat
        elif data.split(';')[1] == 'pre_final':
            client = db.Client.objects.filter(chat_id=chat_id)
            if not client:
                if call.from_user.username:
                    db.Client(tel=sessions['clients'][chat_id]['tel'], tg_nickname=call.from_user.username, adress=sessions['clients'][chat_id]['location'], chat_id=chat_id).save()
                else:
                    db.Client(tel=sessions['clients'][chat_id]['tel'], adress=sessions['clients'][chat_id]['location'], chat_id=chat_id).save()
            else:
                a = db.Client.objects.filter(chat_id=chat_id)
                a_list = a.values_list()[0]
                if sessions['clients'][chat_id]['tel'] and a_list[2] != sessions['clients'][chat_id]['tel']:
                    a.update(tel=sessions['clients'][chat_id]['tel'])
                else:
                    sessions['clients'][chat_id]['tel'] = a_list[2]
                if sessions['clients'][chat_id]['location'] and a_list[3] != sessions['clients'][chat_id]['location']:
                    a.update(adress=sessions['clients'][chat_id]['location'])
                else:
                    sessions['clients'][chat_id]['location'] = a_list[3]
            sessions['clients'][chat_id]['date_on'] = True
            text, time = gen_text_for_order(chat_id, time_send_on=True)
            total_price = gen_text_for_order(chat_id, price=True)
            sessions['clients'][chat_id]['total_price'] = total_price
            sessions['clients'][chat_id]['cleaning_time'] = time
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=message_id,
                                  text=text,
                                  reply_markup=gen_pre_final_keyb())
        # final step - now database fill
        elif data.split(';')[1] == 'final':
            order = filling_db_for_user_oder(chat_id)
            
            for o in gen_order_card(orders=[order]):
                mes = gen_text(o)
                a = bot.send_message(cleaners_chat, mes, reply_markup=gen_keyb_order(o[0]))
                cash['to_edit'].append(a)

        # phone adding if needed
        elif data.split(';')[1] == 'phone':
            text = gen_text_for_order(chat_id)
            text += 'Введите ваш телефон\nФормат телефона +375 ххххххххх'
            bot.delete_message(chat_id, message_id)
            mes = bot.send_message(chat_id, text)
            # next step handler for safely data retrieve
            bot.register_next_step_handler(mes, phone_from_client)
        elif data.split(';')[1] == 'adress':
            text = gen_text_for_order(chat_id)
            text += 'Введите ваш адрес'
            bot.delete_message(chat_id, message_id)
            mes = bot.send_message(chat_id, text)
            # next step handler for safely data retrieve
            bot.register_next_step_handler(mes, location_from_client)
        # movement of services slider
        elif data.split(';')[2] == 'm':
            move = int(data.split(';')[3])
            text = gen_text_for_order(chat_id)
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=message_id,
                                  text=text,
                                  reply_markup=gen_order_keyb(chat_id, move))
        # adding +1 service if can be done
        elif data.split(';')[2] == 'add':
            index = int(data.split(';')[3])
            # check for number change - only applied if make sense
            change_number_for_oder(chat_id, index, 1)
            num = int(data.split(';')[4])
            text = gen_text_for_order(chat_id)
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=message_id,
                                  text=text,
                                  reply_markup=gen_order_keyb(chat_id, num))
        # adding -1 service if can be done
        elif data.split(';')[2] == 'del':
            index = int(data.split(';')[3])
            # check for number change - only applied if make sense
            change_number_for_oder(chat_id, index, -1)
            num = int(data.split(';')[4])
            text = gen_text_for_order(chat_id)
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=message_id,
                                  text=text,
                                  reply_markup=gen_order_keyb(chat_id, num))

def phone_from_client(message):
    try:
        chat_id = message.chat.id
        phone = message.text
        if len(phone) == 9 and phone.isdigit():
            sessions['clients'][chat_id]['tel'] = int(phone)
            print('приняли телефон')
            text = gen_text_for_order(chat_id)
            keyb = InlineKeyboardMarkup()
            if sessions['clients'][chat_id]['location']:
                keyb.add(InlineKeyboardButton("Продолжить", callback_data='c;pre_final'))
            else:
                keyb.add(InlineKeyboardButton("Продолжить", callback_data='c;adress'))
            keyb.add(InlineKeyboardButton("Поменять телефон", callback_data='c;phone'))
            bot.send_message(chat_id, text, reply_markup=keyb)
        else:
            msg = bot.reply_to(message, 'Формат телефона +375 ххххххххх')
            bot.register_next_step_handler(msg, phone_from_client)
    except Exception as e:
        print(e)
        bot.reply_to(message, 'oooops')


def location_from_client(message):
    try:
        chat_id = message.chat.id
        loc = message.text
        sessions['clients'][chat_id]['location'] = loc
        print('приняли адресс')
        text = gen_text_for_order(chat_id)
        keyb = InlineKeyboardMarkup()
        keyb.add(InlineKeyboardButton("Продолжить", callback_data='c;pre_final'))
        keyb.add(InlineKeyboardButton("Поменять адресс", callback_data='c;adress'))
        bot.send_message(chat_id, text, reply_markup=keyb)
    except Exception as e:
        print(e)
        bot.reply_to(message, 'oooops')


@bot.callback_query_handler(func=lambda call: call.data == 'c;calendar')
def query_handler_user_calendar_start(call):
    bot.answer_callback_query(callback_query_id=call.id)
    chat_id, message_id, data, text, keyb = adv_parse(call)
    calendar, step = DetailedTelegramCalendar().build()
    bot.edit_message_text(chat_id=chat_id,
                          message_id=message_id,
                          text=f"Select {LSTEP[step]}",
                          reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def cal(c):
    chat_id, message_id, data, text, keyb = adv_parse(c)
    result, key, step = DetailedTelegramCalendar().process(c.data)
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        sessions['clients'][chat_id]['date'] = result
        sessions['clients'][chat_id]['date_on'] = True
        # duration of work - time
        text, time = gen_text_for_order(chat_id, time_send_on=True) 
        sessions['clients'][chat_id]['cleaning_time'] = time
        keyb = InlineKeyboardMarkup()
        day = sessions['clients'][chat_id]['date']
        sessions['clients'][chat_id]['date'] = datetime.datetime(day.year, day.month, day.day)
        table = get_time_table(sessions['clients'][chat_id]['date'])
        time = datetime.timedelta(hours=int(time), minutes=30*(time % 1 != 0))
        time_pool = time_available(table, time)
        if all([not time_pool[key] for key in time_pool.keys()]):
            text = f"К сожалению в этот день все клинеры заняты, выберите другую дату"
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton('Выбрать другую дату', callback_data='c;calendar'))
        else:
            text = f"Вы выбрали дату: {sessions['clients'][chat_id]['date'].date()}\nВыберите время"
            keyboard = gen_ketb_time(time_pool)
            bot.edit_message_text(text,
                                  c.message.chat.id,
                                  c.message.message_id,
                                  reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data[:7] == 'c;time;')
def time_recording(call):
    chat_id, message_id, data, text, keyb = adv_parse(call)
    h, m = map(int, data.split(';')[2].split(':'))
    day = sessions['clients'][chat_id]['date']
    sessions['clients'][chat_id]['date'] = datetime.datetime(day.year, day.month, day.day, h, m)
    print(sessions['clients'][chat_id]['date'])
    client = db.Client.objects.filter(chat_id=chat_id)
    keyb=InlineKeyboardMarkup()
    if client:
        keyb.add(InlineKeyboardButton("Продолжить", callback_data='c;pre_final'))
    else:
        keyb.add(InlineKeyboardButton("Продолжить", callback_data='c;phone'))
    keyb.add(InlineKeyboardButton('Изменить дату и время', callback_data='c;calendar'))
    text = gen_text_for_order(chat_id, time_send_on=True)
    bot.edit_message_text(text,
                          chat_id,
                          message_id,
                          reply_markup=keyb)


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    bot.answer_callback_query(callback_query_id=call.id)
    chat_id = call.message.chat.id
    data = call.data.split(';')

    # log output
    print(f'[Log call.data]: {call.data}.')
    sys.stdout.flush()

    if chat_id in sessions['cleaners']:
        if call.data.split(';')[0] == 'sched':
            for o in gen_order_card(chat_id=chat_id):
                mes = gen_text(o)
                a = bot.send_message(chat_id, mes, reply_markup=gen_keyb_cleaner_order(o[0]))
                cash['to_edit'].append(a)

        elif data[0] == 'o':
            if data[2] == 'done':
                bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=call.message.text+'\nДополнительное подтвержение', reply_markup=gen_keyb_approve(data[1]))
            elif data[2] == 'yes':
                order = db.Order.objects.get(pk=int(data[1]))
                order.is_finished = True
                order.save()             

                bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=call.message.text + '\n\nЗаказ выполнен!')
                cash['to_edit'].pop(call.message.message_id)

            elif data[2] == 'no':
                bot.delete_message(chat_id, call.message.message_id)

    # to delete
    if call.message.chat.id == cleaners_chat:
        if data[0] == 'close':
            bot.delete_message(cleaners_chat, call.message.message_id)
        elif data[0] == 'o':
            if data[2] == 'take':
                cleaner = db.Employee.objects.get(tg_id=call.from_user.id)
                order = db.Order.objects.get(id=int(data[1]))
                db.Employees_list.objects.create(order_id=order, employee_id=cleaner)
                bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=call.message.text+'\n Заказ принят')
            elif data[2] == 'er':
                print('smth to deal with errors')

print('ready')
bot.infinity_polling()