import telebot
from db_lib import *
from game_lib import *
from gibot_lib import *
from log_lib import *
import requests


TESTCONNECTION = isTestDB()
TESTBOT = isTestBot()

botToken = getBotToken(TESTBOT)
if (not botToken):
    print(f'Cannot read ENV vars: botToken={botToken}')
    exit()
bot = telebot.TeleBot(botToken)

# Message handler
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    #bot.send_message(message.from_user.id, f'{message.from_user.username}')
    # Check if there is cmd
    if (message.text[0] == '/'):
        return cmdHandler(message)
    elif (ibotCheckGameTypeNInProgress(bot, message, gameType=3)):
        return gameType3AnswerHanderl(bot, message)
    bot.send_message(message.from_user.id, 'Я вас не понимаю:(.')
    bot.send_message(message.from_user.id, ibotGetHelpMessage(message.from_user.username))

def cmdHandler(message):
    if message.text == CMD_START:
        ret = startHandler(message)
        #bot.send_message(message.from_user.id, ret)
    elif message.text == CMD_SETTINGS:
        settings(message)
    elif message.text == CMD_HELP:
        bot.send_message(message.from_user.id, ibotGetHelpMessage(message.from_user.username))
    else:
        bot.send_message(message.from_user.id, "Неизвестная команда.")
        bot.send_message(message.from_user.id, ibotGetHelpMessage(message.from_user.username))

@bot.callback_query_handler(func=lambda message: message.data == CMD_START)
def startHandler(message: types.Message):
    startNewGame(message)

@bot.callback_query_handler(func=lambda message: message.data == CMD_SETTINGS)
def settingsHandler(message: types.Message):
    settings(message)

@bot.callback_query_handler(func=lambda message: message.data == CMD_HELP)
def helpHandler(message: types.Message):
    bot.send_message(message.from_user.id, ibotGetHelpMessage(message.from_user.username))

def settings(message: types.Message):
    ibotRequestComplexity(bot, message)

@bot.callback_query_handler(func=lambda message: re.match(fr'^{IBOT_COMPLEXITY_ANSWER}\d+$', message.data))
def complexityHanderl(message: types.Message):
    # Check user name format first
    if (not ibotCheckUserName(bot, message)):
        return
    userName = message.from_user.username
    complexity = int(message.data.split(':')[1])
    if (not dbLibCheckGameComplexity(complexity)):
        bot.send_message(message.from_user.id, text='Нет такой сложности. Попробуйте еще раз.')
        ibotRequestComplexity(bot, message)
        return
    # Set complexity for the user
    ret = Connection.updateUserComplexity(userName, complexity)
    if (not ret):
        bot.send_message(message.from_user.id, 'Произошла ошибка. Попробуйте позже.')
        return
    # Request Game Type setting
    ibotRequestGameType(bot, message)

@bot.callback_query_handler(func=lambda message: re.match(fr'^{IBOT_GAMETYPE_ANSWER}\d+$', message.data))
def gameTypeHanderl(message: types.Message):
    # Check user name format first
    if (not ibotCheckUserName(bot, message)):
        return
    userName = message.from_user.username
    gameType = int(message.data.split(':')[1])
    if (not dbLibCheckGameType(gameType)):
        bot.send_message(message.from_user.id, text='Нет такого типа. Попробуйте еще раз.')
        ibotRequestGameType(bot, message)
        return
    # Set game type for the user
    ret = Connection.updateUserGameType(userName, gameType)
    if (not ret):
        bot.send_message(message.from_user.id, 'Не получилось изменить тип игры. Попробуйте позже.')
        return
    # Success message
    bot.send_message(message.from_user.id, 'Настройки изменены успешно!')
    key1 = types.InlineKeyboardButton(text='Начать новую игру', callback_data=CMD_START)
    key2= types.InlineKeyboardButton(text='Выбрать другой тип игры/сложность', callback_data=CMD_SETTINGS)
    keyboard = types.InlineKeyboardMarkup(); # keyboard
    keyboard.add(key1)
    keyboard.add(key2)
    question = 'Что дальше?'
    bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)

def startNewGame(message: types.Message):
    userName = message.from_user.username
    # Check user name format first
    if (not dbLibCheckUserName(userName)):
        bot.send_message(
            message.from_user.id,
            text=f'Неверный формат имени пользователя {userName} - простите, но у вас не получится поиграть. Попробуйте позже.'
        )
        return
    check = ibotIsUserExist(userName)
    # Check that user exist
    if (not check):
        # Register new user
        ret = ibotUserRegister(userName)
        if (not ret):
            bot.send_message(message.from_user.id, "Регистрация пользователя невозможна - извините.")
            return
        # Show welcome messages
        welcome = ibotGetWelcomeMessage(userName)
        bot.send_message(message.from_user.id, welcome)
    # Get game type and complexity
    gameType = Connection.getUserGameType(userName)
    complexity = Connection.getUserComplexity(userName)
    # Generate new game for the complexity
    params={
        'user':userName,
        'type':gameType,
        'complexity':complexity
    }
    gameId = guess_image.generateNewGame(params)
    ibotShowQuestion(bot, message, gameType, gameId)

