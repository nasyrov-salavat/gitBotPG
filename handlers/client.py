from telnetlib import STATUS
from aiogram import Bot, Dispatcher, types
from keyboards import keyboards_Client, keyboardDevice, addressInlineKeyboard
from aiogram.dispatcher import FSMContext, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage #Хранение данных в ОЗУ
import random
import pytesseract
import cv2
from mysql.connector import Error
import mysql.connector

from config import TOKEN, HOST, USER, PASSWORD, DATABASE

create_table_name = '''CREATE TABLE if not exists name(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    id_user INT,firstname TEXT,
                    lastname TEXT,
                    name_device TEXT)'''

create_table_description = '''CREATE TABLE if not exists description(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    id_user INT,
                    description TEXT)'''

create_table_photo_inv = '''CREATE TABLE if not exists photo_inv(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    id_user INT,
                    photo_inventar TEXT,
                    photo_puth TEXT)'''

create_table_contact_user = '''CREATE TABLE if not exists contact_user(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    id_user INT,
                    contact_user TEXT)'''

create_table_appeal = '''CREATE TABLE if not exists appeal(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    id_user INT,firstname TEXT,
                    lastname TEXT,name_device TEXT,
                    description TEXT, 
                    photo_inventar TEXT,
                    photo_puth TEXT, 
                    contact_user TEXT, 
                    number TEXT,
                    status TEXT )'''

create_table_status_appeal = '''CREATE TABLE if not exists status_appeal(
                    status TEXT )'''


def connect_setting():
    global db_connection
    db_connection = None
    try: 
        db_connection =  mysql.connector.connect(
                host=HOST,
                user=USER,
                password=PASSWORD,
                database=DATABASE,
        )
        print('Успешное подключение к базе данных')
        global cur
        cur = db_connection.cursor()
        with db_connection.cursor() as cursor:   
            cursor.execute(create_table_name)
            cursor.execute(create_table_description)
            cursor.execute(create_table_photo_inv)
            cursor.execute(create_table_contact_user)
            cursor.execute(create_table_appeal)
            cursor.execute(create_table_status_appeal)
            db_connection.commit()
            
    except Error as e:
        print('Не удалось подключиться ')
    


async def on_startup(_):
    print('Происходит подключение к базе данных')
    connect_setting()
        







storage=MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)






############################################################################################################################################################################################
#################   СТАРТ БОТА  ######################################

async def command_start(message: types.Message):
        await bot.send_message(message.from_user.id, f'Здравствуйте, <strong>{message.from_user.first_name} {message.from_user.last_name}.\n\
</strong>Вас приветствует телеграм бот <a href="https://cbmo.ru/">КГУ МО ЦБ МО</a>.\n\
Для дальнейшей работы выберите интересующий Вас раздел', reply_markup=keyboards_Client, parse_mode='HTML')
        await message.delete()

async def adress_start(message: types.Message):
    photo = open('admin/contact/contact_org.png', 'rb')
    await bot.send_photo(chat_id=message.chat.id, photo=photo)

async def listWorker(message: types.Message):
    doc = open('admin/list/Телефоны сотрудников.pdf', 'rb')
    await message.reply_document(doc)

############################################################################################################################################################################################
#################                  callback   ######################################
async def list_menu(message: types.Message):
    await message.answer("Выберите из списка меню необходимую услугу", reply_markup=addressInlineKeyboard)

async def photo_sent(message: types.Message):
    #show_alert=True - Показывать на экране
    photo = open('admin/contact/contact_org.png', 'rb')
    await bot.send_photo(message.from_user.id,photo=photo)

async def doc_sent(message: types.Message):
    doc = open(('admin/list/Телефоны сотрудников') + '.pdf', 'rb')
    await bot.send_document(message.from_user.id, doc)

############################################################################################################################################################################################
#################                  Если "Помощь"  ОБРАБОТЧИК СОСТОЯНИЙ    ######################################
class FSMAdmin(StatesGroup):
    nameDevice = State()    
    description = State() 
    photoInventar = State()
    contactUser = State() 
    numberAppeal = State()       

async def cm_start(message: types.Message):
    await FSMAdmin.next()
    await message.answer('Выберите устройство, которое необходимо починить', reply_markup=keyboardDevice)

async def nameDevice(message: types.Message, state: FSMContext ): 
    async with state.proxy() as data:
        id_user = message.from_user.id
        firstname = message.from_user.first_name
        lastname = message.from_user.last_name
        name_device = message.text
        
        number = str(random.randint(1, 1000000))
        data['appeal'] = number     
        sql = "insert into name(id_user, firstname, lastname, name_device) values(%s, %s, %s, %s)" 
        val =(id_user, firstname, lastname, name_device)
        cur.execute(sql,val) 
        db_connection.commit()
        
        data['GLid_user'] = id_user
        data['GLfirstname'] = firstname
        data['GLlastname'] = lastname
        data['GLname_device'] = name_device

        await FSMAdmin.next()
        await message.answer('Опишите кратко проблему, которую необходимо решить')

