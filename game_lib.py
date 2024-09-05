from guess_image_lib import *
from db_lib import *
from img_ui_lib import *

class guess_image:
    LOGIN_PAGE = 0
    GAME_TYPE_PAGE = 1
    QUESTION_PAGE = 2
    GAME_LIST_PAGE = 3
    NEW_GAME_PAGE = 4
    ANSWER_PAGE = 5
    NEW_USER_PAGE = 6

    GAME2NUMBEROFOPTIONS = 3

    # Analize params and understand which page to show next
    def getPageToShow(queryParams):
        user = queryParams.get('user')
        if (not user): # No user
            return guess_image.LOGIN_PAGE # Login page
        userId = Connection.getUserIdByName(user)
        if (userId == None):
            # error in db
            return guess_image.LOGIN_PAGE
        elif (dbNotFound(userId)):
            # No such user yet
            return guess_image.LOGIN_PAGE
        # User exist
        if (queryParams.get('list_all')!=None or queryParams.get('list_unfinished')!=None or queryParams.get('list_finished')!=None):
            return guess_image.GAME_LIST_PAGE # Game list

        if (not queryParams.get('game')):
            if (not queryParams.get('type') or not queryParams.get('complexity')):
                return guess_image.GAME_TYPE_PAGE # Game type choose
            else:
                ret1 = dbLibCheckGameType(queryParams.get('type'))
                ret2 = dbLibCheckGameComplexity(queryParams.get('complexity'))
                if (ret1 and ret2):
                    return guess_image.NEW_GAME_PAGE
                else:
                    return guess_image.GAME_TYPE_PAGE # Wrong game_type
        # game id passed
        gameId = queryParams.get('game')
        ret = dbLibCheckGameId(gameId)
        if (not ret): # incorrect game id
            return guess_image.GAME_TYPE_PAGE
        
        gameInfo = Connection.getGameInfoById(gameId)
        if (ret == gameInfo): # error with DB
            return guess_image.GAME_TYPE_PAGE
        if (dbNotFound(gameInfo)): # cannot find game - return to game type screen
            return guess_image.GAME_TYPE_PAGE
        
        # Game exist in DB
        # Check user <-> game connectoin
        gameUserId = gameInfo['user']
        if (userId != gameUserId):
            print(f'ERROR: getPageToShow: user <-> game mismatch ({user}<->{gameId})')
            return guess_image.GAME_TYPE_PAGE

        if (not queryParams.get('answer')):
            return guess_image.QUESTION_PAGE
        else:
            # Check answer format
            ret = dbLibCheckAnswer(queryParams.get('answer'))
            if (ret):
                return guess_image.ANSWER_PAGE # Question screen
            else: # answer format is invalid
                return guess_image.QUESTION_PAGE

    # Show page login
    def pageLogin(queryParams):
        userName = queryParams.get('user')
        error = ''
        if userName:
            error = showError(f'User "{userName}" not found')
        baseUrl = getBaseUrl()
        debug(f'Login page invoked')
        return error+showLoginPage(baseUrl)

    # Show new user page
    def pageNewUser(queryParams):
        debug(f'New user page invoked')
        return showNewUserPage()

    # Show page to choose game type
    def pageGameType(queryParams):
        debug(f'Game type page invoked')
        errMsg = ''
        gameId = queryParams.get('game')
        if (gameId): # 'game' parameter is present - it is incorrect one
            ret = dbLibCheckGameId(gameId) # Check gameId format
            if (not ret): # incorrect game id
                errMsg = showError(f'Wrong game format: {gameId}. Please start new one.')
            else:
                ret = Connection.getGameInfoById(gameId)
                if (ret == None): # error with DB
                    errMsg = showError('Error with DB occured. Please try again later.')
                if (dbNotFound(ret)): # cannot find game
                    errMsg = showError('Unknown game. Please start new one.')
        elif (queryParams.get('type')!=None): # "game_type is present"
            ret = dbLibCheckGameType(queryParams.get('type')) # Check format
            if (not ret):
                errMsg = showError('Incorrect game type "{ret}". Please start new game.')

        game_types = Connection.getGameTypes()        
        return errMsg + showGameTypePage(queryParams, game_types)

    # Generate new game.
    # Returns:
    #   None - if error
    #   id - new game id
    def generateNewGame(queryParams):
        ret = None
        game_type = queryParams.get('type')
        game_complexity = queryParams.get('complexity')
        if (not dbLibCheckGameType(game_type)):
            print(f'ERROR: generateNewGame: game type is incorect ({game_type})')
            return None
        if (not dbLibCheckGameComplexity(game_complexity)):
            print(f'ERROR: generateNewGame: game complexity is incorect ({game_complexity})')
            return None
        game_type = int(game_type)
        if (game_type == 1):
            ret = guess_image.generateNewGame1(queryParams)
        elif (game_type == 2):
            ret = guess_image.generateNewGame2(queryParams)
        else:
            print(f'ERROR: generateNewGame: unknown game type {game_type}')
        return ret

    # Extract game type 1 question options
    # Returns:
    #   [id1, ...] - GAME2NUMBEROFOPTIONS image ids
    #   None - if any error
    def getQuestionType1Options(gameInfo):
        imageIds = []
        question = gameInfo['question']
        for item in question.split(' '):
            imageIds.append(int(item))
        if (len(imageIds) != guess_image.GAME2NUMBEROFOPTIONS + 1): # +1 correct answer
            return None
        return imageIds

    # Extract message ids for images
    # Returns:
    #   [id1, ...] - GAME2NUMBEROFOPTIONS message ids
    #   None - if any error
    def getMessageIds(mIdsTxt):
        mIds = []
        for item in mIdsTxt.split(' '):
            mIds.append(int(item))
        if (len(mIds) != guess_image.GAME2NUMBEROFOPTIONS + 1): # +1 correct answer
            return None
        return mIds

    # Generate new game with type 1: guess image of the creator
    # Returns:
    #   None - is any error
    #   gameId - id of new game
    def generateNewGame1(queryParams):
        complexity = int(queryParams.get('complexity'))
       # Get random creator
        ret = Connection.getRandomCreatorIds(complexity)
        if (ret == None):
            print(f'ERROR: generateNewGame1: Cannoe get random creator: DB issue')
            return None
        elif (dbNotFound(ret)):
            print(f'ERROR: generateNewGame1: Cannot get random creator: creator not found')
            return None  
        creatorId = ret[0]
        # Get random image of the creator
        ret = Connection.getRandomImageIdsOfCreator(creatorId)
        if (ret == None):
            print(f'ERROR: generateNewGame1: Cannot get random image of creator {creatorId}: DB issue')
            return None
        elif (dbNotFound(ret)):
            print(f'ERROR: generateNewGame1: Cannot get random image of creator {creatorId}: image not found')
            return None
        imageId = ret[0]
        # Get 3 random images where creator is not the same
        otherImageIds = Connection.getRandomImageIdsOfOtherCreators(creatorId, complexity, guess_image.GAME2NUMBEROFOPTIONS)
        if (dbNotFound(otherImageIds) or len(otherImageIds) != guess_image.GAME2NUMBEROFOPTIONS):
            print(f'ERROR: generateNewGame1: Cannot get random {guess_image.GAME2NUMBEROFOPTIONS} images of creator other than {creatorId}')
            return None
        userName = queryParams['user']
        userId = Connection.getUserIdByName(userName)
        if (userId == None or dbNotFound(userId)):
            print(f'ERROR: generateNewGame1: Cannot get user id by name {userName}')
            return None
        gameType = queryParams['type']
        questionIds = []
        for i in otherImageIds:
            questionIds.append(i[0]) # it is array of arrays
        questionIds.append(imageId)
        # Shuffle it
        shuffle(questionIds)
        question = " ".join(str(i) for i in questionIds)
        # Generate game with user, type(1), correct_answer (correct_image_id), question(image ids)
        ret = Connection.insertGame(userId, gameType, imageId, question, complexity)
        if (ret == None):
            print(f'ERROR: generateNewGame1: Cannot insert game u={userName},gt={gameType},q={question},ca={imageId}')
            return None
        else:
            # Set current_game
            Connection.setCurrentGame(userName, ret)
        return ret

    # Generate new game with type 2: guess creator of the image
    # Returns:
    #   None - is any error
    #   gameId - id of new game
    def generateNewGame2(queryParams):
        complexity = int(queryParams['complexity'])
        # Get random image info
        imageId = Connection.getRandomImageIdsOfAnyCreator(complexity, 1) # get 1 image
        if (dbNotFound(imageId)):
            print(f'ERROR: generateNewGame2: Cannot get random image')
            return None
        # Get image info
        imageInfo = Connection.getImageInfoById(imageId)
        if (dbNotFound(imageInfo)):
            print(f'ERROR: generateNewGame2: Cannot get random image info (image id = {imageId})')
            return None
        userName = queryParams['user']
        userId = Connection.getUserIdByName(userName)
        if (userId == None or dbNotFound(userId)):
            print(f'ERROR: generateNewGame2: Cannot get user id by name {userName}')
            return None
        gameType = queryParams['type']
        creatorId = imageInfo['creatorId']
        # Generate game with user, type(2), question(image id), correct_answer (creator_id)
        ret = Connection.insertGame(userId,gameType,creatorId,imageId,complexity)
        if (ret == None):
            print(f'ERROR: generateNewGame2: Cannot insert game u={userName},gt={gameType},q={imageId},ca={creatorId}')
            return None
        else:
            # Set current_game
            Connection.setCurrentGame(userName, ret)
        return ret

    # New game creation and question page to show
    def pageNewGame(queryParams):
        debug(f'New game page invoked')
        errMsg = ''
        ret = guess_image.generateNewGame(queryParams)
        if (ret == None):
            errMsg = 'Cannot create new game. Issue with DB.'
            return showErrorPage(errMsg)

        queryParams['game'] = ret
        return guess_image.pageQuestion(queryParams)

    # Get text question
    def getTextQuestion(gameInfo):
        gameType = int(gameInfo['type'])
        textQ = "Default text question"

        if gameType == 1: # Type = 1
            imageInfo = Connection.getImageInfoById(gameInfo['correct_answer'])
            if (dbFound(imageInfo)):
                textQ = f"Какую картину написал \"{imageInfo['creatorName']}\" в {imageInfo['yearStr']}?"
        else: # Type = 2
            imageInfo = Connection.getImageInfoById(gameInfo['question'])
            if (dbFound(imageInfo)):
                textQ = f"Кто написал картину \"{imageInfo['imageName']}\" в {imageInfo['yearStr']}?"
        return textQ

    # Show question page
    def pageQuestion(queryParams, errMsg1 = ''):
        debug(f'Question page invoked')
        # Get game from DB
        gameId = queryParams.get('game')
        gameInfo = Connection.getGameInfoById(gameId)
        if (gameInfo == None):
            errMsg = 'Cannot get game. Issue with DB.'
            return showErrorPage(errMsg)
        if (dbNotFound(gameInfo)):
            errMsg = 'Cannot get game. No game found.'
            return showErrorPage(errMsg)
        # Game was found
        # Check user <-> game connectoin
        userName = queryParams.get('user')
        userId = Connection.getUserIdByName(userName)
        gameUserId = gameInfo['user']
        if (userId != gameUserId):
            errMsg = showError(f'user <-> game mismatch ({userName}<->{gameId})')
            del queryParams['game']
            return errMsg + guess_image.pageGameType(queryParams)

        # Get text question
        textQuestion = guess_image.getTextQuestion(gameInfo)

        # Show question page
        return errMsg1 + showQuestionPage(queryParams, gameInfo, textQuestion)

    # Show game list page
    def pageGameList(queryParams):
        debug(f'Game list page invoked')
        userName = queryParams.get('user')
        userId = Connection.getUserIdByName(userName)
        if (dbNotFound(userId)):
            print(f'ERROR: pageGameList: Cannot get user id by name {userName}')
            errMsg = f'Cannot find user {userName}'
            return showErrorPage(errMsg)

        games = []
        list_type = ''
        if (queryParams.get('list_all')!=None):
            games = Connection.getAllGamesList(userId)
            list_type = '"all"'
        elif (queryParams.get('list_finished')!=None):
            games = Connection.getFinishedGamesList(userId)
            list_type = '"finished"'
        elif (queryParams.get('list_unfinished')!=None):
            games = Connection.getUnfinishedGamesList(userId)
            list_type = '"unfinished"'
        else:
            errMsg = f'Strange thing happend - cannot find list option for user {userName}'
            return showErrorPage(errMsg)
        return showListPage(queryParams, games, list_type)

    # Finish game
    # Returns: True/False
    def finishGame(userName, gameId, answer):
        ret =  Connection.finishGame(gameId, answer)
        if (not ret):
            return False
        # Clear current game
        Connection.clearCurrentGame(userName)
        Connection.clearCurrentGameData(userName)
        return True

    # Check answer and return question page
    def pageAnswer(queryParams):
        userName = queryParams.get('user')
        gameId = queryParams.get('game')
        gameInfo = Connection.getGameInfoById(gameId)
        if (dbNotFound(gameInfo)):
            err = showError(f'Cannot find game {gameId}')
            return err + showGameTypePage(queryParams)
        try:
            answer = int(queryParams.get('answer'))
        except:
            print(f"Passed not int answer")
            return guess_image.pageQuestion(queryParams)
        ret = guess_image.finishGame(userName, gameId, answer)
        if ret:
            gameInfo = Connection.getGameInfoById(gameId)
            if (dbNotFound(gameInfo)):
                err = showError(f'Cannot find game {gameId}')
                return err + showGameTypePage(queryParams)
            ret = guess_image.pageQuestion(queryParams) # Result page
        else:
            err = showError(f'Cannot apply answer for game {gameId}. Please try again.')
            ret = guess_image.pageQuestion(queryParams,err)
        return ret

    # Entry point for game
    def entryPoint(method, queryParams):
        ret = "Error - something wrong happended"
        newUser = queryParams.get('newuser')
        registerUser = queryParams.get('registeruser')
        userName = queryParams.get('user')
        if (newUser != None): # Register page
            ret = guess_image.pageNewUser(queryParams)
        elif (registerUser != None): # Create new user
            if (not userName):
                errMsg = showError("Need to pass user name")
                ret = errMsg + guess_image.pageLogin(queryParams)
            else:
                # New User registragion
                if (not checkUserNameFormat(userName)):
                    errMsg = showError('Username must conatin letters and digits only started wtih letter')
                    ret = errMsg + guess_image.pageNewUser(queryParams)
                else:
                    # Add new user
                    result = Connection.insertUser(userName)
                    if (not result):
                        errMsg = showError(f"Something wrong with user {userName} registration. Please try again.")
                        ret = errMsg + guess_image.pageNewUser(queryParams)
                    else:
                        # User registration successful
                        # Return game type page
                        ret = guess_image.pageGameType(queryParams)
        else: # Other actions
            ret = guess_image.getNextPage(queryParams)
        return ret

    def getNextPage(queryParams):
        # Function array
        routes = [guess_image.pageLogin,
                  guess_image.pageGameType,
                  guess_image.pageQuestion,
                  guess_image.pageGameList,
                  guess_image.pageNewGame,
                  guess_image.pageAnswer,
                  guess_image.pageNewUser]
        page = guess_image.getPageToShow(queryParams)
        result = routes[page](queryParams)
        return result
