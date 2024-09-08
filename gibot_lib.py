import telebot
from telebot import types
from random import shuffle

VERSION='2.0'

from db_lib import *
from game_lib import *
from log_lib import *

IBOT_COMPLEXITY_ANSWER = 'complexity:'
IBOT_TYPE1_ANSWER = 'type1answer:'
IBOT_TYPE2_ANSWER = 'type2answer:'
IBOT_GAMETYPE_ANSWER = 'gametype:'

CMD_START = '/start'
CMD_HELP = '/help'
CMD_SETTINGS = '/settings'

# Returns help message
def ibotGetHelpMessage(userName):
    ret = ibotGetWelcomeMessage(userName)
    return ret + '''
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
            text=f'Пользователь не зарегистрирован. Наберите "{CMD_START}".'
        )
        return False
    return True

# Get user settings
def ibotGetUserSettings(userName):
    userSettings = Connection.getUserSetting(userName)
    ret = None
    if (dbFound(userSettings)):
        ret = {'game_type':userSettings[0], 'complexity':userSettings[1]}
    return ret

# Get welcome message
def ibotGetWelcomeMessage(userName):
    settings = ibotGetUserSettings(userName)
    print(settings)
    ret = f'''
Добро пожаловать, {userName}!
   Это игра "Угадай картину". Версия: {VERSION}

Твои текущие настройки следующие:
    '''
    gameTypes = Connection.getGameTypes()
    Complexities = Connection.getComplexities()
    gameTypeTxt = ''
    for gt in gameTypes:
        if (gt[0] == settings["game_type"]):
            gameTypeTxt = gt[1]
    ret = ret + f'''Выбранный тип игры: "{gameTypeTxt}"
    '''
    complexityTxt = ''
    for c in Complexities:
        if (c[0] == settings["complexity"]):
            complexityTxt = c[1]
    ret = ret + f'''Выбранная сложность: "{complexityTxt}"
    '''
    ret = ret + f'''
