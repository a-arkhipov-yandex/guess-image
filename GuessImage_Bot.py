import telebot
from db_lib import *
from game_lib import *
from gibot_lib import *
from log_lib import *
import requests


TESTCONNECTION = isTestDB()
TESTBOT = isTestBot()

botToken = getBotToken(test=TESTBOT)
if (not botToken):
    print(f'Cannot read ENV vars: botToken={botToken}')
    exit()
bot = telebot.TeleBot(token=botToken)

# Message handler
@bot.message_handler(content_types=['text'])
def get_text_messages(message) -> None:
    # Check if there is cmd
    if (message.text[0] == '/'):
        return cmdHandler(message=message)
    elif (ibotCheckGameTypeNInProgress(bot=bot, message=message, gameType=3)):
        return gameType3AnswerHanderl(bot=bot, message=message)
    bot.send_message(chat_id=message.from_user.id, text='Я вас не понимаю:(.')
    bot.send_message(chat_id=message.from_user.id, text=ibotGetHelpMessage(userName=message.from_user.username))

def cmdHandler(message) -> None:
    if message.text == CMD_START:
        ret = startNewGame(message=message)
        #bot.send_message(message.from_user.id, ret)
    elif message.text == CMD_SETTINGS:
        settings(message=message)
    elif message.text == CMD_HELP:
        bot.send_message(chat_id=message.from_user.id, text=ibotGetHelpMessage(userName=message.from_user.username))
    else:
        bot.send_message(chat_id=message.from_user.id, text="Неизвестная команда.")
        bot.send_message(chat_id=message.from_user.id, text=ibotGetHelpMessage(userName=message.from_user.username))

@bot.callback_query_handler(func=lambda message: message.data == CMD_START)
def startHandler(message: types.CallbackQuery) -> None:
    bot.answer_callback_query(callback_query_id=message.id)
    startNewGame(message=message)

@bot.callback_query_handler(func=lambda message: message.data == CMD_SETTINGS)
def settingsHandler(message: types.CallbackQuery) -> None:
    bot.answer_callback_query(callback_query_id=message.id)
    settings(message=message)

@bot.callback_query_handler(func=lambda message: message.data == CMD_HELP)
def helpHandler(message: types.CallbackQuery) -> None:
    bot.answer_callback_query(callback_query_id=message.id)
    bot.send_message(chat_id=message.from_user.id, text=ibotGetHelpMessage(userName=message.from_user.username))

def settings(message: types.Message) -> None:
    ibotRequestComplexity(bot=bot, message=message)

@bot.callback_query_handler(func=lambda message: re.match(fr'^{IBOT_COMPLEXITY_ANSWER}\d+$', message.data))
def complexityHanderl(message: types.CallbackQuery) -> None:
    bot.answer_callback_query(callback_query_id=message.id)
    # Check user name format first
    if (not ibotCheckUserName(bot=bot, message=message)):
        bot.send_message(chat_id=message.from_user.id, text="Произошла ошибка.")
        return
    userName = message.from_user.username
    complexity = int(message.data.split(sep=':')[1])
    if (not dbLibCheckGameComplexity(game_type=complexity)):
        bot.send_message(chat_id=message.from_user.id, text='Нет такой сложности. Попробуйте еще раз.')
        ibotRequestComplexity(bot=bot, message=message)
        return
    # Set complexity for the user
    ret = Connection.updateUserComplexity(userName=userName, complexity=complexity)
    if (not ret):
        bot.send_message(chat_id=message.from_user.id, text='Произошла ошибка. Попробуйте позже.')
        return
    # Request Game Type setting
    ibotRequestGameType(bot=bot, message=message)

@bot.callback_query_handler(func=lambda message: re.match(fr'^{IBOT_GAMETYPE_ANSWER}\d+$', message.data))
def gameTypeHanderl(message: types.CallbackQuery) -> None:
    bot.answer_callback_query(callback_query_id=message.id)
    # Check user name format first
    if (not ibotCheckUserName(bot=bot, message=message)):
        bot.send_message(chat_id=message.from_user.id, text="Произошла ошибка.")
        return
    userName = getUserByMessage(message=message)
    gameType = int(message.data.split(sep=':')[1])
    if (not dbLibCheckGameType(game_type=gameType)):
        bot.send_message(chat_id=message.from_user.id, text='Нет такого типа. Попробуйте еще раз.')
        ibotRequestGameType(bot=bot, message=message)
        return
    # Set game type for the user
    ret = Connection.updateUserGameType(userName=userName, gameType=gameType)
    if (not ret):
        bot.send_message(chat_id=message.from_user.id, text='Не получилось изменить тип игры. Попробуйте позже.')
        return
    # Success message
    bot.send_message(chat_id=message.from_user.id, text='Настройки изменены успешно!')
    key1 = types.InlineKeyboardButton(text='Начать новую игру', callback_data=CMD_START)
    key2= types.InlineKeyboardButton(text='Выбрать другой тип игры/сложность', callback_data=CMD_SETTINGS)
    keyboard = types.InlineKeyboardMarkup(); # keyboard
    keyboard.add(key1)
    keyboard.add(key2)
    question = 'Что дальше?'
    bot.send_message(chat_id=message.from_user.id, text=question, reply_markup=keyboard)