async def description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        id_user = message.from_user.id
        description = message.text
        data['GLdescription'] = description

        sql = "insert into description(id_user, description) values(%s, %s)" 
        val =(id_user, description)
        cur.execute(sql,val) 
        db_connection.commit()
        
        await FSMAdmin.next()
        await message.answer('Сфотографируйте инвентарный номер')

async def photoInventar(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        id_user = message.from_user.id                        
        document_id = message.photo[0].file_id  # Получение уникального id для добавления в название файла
        file_info = await bot.get_file(document_id)
        path_photo = f'img/{file_info.file_unique_id}.jpg'
        print(path_photo)

        await message.photo[-1].download(path_photo)
        image = cv2.imread(path_photo)
###########################################################################################################################################################################################
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract' #ОБЯЗАТЕЛЬНО УБРАТЬ ДЛЯ WINDOWS
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract' #ОБЯЗАТЕЛЬНО УБРАТЬ ДЛЯ LINUX
###########################################################################################################################################################################################
        string = pytesseract.image_to_string (image, config = 'outputbase digits')
        getTextMain = string.split('\n')
        getText= [x for x in getTextMain if x]
        if (len(getText) == 0):
            getUpdateText = '0'
        else:
            getUpdateText = getText.pop()
        # if string == '':
        #     getUpdateText = '0'
        # else:
        #     word = "N "
        #     result_with_word = re.search(re.escape(word) + '.*', string).group()
        #     getUpdateText = result_with_word.replace("N ", "")    
        
        keyboards = types.ReplyKeyboardMarkup(resize_keyboard=True) 
        buttons = ["Да", "Нет"]
        keyboards.add(*buttons)
        
        data['photo_inventar'] = getUpdateText
        data['photo_puth'] = str(path_photo)
        photo_inventar = getUpdateText # Для передачи в другую функцию
        photo_puth = str(path_photo)
        sql = "insert into photo_inv(id_user, photo_inventar, photo_puth) values(%s, %s, %s)" 
        val =(id_user, photo_inventar,photo_puth )
        cur.execute(sql,val) 
        db_connection.commit()

        data['GLphoto_inventar'] = photo_inventar
        data['GLphoto_puth'] = photo_puth

        await message.answer('Подскажите, ваш инвентарный номер = ' + getUpdateText + ' ?', reply_markup = keyboards)
        await FSMAdmin.next()


async def contactUser(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        # if (message.text == "Да"):
        #     data['GLphoto_puth'] = 'Считал с фото корректно'
        #     data['GLphoto_inventar']
        # else:
        #     data['photo_inventar'] = 'Не считал с фото'
        #     data['GLphoto_puth']

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton(text="Отправить номер 📱", request_contact=True))
        await message.answer("Отправить номер для обратной связи\n(Пожалуйста, нажмите на кнопку ниже)", reply_markup=keyboard)
        await FSMAdmin.next()

async def numberAppeal(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        number = data['appeal'] 
        id_user = message.from_user.id    
        contact_user = message.contact.phone_number 

        data['GLcontact_user'] = contact_user
        data['GLstatus'] = 'В обработке'
        sql = "insert into contact_user(id_user, contact_user) values(%s, %s)" 
        val =(id_user, contact_user)
        cur.execute(sql,val) 
        db_connection.commit()

        appealsql = "insert into appeal(id_user, firstname, lastname, name_device, description, photo_inventar, photo_puth, contact_user, number, status ) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" 
        datasql =(data['GLid_user'], data['GLfirstname'],  data['GLlastname'], data['GLname_device'], data['GLdescription'], data['GLphoto_inventar'],data['GLphoto_puth'], data['GLcontact_user'],data['appeal'],  data['GLstatus'])
        cur.execute(appealsql,datasql) 
        db_connection.commit()
            
    await message.answer('Спасибо за обращение. Номер вашей заявки = ' + number,  reply_markup=keyboards_Client)
    await state.finish()
    
############################################################################################################################################################################################

def register_handlers_callback(dp : Dispatcher):
    dp.register_message_handler(list_menu, commands="Другое")
    dp.register_callback_query_handler(photo_sent, Text(equals="address"))
    dp.register_callback_query_handler(doc_sent, Text(equals="numbers"))

def register_handlers_client(dp : Dispatcher):
    dp.register_message_handler(command_start, commands=['start', 'help'])
    dp.register_message_handler(cm_start, commands=['Поддержка📝', 'support'], state=None) 
    dp.register_message_handler(listWorker, commands=['phoneorg'])
    dp.register_message_handler(adress_start, commands=['contact'])
    dp.register_message_handler(list_menu, commands=['Подробнее📋', 'other'])

    dp.register_message_handler(nameDevice, state = FSMAdmin.nameDevice)
    dp.register_message_handler(description, state = FSMAdmin.description)
    dp.register_message_handler(photoInventar, state = FSMAdmin.photoInventar, content_types='photo')
    dp.register_message_handler(contactUser, state = FSMAdmin.contactUser )
    dp.register_message_handler(numberAppeal, content_types=types.ContentType.CONTACT, state = FSMAdmin.numberAppeal)