Удачи тебе!!!
    '''
    return ret

# Settings section
def ibotSettings(bot, message):
    ibotRequestGameType(bot, message)

# Check that game3 is in progress
# Returns: True/False
def ibotCheckGameTypeNInProgress(bot, message, gameType):
    fName = ibotCheckGameTypeNInProgress.__name__
    userName = message.from_user.username
    # Check user name format first
    ret = ibotCheckUserName(bot, message)
    if (not ret):
        return False
    ret = Connection.getCurrentGame(userName)
    if (dbFound(ret)):
        gameInfo = Connection.getGameInfoById(ret)
        if (dbFound(gameInfo)): # Game info is valid
            if (gameInfo['type'] == gameType):
                return True
        else:
            log(f'{fName}: Cannot get gameInfo from DB: {ret}', LOG_ERROR)
    return False

# Register new user. Returns: True/False
def ibotUserRegister(userName):
    if (not dbLibCheckUserName(userName)):
        log(f'ibotUserRegister: Try to register user with wrong format ({userName})', LOG_ERROR)
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
    elif (type == 2):
        ibotShowQuestionType2(bot,message, gameId)
    elif (type == 3): # type = 3
        ibotShowQuestionType3(bot,message, gameId)
    else:
        bot.send_message(message.from_user.id, "Неизваестный тип игры. Пожалуйста, начните новую игру.")
    
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
        bot.send_message(message.from_user.id, text=f'Извините, но игра уже завершена. Введите "{CMD_START}" чтобы начать новую.')
        return
    imageIds = guess_image.getQuestionType1Options(gameInfo)
    if (not imageIds):
        log(f'{ibotShowQuestionType1.__name__}: wrong format of imageIds = {imageIds}', LOG_ERROR)
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

# Send buttons after answer
def ibotSendAfterAnswer(bot, message):
    key1 = types.InlineKeyboardButton(text='Сыграть еще раз', callback_data=CMD_START)
    key2= types.InlineKeyboardButton(text='Выбрать другой тип игры/сложность', callback_data=CMD_SETTINGS)
    keyboard = types.InlineKeyboardMarkup(); # keyboard
    keyboard.add(key1)
    keyboard.add(key2)
    question = 'Выберите дальнейшее действие:'
    bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)

# Modify captures of images with creator, name, year
def ibotModifyImageCaptures(bot, message, mIds, imageIds):
    if (len(mIds) != len(imageIds)):
        log(f'{ibotModifyImageCaptures.__name__}: len of mIds and imageIds doesnt match', LOG_ERROR)
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
        log(f'{ibotModifyImageCapture.__name__}: Cannot get image info for {imageId}', LOG_ERROR)

def ibotShowQuestionType2(bot,message, gameId, gameType = 2):
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
        bot.send_message(message.from_user.id, text='Игра уже сыграна. Пожалуйста, начните новую.')
        return
    # Show image
    bot.send_photo(message.from_user.id, url)
    textQuestion = guess_image.getTextQuestion(gameInfo)
    if (gameType == 2): # Show answer options
        creatorId = imageInfo['creatorId']
        creatorName = imageInfo['creatorName']
        creators = Connection.getNCreators(CREATORS_IN_TYPE2_ANSWER, creatorId, complexity)
        creators.append({'creatorId':creatorId,'creatorName':creatorName})
        shuffle(creators)
        # Show buttons with answer options
        keyboard = types.InlineKeyboardMarkup()
        for i in range(0, len(creators)): # 2 because we start with 1 + correct creator
            creatorId = creators[i].get('creatorId')
            creatorName = creators[i].get('creatorName')
            data = f'{IBOT_TYPE2_ANSWER}{creatorId}'
            key = types.InlineKeyboardButton(text=creatorName, callback_data=data)
            keyboard.add(key)

        bot.send_message(message.from_user.id, text=textQuestion, reply_markup=keyboard)
    else: # game type == 3
        bot.send_message(message.from_user.id, text=textQuestion)

def ibotShowQuestionType3(bot,message, gameId):
    return ibotShowQuestionType2(bot,message, gameId, gameType=3)


def ibotCheckAnswerGameType3(userCreatorName, correctCreatorName):
    # 1. Convern both strings to the same format
    userCreatorName = userCreatorName.lower() # Convert to lower
    correctCreatorName = correctCreatorName.lower()
    userCreatorName = userCreatorName.replace('ё','е') # Replace 'ё'
    correctCreatorName = correctCreatorName.replace('ё','е') # Replace 'ё'
    correctCreatorName = correctCreatorName.replace('й','й') # Replace 'й'

    # 0. Full match
    if (userCreatorName == correctCreatorName):
        log(f'Full match: {userCreatorName} == {correctCreatorName}',LOG_DEBUG)
        return True

    lU = len(userCreatorName)
    lC = len(correctCreatorName)
    # 2. Check length of userAnswer
    if (lU > lC):
        log(f'User len > correct len: {lU} > {lC}',LOG_DEBUG)
        return False
    
    # 3. Check if only one word in answer (probably last name)
    userAnswerWords = userCreatorName.split(' ')
    if (len(userAnswerWords) == 1):
        # Get last work of correctAnswer
        correctAnswerWords = correctCreatorName.split(' ')
        userAnswerLastWord = userAnswerWords[0]
        correctAnswerLastWord = correctAnswerWords[-1]
        # If correct last word len < 3 - only exact answer
        if (len(correctAnswerLastWord) <= 3):
            if (userAnswerLastWord == correctAnswerLastWord):
                log(f'Full last word match (len <=3): {userAnswerLastWord} == {correctAnswerLastWord}',LOG_DEBUG)
                return True
        else:
            # Check len difference
            lAlw = len(userAnswerLastWord)
            lClw = len(correctAnswerLastWord)
            if (abs(lAlw-lClw) <= 2):
                # Check similarity for last name
                ret = isStrSimilar(userAnswerLastWord, correctAnswerLastWord)
                if (ret):
                    log(f'Last word similarity match (similarity={ret}): {userAnswerLastWord} | {correctAnswerLastWord}',LOG_DEBUG)
                    return True

    if (lU > 5):
        correctAnswer = correctCreatorName[-lU:]
        ret = isStrSimilar(userCreatorName, correctAnswer)
        if (ret):
            log(f'Last part of answer similarity (similarity={ret}): {userCreatorName} | {correctAnswer}',LOG_DEBUG)
            return True

    # 4. Check Levenstein similarity for full answer
    ret = isStrSimilar(userCreatorName, correctCreatorName)
    if (ret):
        log(f'Full answer similarity (similarity={ret}: {userCreatorName} | {correctCreatorName}',LOG_DEBUG)
        return True

    return ret