@bot.callback_query_handler(func=lambda message: re.match(fr'^{IBOT_TYPE2_ANSWER}\d+$', message.data))
def gameType2AnswerHanderl(message: types.Message):
    userName = message.from_user.username
    # Check user name format first
    if (not ibotCheckUserName(bot, message)):
        return
    creatorId = int(message.data.split(':')[1])
    # Get current game
    gameId = Connection.getCurrentGame(userName)
    if (not gameId):
        bot.send_message(message.from_user.id, text=f'Нет запущенных игр. Введите "{CMD_START}" чтобы начать новую.')
        return

    # Finish game and return result
    guess_image.finishGame(userName, gameId, creatorId)
    # Get game info
    gameInfo = Connection.getGameInfoById(gameId)
    # Check result
    result = gameInfo['result']
    # Get correct answer
    correctAnswerId = gameInfo.get('correct_answer')
    correctAnswer = Connection.getCreatorNameById(correctAnswerId)
    creatorInfo = Connection.getCreatorInfoById(correctAnswerId)
    writeForm = ""
    if (dbFound(creatorInfo)):
        if (dbIsWoman(creatorInfo['gender'])):
            writeForm = 'а'
    correctMessage = f'Эту картину написал{writeForm} {correctAnswer}.'
    ibotShowGameResult(bot=bot, message=message, result=result, correctAnswer=correctAnswer, correctMessage=correctMessage)

def gameType3AnswerHanderl(bot, message: types.Message):
    userName = message.from_user.username
    # Check user name format first
    if (not ibotCheckUserName(bot, message)):
        return
    # Get current game
    gameId = Connection.getCurrentGame(userName)
    if (not gameId):
        bot.send_message(message.from_user.id, text=f'Нет запущенных игр. Введите "{CMD_START}" чтобы начать новую.')
        return

    # User answer
    userCreatorName = message.text
    # Get game info
    gameInfo = Connection.getGameInfoById(gameId)
    # Get correct answer - creatorId from DB
    correctAnswerId = gameInfo.get('correct_answer')
    correctAnswer = Connection.getCreatorNameById(correctAnswerId)
    answer = 0

    if (ibotCheckAnswerGameType3(userCreatorName, correctAnswer)):
        answer = correctAnswerId # User is correct

    # Finish game and return result
    guess_image.finishGame(userName, gameId, answer)
    # Check result
    # Get game info to update result
    gameInfo = Connection.getGameInfoById(gameId)
    result = gameInfo['result']
    creatorInfo = Connection.getCreatorInfoById(correctAnswerId)
    writeForm = ""
    if (dbFound(creatorInfo)):
        if (dbIsWoman(creatorInfo['gender'])):
            writeForm = 'а'
    correctMessage = f'Эту картину написал{writeForm} {correctAnswer}.'
    ibotShowGameResult(bot=bot, message=message, result=result, correctAnswer=correctAnswer, correctMessage=correctMessage)

@bot.callback_query_handler(func=lambda message: re.match(fr'^{IBOT_TYPE1_ANSWER}\d+$', message.data))
def gameType1AnswerHanderl(message: types.Message):
    fName = gameType1AnswerHanderl.__name__
    userName = message.from_user.username
    # Check user name format first
    ret = ibotCheckUserName(bot, message)
    if (not ret):
        return
    imageId = int(message.data.split(':')[1])
    # Get current game
    gameId = Connection.getCurrentGame(userName)
    if (not gameId):
        bot.send_message(message.from_user.id, text='Нет запущенных игр. Введите "/start" чтобы начать новую.')
        return
    # Get question info
    gameInfo = Connection.getGameInfoById(gameId)
    answerOptions = guess_image.getQuestionType1Options(gameInfo)
    correctAnswerNum = None
    if (answerOptions):
        correctAnswerNum = ibotFindNumOfType1Answer(answerOptions, gameInfo['correct_answer'])
    imageIds = guess_image.getQuestionType1Options(gameInfo)
    if (not imageIds):
        log(f'{fName}: wrong format of imageIds = {imageIds}', LOG_ERROR)
        bot.send_message(message.from_user.id, "Произошла ошибка. Пожалуйста начните новую игру")
        return

    # Get image messages ids
    mIdsTxt = Connection.getCurrentGameData(userName)
    mIds = guess_image.getMessageIds(mIdsTxt)
    ibotModifyImageCaptures(bot, message, mIds, imageIds)

    # Finish game and return result
    guess_image.finishGame(userName, gameId, imageId)
    # Get game info
    gameInfo = Connection.getGameInfoById(gameId)
    # Check result
    result = gameInfo['result']
    correctAnswerId = gameInfo.get('correct_answer')
    correctAnswer = Connection.getImageInfoById(correctAnswerId).get('imageName')
    correctMessage = f'Это картина "{correctAnswer}"'
    ibotShowGameResult(bot=bot, message=message, result=result, correctAnswer=correctAnswer,
                       correctMessage=correctMessage, correctAnswerNum=correctAnswerNum)

# Show game result
def ibotShowGameResult(bot, message, result, correctAnswer, correctMessage='', correctAnswerNum=None):
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
    
    ibotSendAfterAnswer(bot, message)

#===============
# Main section
#---------------
def main():
    initLog()
    Connection.initConnection(test=TESTCONNECTION)
    while(True):
        try:
            bot.infinity_polling()
        except KeyboardInterrupt:
            log('Exiting by user request')
            break
        except requests.exceptions.ReadTimeout as error:
            log(f'main: exception: {error}', LOG_ERROR)
            continue
    Connection.closeConnection()
    closeLog()

if __name__ == "__main__":
    main()
