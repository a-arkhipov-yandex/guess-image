import telebot
from telebot import types
import re
from random import shuffle

from db_lib import *
from game_lib import *

IBOT_COMPLEXITY_ANSWER = 'complexity:'
IBOT_TYPE1_ANSWER = 'type1answer:'
IBOT_TYPE2_ANSWER = 'type2answer:'
IBOT_GAMETYPE_ANSWER = 'gametype:'

# Returns help message
def ibotGetHelpMessage():
    return '''
        Команды GuessImage_Bot:
        /help - вывести помощь по каомандам (это сообщение)
        /start - начать новую игру с текущими настройками (может вызываться на любом шаге)
        /settings - установить настройки типа игры и сложности
    '''
    #    /menu - вызвать меню
    #    /game - продолжить начатую игру
    #'''

def ibotIsUserExist(userName):
    userId = Connection.getUserIdByName(userName)
    if(dbNotFound(userId)):
        return False
    return True

# Check username. Return True on success of False on failure
def ibotCheckUserName(bot, message):
    userName = message.from_user.username
    # Check user name format first
    if (not dbLibCheckUserName(userName)):
        bot.send_message(
            message.from_user.id,
            text=f'Неверный формат имени пользователя {userName} - простите, но у вас не получится поиграть.'
        )
        return False
    # Check that user exists in DB
    if (not ibotIsUserExist(userName)):
        bot.send_message(
            message.from_user.id,
            text=f'Пользователь не зарегистрирован. Наберите "/start".'
        )
        return False
    return True

# Get user settings
def ibotGetUserSettings(userName):
    return ''

# Get welcome message
def ibotGetWelcomeMessage(userName):
    settings = ibotGetUserSettings(userName)
    ret = f'''
        Добро пожаловать, {userName}!
        Это игра "Угадай картину".
        Твои текущие настройки следующие:
        {settings}
        Досупные команды можно посмотреть набрав '/help'
        Чтобы начать игру - набери '/start'
        Удачи тебе!!!
    '''
    return ret

# Settings section
def ibotSettings(bot, message):
    ibotRequestGameType(bot, message)

# Register new user. Returns: True/False
def ibotUserRegister(userName):
    if (not dbLibCheckUserName(userName)):
        print(f'ERROR: Try to register user with wrong format ({userName})')
        return False
    # Check if user registered
    userId = Connection.getUserIdByName(userName)
    if (not dbFound(userId)):
        # Register new user
        ret = Connection.insertUser(userName)
        # If registration fails - return error
        if (not ret):
            return False
    return True

# Request new GameType
def ibotRequestGameType(bot, message):
    # Check user name format first
    ret = ibotCheckUserName(bot, message)
    if (not ret):
        return
    # Get game type
    game_types = Connection.getGameTypes()
    # Request game type
    keyboard = types.InlineKeyboardMarkup(); # keyboard
    for gameType in game_types:
        key = types.InlineKeyboardButton(text=gameType[1], callback_data=f'{IBOT_GAMETYPE_ANSWER}{gameType[0]}')
        keyboard.add(key)
    question = 'Выберите тип игры:'
    bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)

# Start new game
def ibotRequestComplexity(bot, message):
    # Check user name format first
    ret = ibotCheckUserName(bot, message)
    if (not ret):
        return
    complexities = Connection.getComplexities()
    # Request game complexity
    keys = []
    for c in complexities:
        key = types.InlineKeyboardButton(text=c[1], callback_data=f'{IBOT_COMPLEXITY_ANSWER}{c[0]}')
        keys.append(key)
    keyboard = types.InlineKeyboardMarkup([keys]); # keyboard
    question = 'Выберите уровень сложности:'
    bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)

def ibotShowQuestion(bot,message,type,gameId):
    if (type == 1):
        ibotShowQuestionType1(bot,message, gameId)
    else:
        ibotShowQuestionType2(bot,message, gameId)

# Find number of correct answer in type 1 question
# Returns:
#   i - num of correct answer starting from 1
#   None - if any issues
def ibotFindNumOfType1Answer(imageIds, correctId):
    ret = None
    for i in range(0, len(imageIds)):
        if (imageIds[i] == correctId):
            ret = i + 1
            break
    return ret

