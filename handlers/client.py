from aiogram import Dispatcher, types
from keyboards import keyboards_Client, keyboardDevice, addressInlineKeyboard
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import random
import pytesseract
import cv2
from aiogram.dispatcher.filters import Text
from aiogram import Bot 
from aiogram.dispatcher import Dispatcher
from test import TOKEN
from aiogram.contrib.fsm_storage.memory import MemoryStorage #Хранение данных в ОЗУ
import psycopg2


def sql_start():
   
    global con, cur 
    con = psycopg2.connect(
        database="CBMO", 
        user="postgres", 
        password="1963", 
        host="127.0.0.1", 
        port="5432"
    )
    cur = con.cursor()  
    if con:
        print('Подключение в БД успешно')

    cur.execute('''CREATE TABLE if not exists USERS 
    (   
        id_user INT,
        firstname CHARACTER VARYING(50),
        lastname CHARACTER VARYING(50),
        name_device CHARACTER VARYING(50),
        description text);''')

    cur.execute('''CREATE TABLE if not exists NAME 
        (   id INT PRIMARY KEY,
            id_user INT,
            firstname CHARACTER VARYING(50),
            lastname CHARACTER VARYING(50),
            name_device CHARACTER VARYING(50),
            description text);''')
    
    cur.execute('''CREATE TABLE if not exists DESCRIPTION 
    (   id INT PRIMARY KEY, 
        id_user INT,      
        description text);''')
    
    cur.execute('''CREATE TABLE if not exists PHOTO_INV 
    (   id INT PRIMARY KEY, 
        id_user INT,      
        photo_inventar text,
        photo_puth text);''')

    cur.execute('''CREATE TABLE if not exists CONTACT_USER 
    (   id INT PRIMARY KEY, 
        id_user INT,      
        contact_user text);''')

    con.commit()  


storage=MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)

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
        cur.execute("INSERT INTO NAME (id, id_user, firstname, lastname, name_device ) VALUES (%s, %s, %s, %s, %s);", (data['appeal'], id_user, firstname, lastname,name_device ))
        con.commit()
        await FSMAdmin.next()
        await message.answer('Опишите кратко проблему, которую необходимо решить')

async def description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        number = data['appeal'] 
        id_user = message.from_user.id
        description = message.text
        cur.execute("INSERT INTO DESCRIPTION (id, id_user, description ) VALUES (%s, %s, %s);", (number, id_user, description))
        con.commit()
        # cur.execute("SELECT NAME.id, NAME.id_user, firstname, lastname, name_device, DESCRIPTION.id, DESCRIPTION.description FROM NAME INNER JOIN DESCRIPTION ON DESCRIPTION.id = NAME.id;")    
        # con.commit()
        await FSMAdmin.next()
        await message.answer('Сфотографируйте инвентарный номер')

async def photoInventar(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        number = data['appeal'] 
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
        
        await message.answer('Подскажите, ваш инвентарный номер = ' + getUpdateText + ' ?', reply_markup = keyboards)
        await FSMAdmin.next()
        cur.execute("INSERT INTO PHOTO_INV (id, id_user, photo_inventar, photo_puth ) VALUES (%s, %s, %s, %s);", (number, id_user, photo_inventar, photo_puth))
        con.commit()

async def contactUser(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        # if (message.text == "Да"):
        #     number = data['appeal'] 
        #     getUpdateText = data['photo_inventar']
        #     data['photo_puth'] = 'Считал с фото корректно'
        #     cur.execute("UPDATE PHOTO_INV SET (photo_puth ) = (%s) WHERE  ;", ('Считал с фото корректно',))
        # else:
        #     puth_fileUser = data['photo_puth']
        #     data['photo_puth'] = puth_fileUser
        #     data['photo_inventar'] = 'Не считал с фото'

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton(text="Отправить номер 📱", request_contact=True))
        await message.answer("Отправить номер для обратной связи\n(Пожалуйста, нажмите на кнопку ниже)", reply_markup=keyboard)
        await FSMAdmin.next()

async def numberAppeal(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        number = data['appeal'] 
        id_user = message.from_user.id    
        contact_user = message.contact.phone_number 
        cur.execute("INSERT INTO CONTACT_USER (id, id_user, contact_user ) VALUES (%s, %s, %s);", (number, id_user, contact_user))
        con.commit()

            
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

