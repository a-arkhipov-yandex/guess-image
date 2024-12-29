from telebot import types
from random import shuffle
import telegram
import telebot

VERSION='2.01'

from db_lib import *
from game_lib import *
from log_lib import *
from img_fs_lib import *
from s3_lib import *

IBOT_COMPLEXITY_ANSWER = 'complexity:'
IBOT_TYPE1_ANSWER = 'type1answer:'
IBOT_TYPE2_ANSWER = 'type2answer:'
IBOT_GAMETYPE_ANSWER = 'gametype:'

CMD_START = '/start'
CMD_HELP = '/help'
CMD_SETTINGS = '/settings'

ENV_BOTSAVEIMAGEPATH = 'BOTSAVEIMAGEPATH'

def getBotImagePath() -> str:
    load_dotenv()
    imagePath = getenv(key=ENV_BOTSAVEIMAGEPATH)
    if (not imagePath):
        imagePath = DEFAULT_SAVE_IMAGE_DIR
    return imagePath

# Returns help message
def ibotGetHelpMessage(userName) -> str:
    ret = ibotGetWelcomeMessage(userName=userName)
    return ret + '''
Команды GuessImage_Bot:
    /help - вывести помощь по каомандам (это сообщение)
    /start - начать новую игру с текущими настройками (может вызываться на любом шаге)
    /settings - установить настройки типа игры и сложности
    '''
    #    /menu - вызвать меню
    #    /game - продолжить начатую игру
    #'''

def ibotIsUserExist(userName) -> bool:
    userId = Connection.getUserIdByName(name=userName)
    if(dbNotFound(result=userId)):
        return False
    return True

def getUserByMessage(message:types.Message):
    username = message.from_user.username
    telegramid = message.from_user.id
    ret = str(telegramid)
    if (checkUserNameFormat(user=username)):
        ret = username
    return ret

# Check username. Return True on success of False on failure
def ibotCheckUserName(bot:telebot.TeleBot, message:telegram.Message) -> bool:
    userName = getUserByMessage(message=message)
    # Check that user exists in DB
    if (not ibotIsUserExist(userName=userName)):
        bot.send_message(
            chat_id=message.from_user.id,
            text=f'Пользователь не зарегистрирован. Наберите "{CMD_START}".'
        )
        return False
    return True

# Get user settings
def ibotGetUserSettings(userName):
    userSettings = Connection.getUserSetting(userName=userName)
    ret = None
    if (dbFound(result=userSettings)):
        ret = {'game_type':userSettings[0], 'complexity':userSettings[1]}
    return ret

