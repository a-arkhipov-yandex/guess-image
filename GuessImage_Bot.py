import telebot
from db_lib import *
from game_lib import *
from gibot_lib import *

TESTCONNECTION = False

botToken = getBotToken()
if (not botToken):
    print(f'Cannot read ENV vars: botToken={botToken}')
    exit()
bot = telebot.TeleBot(botToken)
Connection.initConnection(test=TESTCONNECTION)

# Message handler
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    #bot.send_message(message.from_user.id, f'{message.from_user.username}')
    if message.text == "/start":
        ret = startHandler(message)
        #bot.send_message(message.from_user.id, ret)
    elif message.text == "/settings":
        settings(message)
    elif message.text == "/help":
        ret = ibotGetHelpMessage()
        bot.send_message(message.from_user.id, ret)
    else:
        ret = ibotGetHelpMessage()
        bot.send_message(message.from_user.id, "Неизвестная команда.")
        bot.send_message(message.from_user.id, ret)

@bot.callback_query_handler(func=lambda message: message.data == '/start')
def startHandler(message: types.Message):
    startNewGame(message)

@bot.callback_query_handler(func=lambda message: message.data == '/settings')
def settingsHandler(message: types.Message):
    settings(message)

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
        bot.send_message(message.from_user.id, 'Cannot update complexity. Please try again later.')
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
        bot.send_message(message.from_user.id, 'Cannot update game type. Please try again later.')
        return
    # Success message
    bot.send_message(message.from_user.id, 'Настройки изменены успешно!')
    key1 = types.InlineKeyboardButton(text='Начать новую игру', callback_data=f'/start')
    key2= types.InlineKeyboardButton(text='Выбрать другой тип игры/сложность', callback_data=f'/settings')
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
        bot.send_message(message.from_user.id, text='Нет запущенных игр. Введите "/start" чтобы начать новую.')
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
    correctMessage = f'Эту картину написал {correctAnswer}.'
    ibotShowGameResult(bot, message, result, correctAnswer, correctMessage)

@bot.callback_query_handler(func=lambda message: re.match(fr'^{IBOT_TYPE1_ANSWER}\d+$', message.data))
def gameType1AnswerHanderl(message: types.Message):
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
    # Finish game and return result
    guess_image.finishGame(userName, gameId, imageId)
    # Get game info
    gameInfo = Connection.getGameInfoById(gameId)
    # Check result
    result = gameInfo['result']
    correctAnswerId = gameInfo.get('correct_answer')
    correctAnswer = Connection.getImageInfoById(correctAnswerId).get('imageName')
    correctMessage = f'Это картина "{correctAnswer}"'
    ibotShowGameResult(bot, message, result, correctAnswer, correctMessage)

# Show game result
def ibotShowGameResult(bot, message, result, correctAnswer, correctMessage=''):
    # Check result
    if (result):
        # Answer is correct
        bot.send_message(message.from_user.id, text=f'Поздравляю! Вы ответили верно. {correctMessage}')
    else:
        bot.send_message(message.from_user.id, text=f'А вот и не верно. Верный ответ: "{correctAnswer}"')
    key1 = types.InlineKeyboardButton(text='Сыграть еще раз', callback_data=f'/start')
    key2= types.InlineKeyboardButton(text='Выбрать другой тип игры/сложность', callback_data=f'/settings')
    keyboard = types.InlineKeyboardMarkup(); # keyboard
    keyboard.add(key1)
    keyboard.add(key2)
    question = 'Выберите дальнейшее действие:'
    bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)

#===============
# Main section
#---------------
def main():
    bot.polling(none_stop=True, interval=1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\nExiting by user request.\n')
        Connection.closeConnection()