def ibotShowQuestionType1(bot,message, gameId):
    # Get gameInfo
    gameInfo = Connection.getGameInfoById(gameId)
    finished = (gameInfo['result'] != None)
    if (finished):
        # TODO: show finished info
        bot.send_message(message.from_user.id, text='Извините, но игра уже завершена. Введите "/start" чтобы начать новую.')
        return
    imageIds = guess_image.getQuestionType1Options(gameInfo)
    if (not imageIds):
        print(f'ERROR: {ibotShowQuestionType1.__name__}: wrong format of imageIds = {imageIds}')
        bot.send_message(message.from_user.id, "Произошла ошибка. Пожалуйста начните новую игру")
        return
    data = []
    # Get image URLs
    for id in imageIds:
        url = Connection.getImageUrlById(id)
        data.append({'url':url,'iId':id})

    # Get text question
    textQuestion = guess_image.getTextQuestion(gameInfo)
    bot.send_message(message.from_user.id, text=textQuestion)
    media_group = []
    for d in data:
        media_group.append(types.InputMediaPhoto(show_caption_above_media=True, media=d['url']))
    ret = bot.send_media_group(message.from_user.id, media=media_group)
    mIds = []
    for m in ret:
        mIds.append(m.id)
    mIdsTxt = " ".join(str(i) for i in mIds)
    # Save options in current game data
    ret = Connection.setCurrentGameData(message.from_user.username, mIdsTxt)
    # Show buttons for answer
    keys = []
    for i in range(len(data)):
        responseData = f'{IBOT_TYPE1_ANSWER}{data[i]["iId"]}'
        keys.append(types.InlineKeyboardButton(text=str(i+1), callback_data=responseData))
    keyboard = types.InlineKeyboardMarkup([keys])
    bot.send_message(message.from_user.id, text='Выберите вариант:', reply_markup=keyboard)

# Modify captures of images with creator, name, year
def ibotModifyImageCaptures(bot, message, mIds, imageIds):
    if (len(mIds) != len(imageIds)):
        print(f'ERROR: {ibotModifyImageCaptures.__name__}: len of mIds and imageIds doesnt match')
        return
    for i in range(0, len(mIds)):
        ibotModifyImageCapture(bot, message, mIds[i], imageIds[i])

def ibotModifyImageCapture(bot, message, messageId, imageId):
    # Get image info
    imageInfo = Connection.getImageInfoById(imageId)
    if (dbFound(imageInfo)):
        caption = f"{imageInfo['creatorName']} - {imageInfo['imageName']} - {imageInfo['yearStr']}"
        # Edit image capture
        bot.edit_message_caption(chat_id=message.from_user.id, message_id=messageId, caption=caption)
    else:
        print(f'ERROR: {ibotModifyImageCapture.__name__}: Cannot get image info for {imageId}')

def ibotShowQuestionType2(bot,message, gameId):
    # Get gameInfo
    gameInfo = Connection.getGameInfoById(gameId)
    complexity = gameInfo['complexity']
    imageId = gameInfo['question']
    # Get image URL
    url = Connection.getImageUrlById(imageId)
    # Get answer options
    imageInfo = Connection.getImageInfoById(imageId)
    finished = (gameInfo['result'] != None)
    if (finished):
        # TODO: show finished info
        bot.send_message(message.from_user.id, text='Sorry - this game is already finished. Please start new one.')
        return
    creatorId = imageInfo['creatorId']
    creatorName = imageInfo['creatorName']
    creators = Connection.getNCreators(CREATORS_IN_TYPE2_ANSWER, creatorId, complexity)
    creators.append({'creatorId':creatorId,'creatorName':creatorName})
    shuffle(creators)
    # Show image
    bot.send_photo(message.from_user.id, url)
    # Show buttons with answer options
    keyboard = types.InlineKeyboardMarkup()
    for i in range(0, len(creators)): # 2 because we start with 1 + correct creator
        creatorId = creators[i].get('creatorId')
        creatorName = creators[i].get('creatorName')
        data = f'{IBOT_TYPE2_ANSWER}{creatorId}'
        key = types.InlineKeyboardButton(text=creatorName, callback_data=data)
        keyboard.add(key)
    textQuestion = guess_image.getTextQuestion(gameInfo)
    bot.send_message(message.from_user.id, text=textQuestion, reply_markup=keyboard)