# Get welcome message
def ibotGetWelcomeMessage(userName) -> str:
    settings = ibotGetUserSettings(userName=userName)
    print(settings)
    un = ''
    if (userName):
        un= f', {userName}'
    ret = f'''
Добро пожаловать{un}!
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
def ibotSettings(bot:telebot.TeleBot, message:types.Message) -> None:
    ibotRequestGameType(bot=bot, message=message)

# Check that game type gameType is in progress
# Returns: True/False
def ibotCheckGameTypeNInProgress(bot:telebot.TeleBot, message:types.Message, gameType) -> bool:
    fName = ibotCheckGameTypeNInProgress.__name__
    userName = getUserByMessage(message=message)
    # Check user name format first
    ret = ibotCheckUserName(bot=bot, message=message)
    if (not ret):
        return False
    ret = Connection.getCurrentGame(userName=userName)
    if (dbFound(result=ret)):
        gameInfo = Connection.getGameInfoById(id=ret)
        if (dbFound(result=gameInfo)): # Game info is valid
            if (gameInfo['type'] == gameType):
                return True
        else:
            log(str=f'{fName}: Cannot get gameInfo from DB: {ret}', logLevel=LOG_ERROR)
    return False

# Register new user. Returns: True/False
def ibotUserRegister(userName) -> bool:
    if (not dbLibCheckUserName(user_name=userName)):
        log(str=f'ibotUserRegister: Try to register user with wrong format ({userName})', logLevel=LOG_ERROR)
        return False
    # Check if user registered
    userId = Connection.getUserIdByName(name=userName)
    if (not dbFound(result=userId)):
        # Register new user
        ret = Connection.insertUser(userName=userName)
        # If registration fails - return error
        if (not ret):
            return False
    return True

# Request new GameType
def ibotRequestGameType(bot:telebot.TeleBot, message:types.Message) -> None:
    # Check user name format first
    ret = ibotCheckUserName(bot=bot, message=message)
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
    bot.send_message(chat_id=message.from_user.id, text=question, reply_markup=keyboard)

# Start new game
def ibotRequestComplexity(bot:telebot.TeleBot, message:types.Message) -> None:
    # Check user name format first
    ret = ibotCheckUserName(bot=bot, message=message)
    if (not ret):
        return
    complexities = Connection.getComplexities()
    # Request game complexity
    keys = []
    for c in complexities:
        key = types.InlineKeyboardButton(text=c[1], callback_data=f'{IBOT_COMPLEXITY_ANSWER}{c[0]}')
        keys.append(key)
    keyboard = types.InlineKeyboardMarkup(keyboard=[keys]); # keyboard
    question = 'Выберите уровень сложности:'
    bot.send_message(chat_id=message.from_user.id, text=question, reply_markup=keyboard)

def ibotShowQuestion(bot:telebot.TeleBot,message:types.Message,type,gameId) -> None:
    if (type == 1):
        ibotShowQuestionType1(bot=bot,message=message, gameId=gameId)
    elif (type == 2):
        ibotShowQuestionType2(bot=bot,message=message, gameId=gameId)
    elif (type == 3): # type = 3
        ibotShowQuestionType3(bot=bot,message=message, gameId=gameId)
    else:
        bot.send_message(chat_id=message.from_user.id, text="Неизвестный тип игры. Пожалуйста, начните новую игру.")
    
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

def ibotShowQuestionType1(bot:telebot.TeleBot,message:types.Message, gameId) -> None:
    # Get gameInfo
    gameInfo = Connection.getGameInfoById(id=gameId)
    finished = (gameInfo['result'] != None)
    if (finished):
        bot.send_message(chat_id=message.from_user.id, text=f'Извините, но игра уже завершена. Введите "{CMD_START}" чтобы начать новую.')
        return
    imageIds = guess_image.getQuestionType1Options(gameInfo=gameInfo)
    if (not imageIds):
        log(str=f'{ibotShowQuestionType1.__name__}: wrong format of imageIds = {imageIds}', logLevel=LOG_ERROR)
        bot.send_message(chat_id=message.from_user.id, text="Произошла ошибка. Пожалуйста начните новую игру")
        return
    data = []
    # Get image URLs
    for id in imageIds:
        url = Connection.getImageUrlById(id=id)
        data.append({'url':url,'iId':id})

    # Get text question
    textQuestion = guess_image.getTextQuestion(gameInfo=gameInfo)
    bot.send_message(chat_id=message.from_user.id, text=textQuestion)
    media_group = []
    for d in data:
        media_group.append(types.InputMediaPhoto(show_caption_above_media=True, media=d['url']))
    ret = bot.send_media_group(chat_id=message.from_user.id, media=media_group)
    mIds = []
    for m in ret:
        mIds.append(m.id)
    mIdsTxt = " ".join(str(i) for i in mIds)
    # Save options in current game data
    ret = Connection.setCurrentGameData(userName=message.from_user.username, gameData=mIdsTxt)
    # Show buttons for answer
    keys = []
    for i in range(len(data)):
        responseData = f'{IBOT_TYPE1_ANSWER}{data[i]["iId"]}'
        keys.append(types.InlineKeyboardButton(text=str(i+1), callback_data=responseData))
    keyboard = types.InlineKeyboardMarkup(keyboard=[keys])
    bot.send_message(chat_id=message.from_user.id, text='Выберите вариант:', reply_markup=keyboard)

# Send buttons after answer
def ibotSendAfterAnswer(bot:telebot.TeleBot, message:types.Message) -> None:
    key1 = types.InlineKeyboardButton(text='Сыграть еще раз', callback_data=CMD_START)
    key2= types.InlineKeyboardButton(text='Выбрать другой тип игры/сложность', callback_data=CMD_SETTINGS)
    keyboard = types.InlineKeyboardMarkup(); # keyboard
    keyboard.add(key1)
    keyboard.add(key2)
    question = 'Выберите дальнейшее действие:'
    bot.send_message(chat_id=message.from_user.id, text=question, reply_markup=keyboard)

# Modify captures of images with creator, name, year
def ibotModifyImageCaptures(bot, message, mIds, imageIds) -> None:
    if (len(mIds) != len(imageIds)):
        log(str=f'{ibotModifyImageCaptures.__name__}: len of mIds and imageIds doesnt match', logLevel=LOG_ERROR)
        return
    for i in range(0, len(mIds)):
        ibotModifyImageCapture(bot=bot, message=message, messageId=mIds[i], imageId=imageIds[i])

def ibotModifyImageCapture(bot:telebot.TeleBot, message:types.Message, messageId, imageId) -> None:
    # Get image info
    imageInfo = Connection.getImageInfoById(id=imageId)
    if (dbFound(result=imageInfo)):
        caption = f"{imageInfo['creatorName']} - {imageInfo['imageName']} - {imageInfo['yearStr']}"
        # Edit image capture
        bot.edit_message_caption(chat_id=message.from_user.id, message_id=messageId, caption=caption)
    else:
        log(str=f'{ibotModifyImageCapture.__name__}: Cannot get image info for {imageId}', logLevel=LOG_ERROR)

def ibotShowQuestionType2(bot:telebot.TeleBot,message:types.Message, gameId, gameType = 2) -> None:
    # Get gameInfo
    gameInfo = Connection.getGameInfoById(id=gameId)
    complexity = gameInfo['complexity']
    imageId = gameInfo['question']
    # Get image URL
    url = Connection.getImageUrlById(id=imageId)
    # Get answer options
    imageInfo = Connection.getImageInfoById(id=imageId)
    finished = (gameInfo['result'] != None)
    if (finished):
        bot.send_message(chat_id=message.from_user.id, text='Игра уже сыграна. Пожалуйста, начните новую.')
        return
    # Show image
    bot.send_photo(chat_id=message.from_user.id, photo=url)
    textQuestion = guess_image.getTextQuestion(gameInfo=gameInfo)
    if (gameType == 2): # Show answer options
        creatorId = imageInfo['creatorId']
        creatorName = imageInfo['creatorName']

        # Get year range for creators
        yearRange = guess_image.getCreatorByImageYearRange(intYear=imageInfo['intYear'])
        log(str=f'Range = {yearRange}', logLevel=LOG_DEBUG)
        creators = Connection.getNCreators(
            n=CREATORS_IN_TYPE2_ANSWER,
            exclude=creatorId,
            complexity=complexity,
            range=yearRange)
        creators.append({'creatorId':creatorId,'creatorName':creatorName})
        shuffle(creators)
        log(str=creators,logLevel=LOG_DEBUG)
        # Show buttons with answer options
        keyboard = types.InlineKeyboardMarkup()
        for i in range(0, len(creators)): # 2 because we start with 1 + correct creator
            creatorId = creators[i].get('creatorId')
            creatorName = creators[i].get('creatorName')
            data = f'{IBOT_TYPE2_ANSWER}{creatorId}'
            key = types.InlineKeyboardButton(text=creatorName, callback_data=data)
            keyboard.add(key)

        bot.send_message(chat_id=message.from_user.id, text=textQuestion, reply_markup=keyboard)
    else: # game type == 3
        bot.send_message(chat_id=message.from_user.id, text=textQuestion)

def ibotShowQuestionType3(bot:telebot.TeleBot,message, gameId) -> None:
    return ibotShowQuestionType2(bot=bot, message=message, gameId=gameId, gameType=3)


def ibotCheckAnswerGameType3(userCreatorName:str, correctCreatorName:str) -> bool:
    # 1. Convern both strings to the same format
    userCreatorName = userCreatorName.lower() # Convert to lower
    correctCreatorName = correctCreatorName.lower()
    userCreatorName = userCreatorName.replace('ё','е') # Replace 'ё'
    correctCreatorName = correctCreatorName.replace('ё','е') # Replace 'ё'
    correctCreatorName = correctCreatorName.replace('й','й') # Replace 'й'

    # 0. Full match
    if (userCreatorName == correctCreatorName):
        log(str=f'Full match: {userCreatorName} == {correctCreatorName}',logLevel=LOG_DEBUG)
        return True

    lU = len(userCreatorName)
    lC = len(correctCreatorName)
    # 2. Check length of userAnswer
    if (lU > lC):
        log(str=f'User len > correct len: {lU} > {lC}',logLevel=LOG_DEBUG)
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
                log(str=f'Full last word match (len <=3): {userAnswerLastWord} == {correctAnswerLastWord}',logLevel=LOG_DEBUG)
                return True
        else:
            # Check len difference
            lAlw = len(userAnswerLastWord)
            lClw = len(correctAnswerLastWord)
            if (abs(lAlw-lClw) <= 2):
                # Check similarity for last name
                ret = isStrSimilar(str1=userAnswerLastWord, str2=correctAnswerLastWord)
                if (ret):
                    log(str=f'Last word similarity match (similarity={ret}): {userAnswerLastWord} | {correctAnswerLastWord}',logLevel=LOG_DEBUG)
                    return True

    if (lU > 5):
        correctAnswer = correctCreatorName[-lU:]
        ret = isStrSimilar(str1=userCreatorName, str2=correctAnswer)
        if (ret):
            log(str=f'Last part of answer similarity (similarity={ret}): {userCreatorName} | {correctAnswer}',logLevel=LOG_DEBUG)
            return True

    # 4. Check Levenstein similarity for full answer
    ret = isStrSimilar(str1=userCreatorName, str2=correctCreatorName)
    if (ret):
        log(str=f'Full answer similarity (similarity={ret}: {userCreatorName} | {correctCreatorName}',logLevel=LOG_DEBUG)
        return True
    return ret

def ibotPhotoHandle(bot:telebot.TeleBot, userName, telegramid, file_info:telegram.File) -> bool:
    fName = ibotPhotoHandle.__name__
    log(str=f'{fName}: Photo handling is started')
    downloaded_file = bot.download_file(file_path=file_info.file_path)
    # Get image info from DB
    text = Connection.getCurrentImageInfo(userName=userName)
    if (text is None):
        log(str=f'{fName}: Cannot get image info from DB',logLevel=LOG_ERROR)
        bot.send_message(chat_id=telegramid, text='Не найдена информация о картине')
        return False

    # Clear image info in DB
    Connection.clearCurrentImageInfo(userName=userName)

    #text = adjustText(text=text)
    info = parseCreatorAndImageInfo(text=text)
    if (info is None):
        log(str=f'{fName}: Cannot parse creator and image data from "{text}"',logLevel=LOG_ERROR)
        bot.send_message(chat_id=telegramid, text='Неверный формат информации о картине')
        return False
    creatorName = info[0]
    imageName = info[1]
    year = info[2]
    intYear = info[3]
    # Check if such creator and image is already in DB
    creatorId = Connection.getCreatorIdByName(creator=creatorName)
    createPerson = False
    if (dbFound(result=creatorId)):
        imageId = Connection.getImageIdByCreatorId(creatorId=creatorId, image=imageName, year=year)
        if (dbFound(result=imageId)):
            errorMsg = f'Image does already exist: {creatorName} - {imageName} - {intYear}'
            bot.send_message(chat_id=telegramid, text=errorMsg)
            log(str=f'{fName}: {errorMsg}',logLevel=LOG_ERROR)
            return False
    else: # New person
        createPerson = True
    imageFileName = buildImgLocalFileName(creator=creatorName, name=imageName, year=year)
    imageFilePath = getBotImagePath() + imageFileName
    imageFileNameNoExtension = buildImgName(creator=creatorName,name=imageName,year=year)
    # Check that file doesn't exist
    if (path.exists(path=imageFilePath)):
        errorMsg = f'Duplicate file found. Cannot proceed. Image file name: {imageFileNameNoExtension}'
        log(str=f'{fName}: {errorMsg}',logLevel=LOG_WARNING)
        bot.send_message(chat_id=telegramid, text=errorMsg)
        return False
    # Save image file
    with open(file=imageFilePath, mode='wb') as new_file:
        new_file.write(downloaded_file)
    log(str=f'{fName}: Saved file - {imageFileNameNoExtension}')
    bot.send_message(chat_id=telegramid, text=f'Картина "{imageFileNameNoExtension}" сохранена')

    orient = getImageOrientation(file=imageFilePath)
    log(str=f'{fName}: Saved file - {imageFilePath}')
    # Handle file
    messageToUser = f'Image file saved: {imageFileNameNoExtension}'
    # Save to S3
    imageS3FileName = buildImgS3FileName(creator=creatorName, name=imageName, year=year)
    ret = uploadImg(imgName=imageS3FileName)
    if (ret != 0):
        errorMsg = f'Cannot upload image to S3 {imageFileName}. Returned: {ret}'
        log(str=f'{fName}:{errorMsg}', logLevel=LOG_ERROR)
        bot.send_message(chat_id=telegramid, text=f'Cannot upload file to S3: {imageFileNameNoExtension}')
        return False
    # Create new person
    if (createPerson):
        res = Connection.insertCreator(creator=creatorName)
        if (not res):
            errorMsg = f'Cannot create creator {creatorName}'
            log(str=f'{fName}:{errorMsg}', logLevel=LOG_ERROR)
            bot.send_message(chat_id=telegramid, text=errorMsg)
            return False
        creatorId = Connection.getCreatorIdByName(creator=creatorName)
        messageToUser = messageToUser + "\n" f'New creator created: {creatorName}'
    # Create image
    res = Connection.insertImage(creatorId=creatorId,image=imageName,year=year,intYear=intYear,orientation=orient)
    if (not res):
        errorMsg = f'Cannot create image {imageFileNameNoExtension}'
        log(str=f'{fName}:{errorMsg}', logLevel=LOG_ERROR)
        bot.send_message(chat_id=telegramid, text=errorMsg)
        # Delete inserted Creator
        if (createPerson):
            Connection.deleteCreator(creatorId=creatorId)
        return False
    messageToUser = messageToUser + "\n" + f'New image created {imageFileNameNoExtension}'
    bot.send_message(chat_id=telegramid, text=messageToUser)
    return True