def startNewGame(message: types.Message) -> None:
    userName = getUserByMessage(message=message)
    check = ibotIsUserExist(userName=userName)
    # Check that user exist
    if (not check):
        # Register new user
        ret = ibotUserRegister(userName=userName)
        if (not ret):
            bot.send_message(chat_id=message.from_user.id, text="Регистрация пользователя невозможна - извините.")
            return
        # Show welcome messages
        welcome = ibotGetWelcomeMessage(userName=userName)
        bot.send_message(chat_id=message.from_user.id, text=welcome)
    # Get game type and complexity
    gameType = Connection.getUserGameType(userName=userName)
    complexity = Connection.getUserComplexity(userName=userName)
    # Generate new game for the complexity
    params={
        'user':userName,
        'type':gameType,
        'complexity':complexity
    }
    gameId = guess_image.generateNewGame(queryParams=params)
    ibotShowQuestion(bot=bot, message=message, type=gameType, gameId=gameId)

@bot.callback_query_handler(func=lambda message: re.match(fr'^{IBOT_TYPE2_ANSWER}\d+$', message.data))
def gameType2AnswerHanderl(message: types.CallbackQuery) -> None:
    userName = getUserByMessage(message=message)
    bot.answer_callback_query(callback_query_id=message.id)
    # Check user name format first
    if (not ibotCheckUserName(bot=bot, message=message)):
        bot.send_message(chat_id=message.from_user.id, text="Произошла ошибка.")
        return
    creatorId = int(message.data.split(sep=':')[1])
    # Get current game
    gameId = Connection.getCurrentGame(userName=userName)
    if (not gameId):
        bot.send_message(chat_id=message.from_user.id, text=f'Нет запущенных игр. Введите "{CMD_START}" чтобы начать новую.')
        return

    # Finish game and return result
    guess_image.finishGame(userName=userName, gameId=gameId, answer=creatorId)
    # Get game info
    gameInfo = Connection.getGameInfoById(id=gameId)
    # Check result
    result = gameInfo['result']
    # Get correct answer
    correctAnswerId = gameInfo.get('correct_answer')
    correctAnswer = Connection.getCreatorNameById(creatorId=correctAnswerId)
    creatorInfo = Connection.getCreatorInfoById(creatorId=correctAnswerId)
    writeForm = ""
    if (dbFound(result=creatorInfo)):
        if (dbIsWoman(gender=creatorInfo['gender'])):
            writeForm = 'а'
    correctMessage = f'Эту картину написал{writeForm} {correctAnswer}.'
    ibotShowGameResult(bot=bot, message=message, result=result, correctAnswer=correctAnswer, correctMessage=correctMessage)

def gameType3AnswerHanderl(bot, message: types.Message) -> None:
    userName = getUserByMessage(message=message)
    # Check user name format first
    if (not ibotCheckUserName(bot=bot, message=message)):
        bot.send_message(chat_id=message.from_user.id, text="Произошла ошибка.")
        return
    # Get current game
    gameId = Connection.getCurrentGame(userName=userName)
    if (not gameId):
        bot.send_message(message.from_user.id, text=f'Нет запущенных игр. Введите "{CMD_START}" чтобы начать новую.')
        return

    # User answer
    userCreatorName = message.text
    # Get game info
    gameInfo = Connection.getGameInfoById(id=gameId)
    # Get correct answer - creatorId from DB
    correctAnswerId = gameInfo.get('correct_answer')
    correctAnswer = Connection.getCreatorNameById(creatorId=correctAnswerId)
    answer = 0

    if (ibotCheckAnswerGameType3(userCreatorName=userCreatorName, correctCreatorName=correctAnswer)):
        answer = correctAnswerId # User is correct

    # Finish game and return result
    guess_image.finishGame(userName=userName, gameId=gameId, answer=answer)
    # Check result
    # Get game info to update result
    gameInfo = Connection.getGameInfoById(id=gameId)
    result = gameInfo['result']
    creatorInfo = Connection.getCreatorInfoById(creatorId=correctAnswerId)
    writeForm = ""
    if (dbFound(creatorInfo)):
        if (dbIsWoman(creatorInfo['gender'])):
            writeForm = 'а'
    correctMessage = f'Эту картину написал{writeForm} {correctAnswer}.'
    ibotShowGameResult(bot=bot, message=message, result=result, correctAnswer=correctAnswer, correctMessage=correctMessage)

@bot.callback_query_handler(func=lambda message: re.match(fr'^{IBOT_TYPE1_ANSWER}\d+$', message.data))
def gameType1AnswerHanderl(message: types.CallbackQuery) -> None:
    fName = gameType1AnswerHanderl.__name__
    userName = getUserByMessage(message=message)
    bot.answer_callback_query(callback_query_id=message.id)
    # Check user name format first
    ret = ibotCheckUserName(bot=bot, message=message)
    if (not ret):
        return
    imageId = int(message.data.split(sep=':')[1])
    # Get current game
    gameId = Connection.getCurrentGame(userName=userName)
    if (not gameId):
        bot.send_message(chat_id=message.from_user.id, text='Нет запущенных игр. Введите "/start" чтобы начать новую.')
        return
    # Get question info
    gameInfo = Connection.getGameInfoById(id=gameId)
    answerOptions = guess_image.getQuestionType1Options(gameInfo=gameInfo)
    correctAnswerNum = None
    if (answerOptions):
        correctAnswerNum = ibotFindNumOfType1Answer(imageIds=answerOptions, correctId=gameInfo['correct_answer'])
    imageIds = guess_image.getQuestionType1Options(gameInfo=gameInfo)
    if (not imageIds):
        log(str=f'{fName}: wrong format of imageIds = {imageIds}', logLevel=LOG_ERROR)
        bot.send_message(chat_id=message.from_user.id, text="Произошла ошибка. Пожалуйста начните новую игру")
        return

    # Get image messages ids
    mIdsTxt = Connection.getCurrentGameData(userName=userName)
    mIds = guess_image.getMessageIds(mIdsTxt=mIdsTxt)
    ibotModifyImageCaptures(bot=bot, message=message, mIds=mIds, imageIds=imageIds)

    # Finish game and return result
    guess_image.finishGame(userName=userName, gameId=gameId, answer=imageId)
    # Get game info
    gameInfo = Connection.getGameInfoById(id=gameId)
    # Check result
    result = gameInfo['result']
    correctAnswerId = gameInfo.get('correct_answer')
    correctAnswer = Connection.getImageInfoById(id=correctAnswerId).get('imageName')
    correctMessage = f'Это картина "{correctAnswer}"'
    ibotShowGameResult(bot=bot, message=message, result=result, correctAnswer=correctAnswer,
                       correctMessage=correctMessage, correctAnswerNum=correctAnswerNum)

# Show game result
def ibotShowGameResult(bot, message, result, correctAnswer, correctMessage='', correctAnswerNum=None) -> None:
    # Check result
    correctAnswerTxt = ''
    if (correctAnswerNum):
        correctAnswerTxt = f' под номером {correctAnswerNum}'

    if (result):
        # Answer is correct
        bot.send_message(message.from_user.id, text=f'Поздравляю! Вы ответили верно. {correctMessage}{correctAnswerTxt}')
    else:
        correctAnswerTxt = ''
        if (correctAnswerNum):
            correctAnswerTxt = f' под номером {correctAnswerNum}'

        bot.send_message(message.from_user.id, text=f'А вот и не верно. Верный ответ{correctAnswerTxt}: "{correctAnswer}"')
    
    ibotSendAfterAnswer(bot=bot, message=message)

#===============
# Main section
#---------------
def main() -> None:
    initLog()
    Connection.initConnection(test=TESTCONNECTION)
    while(True):
        try:
            bot.infinity_polling()
        except KeyboardInterrupt:
            log(str='Exiting by user request')
            break
        except requests.exceptions.ReadTimeout as error:
            log(str=f'main: exception: {error}', logLevel=LOG_ERROR)
            continue
    Connection.closeConnection()
    closeLog()

if __name__ == "__main__":
    main()
