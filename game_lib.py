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

    IMAGERANGEDIFF = 51
    CREATORRANGEDIFF = 40

    # Get range for image search
    # Returns:
    #   (startYear, endYear) - start, end years for image creation
    def getImageCreationRange(intYear):
        return (intYear - guess_image.IMAGERANGEDIFF, intYear + guess_image.IMAGERANGEDIFF)

    # Get range for creator seatch by image year
    # Returns:
    #   (startYear, endYear) - start, end years for image creation
    def getCreatorByImageYearRange(intYear):
        return (intYear - 2*guess_image.CREATORRANGEDIFF, intYear + 2*guess_image.IMAGERANGEDIFF)

    # Get range for creator search
    # Returns:
    #   (None,None) - cannot detirmine
    #   (startYear, endYear) - start, end years for creator
    def getCreatorYearRange(creatorBirth, creatorDeath):
        # return nothing if neither birth nor death provided
        if (not creatorBirth and not creatorDeath):
            return (None,None)
        middleYear = 0
        if (creatorBirth and not creatorDeath):
            middleYear = creatorBirth + guess_image.CREATORRANGEDIFF
        elif (creatorDeath and not creatorBirth):
            middleYear = creatorDeath - guess_image.CREATORRANGEDIFF
        else:
            middleYear = int((creatorDeath - creatorBirth)/2)
        return (middleYear-2*guess_image.CREATORRANGEDIFF, middleYear+2*guess_image.CREATORRANGEDIFF)

    # Analize params and understand which page to show next
    def getPageToShow(queryParams):
        user = queryParams.get('user')
        if (not user): # No user
            return guess_image.LOGIN_PAGE # Login page
        userId = Connection.getUserIdByName(name=user)
        if (userId is None):
            # error in db
            return guess_image.LOGIN_PAGE
        elif (dbNotFound(result=userId)):
            # No such user yet
            return guess_image.LOGIN_PAGE
        # User exist
        if (queryParams.get('list_all')!=None or queryParams.get('list_unfinished')!=None or queryParams.get('list_finished')!=None):
            return guess_image.GAME_LIST_PAGE # Game list

        if (not queryParams.get('game')):
            if (not queryParams.get('type') or not queryParams.get('complexity')):
                return guess_image.GAME_TYPE_PAGE # Game type choose
            else:
                ret1 = dbLibCheckGameType(game_type=queryParams.get('type'))
                ret2 = dbLibCheckGameComplexity(game_type=queryParams.get('complexity'))
                if (ret1 and ret2):
                    return guess_image.NEW_GAME_PAGE
                else:
                    return guess_image.GAME_TYPE_PAGE # Wrong game_type
        # game id passed
        gameId = queryParams.get('game')
        ret = dbLibCheckGameId(game_id=gameId)
        if (not ret): # incorrect game id
            return guess_image.GAME_TYPE_PAGE
        
        gameInfo = Connection.getGameInfoById(id=gameId)
        if (ret == gameInfo): # error with DB
            return guess_image.GAME_TYPE_PAGE
        if (dbNotFound(result=gameInfo)): # cannot find game - return to game type screen
            return guess_image.GAME_TYPE_PAGE
        
        # Game exist in DB
        # Check user <-> game connectoin
        gameUserId = gameInfo['user']
        if (userId != gameUserId):
            log(str=f'ERROR: getPageToShow: user <-> game mismatch ({user}<->{gameId})',logLevel=LOG_ERROR)
            return guess_image.GAME_TYPE_PAGE

        if (not queryParams.get('answer')):
            return guess_image.QUESTION_PAGE
        else:
            # Check answer format
            ret = dbLibCheckAnswer(answer=queryParams.get('answer'))
            if (ret):
                return guess_image.ANSWER_PAGE # Question screen
            else: # answer format is invalid
                return guess_image.QUESTION_PAGE

    # Show page login
    def pageLogin(queryParams) -> str:
        userName = queryParams.get('user')
        error = ''
        if userName:
            error = showError(error=f'User "{userName}" not found')
        baseUrl = getBaseUrl()
        log(str=f'Login page invoked',logLevel=LOG_DEBUG)
        return error+showLoginPage(baseUrl=baseUrl)

    # Show new user page
    def pageNewUser(queryParams):
        log(str=f'New user page invoked',logLevel=LOG_DEBUG)
        return showNewUserPage()

    # Show page to choose game type
    def pageGameType(queryParams) -> str:
        log(str=f'Game type page invoked',logLevel=LOG_DEBUG)
        errMsg = ''
        gameId = queryParams.get('game')
        if (gameId): # 'game' parameter is present - it is incorrect one
            ret = dbLibCheckGameId(game_id=gameId) # Check gameId format
            if (not ret): # incorrect game id
                errMsg = showError(error=f'Wrong game format: {gameId}. Please start new one.')
            else:
                ret = Connection.getGameInfoById(id=gameId)
                if (ret is None): # error with DB
                    errMsg = showError(error='Error with DB occured. Please try again later.')
                if (dbNotFound(result=ret)): # cannot find game
                    errMsg = showError(error='Unknown game. Please start new one.')
        elif (queryParams.get('type') is not None): # "game_type is present"
            ret = dbLibCheckGameType(game_type=queryParams.get('type')) # Check format
            if (not ret):
                errMsg = showError(error='Incorrect game type "{ret}". Please start new game.')

        game_types = Connection.getGameTypes()        
        return errMsg + showGameTypePage(params=queryParams, game_types=game_types)

    # Generate new game.
    # Returns:
    #   None - if error
    #   id - new game id
    def generateNewGame(queryParams):
        ret = None
        game_type = queryParams.get('type')
        game_complexity = queryParams.get('complexity')
        if (not dbLibCheckGameType(game_type=game_type)):
            log(str=f'ERROR: generateNewGame: game type is incorect ({game_type})',logLevel=LOG_ERROR)
            return None
        if (not dbLibCheckGameComplexity(game_type=game_complexity)):
            log(str=f'ERROR: generateNewGame: game complexity is incorect ({game_complexity})',logLevel=LOG_ERROR)
            return None
        game_type = int(game_type)
        if (game_type == 1):
            ret = guess_image.generateNewGame1(queryParams=queryParams)
        elif (game_type == 2):
            ret = guess_image.generateNewGame2(queryParams=queryParams)
        elif (game_type == 3):
            ret = guess_image.generateNewGame3(queryParams=queryParams)
        else:
            log(str=f'ERROR: generateNewGame: unknown game type {game_type}',logLevel=LOG_ERROR)
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

    # Get random creator and ramdom image of this creator
    # Returns:
    #   (creatorId, imageId) - tuple with ids
    #   None - in case of any errors
    def getRandomCreatorAndImageId(complexity):
        fName = guess_image.getRandomCreatorAndImageId.__name__
       # Get random creator
        ret = Connection.getRandomCreatorIds(complexity=complexity)
        if (ret is None):
            log(str=f'{fName}: Cannoe get random creator: DB issue',logLevel=LOG_ERROR)
            return None
        elif (dbNotFound(result=ret)):
            log(str=f'{fName}: Cannot get random creator: creator not found',logLevel=LOG_ERROR)
            return None  
        creatorId = ret[0]
        # Get random image of the creator
        ret = Connection.getRandomImageIdsOfCreator(creatorId=creatorId)
        if (ret == None):
            log(str=f'{fName}: Cannot get random image of creator {creatorId}: DB issue',logLevel=LOG_ERROR)
            return None
        elif (dbNotFound(result=ret)):
            log(str=f'{fName}: Cannot get random image of creator {creatorId}: image not found',logLevel=LOG_ERROR)
            return None
        imageId = ret[0]
        return (creatorId, imageId)

    # Generate new game with type 1: guess image of the creator
    # Returns:
    #   None - is any error
    #   gameId - id of new game
    def generateNewGame1(queryParams):
        fName = guess_image.generateNewGame1.__name__
        complexity = queryParams.get('complexity')
        if (not complexity):
            log(str=f'ERROR: {fName}: Cannot get complexity: {queryParams}',logLevel=LOG_ERROR)
            return None
        complexity = int(complexity)
        ret = guess_image.getRandomCreatorAndImageId(complexity=complexity)
        if (not ret):
            return None # Error message is printed in getRandom function
        creatorId = ret[0]
        imageId = ret[1]
        # Get year range for other images
        imageInfo = Connection.getImageInfoById(id=imageId)
        yearRange = (None, None)
        if (dbFound(result=imageInfo)):
            yearRange = guess_image.getImageCreationRange(intYear=imageInfo['intYear'])
        # Get 3 random images where creator is not the same
        otherImageIds = Connection.getRandomImageIdsOfOtherCreators(
            creatorId=creatorId,
            complexity=complexity, 
            n=guess_image.GAME2NUMBEROFOPTIONS,
            range=yearRange)
        if (dbNotFound(result=otherImageIds) or len(otherImageIds) != guess_image.GAME2NUMBEROFOPTIONS):
            log(str=f'{fName}: Cannot get random {guess_image.GAME2NUMBEROFOPTIONS} images of creator other than {creatorId}',logLevel=LOG_ERROR)
            return None
        userName = queryParams['user']
        userId = Connection.getUserIdByName(name=userName)
        if (userId is None or dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot get user id by name {userName}',logLevel=LOG_ERROR)
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
        ret = Connection.insertGame(user_id=userId, game_type=gameType, correct_answer=imageId, question=question, complexity=complexity)
        if (ret is None):
            log(str=f'{fName}: Cannot insert game u={userName},gt={gameType},q={question},ca={imageId}',logLevel=LOG_ERROR)
            return None
        else:
            # Set current_game
            Connection.setCurrentGame(userName=userName, gameId=ret)
        return ret

    # Generate new game with type 2 or 3 (if gameType is set): guess creator of the image
    # Returns:
    #   None - is any error
    #   gameId - id of new game
    def generateNewGame2(queryParams, gameType = 2):
        fName = guess_image.generateNewGame2.__name__
        userName = queryParams['user']
        userId = Connection.getUserIdByName(name=userName)
        if (userId == None or dbNotFound(result=userId)):
            log(str=f'ERROR: {fName}: Cannot get user id by name {userName}',logLevel=LOG_ERROR)
            return None
        # Check game type
        if (gameType != 2 and gameType != 3):
            log(str=f'ERROR: {fName}: Incorrect game type provided: {gameType}',logLevel=LOG_ERROR)
            return None
        complexity = int(queryParams['complexity'])
        if (not complexity):
            log(str=f'ERROR: {fName}: Cannot get complexity: {queryParams}',logLevel=LOG_ERROR)
            return None
        newGameId = guess_image.getRandomCreatorAndImageId(complexity=complexity)
        if (not newGameId):
            return None # Error message is printed in getRandom function
        creatorId = newGameId[0]
        imageId = newGameId[1]
        # Get image info
        imageInfo = Connection.getImageInfoById(id=imageId)
        if (dbNotFound(result=imageInfo)):
            log(str=f'ERROR: {fName}: Cannot get random image info (image id = {imageId})',logLevel=LOG_ERROR)
            return None
        gameType = queryParams['type']
        # Generate game with user, type(2-3), question(image id), correct_answer (creator_id), complexity
        newGameId = Connection.insertGame(user_id=userId,game_type=gameType,correct_answer=creatorId,question=imageId,complexity=complexity)
        if (newGameId is None):
            log(str=f'ERROR: {fName}: Cannot insert game u={userName},gt={gameType},q={imageId},ca={creatorId}',logLevel=LOG_ERROR)
            return None
        else:
            # Set current_game
            Connection.setCurrentGame(userName=userName, gameId=newGameId)
        return newGameId

    # Generate new game with type 3: guess creator of the image - no variants
    # Returns:
    #   None - is any error
    #   gameId - id of new game
    def generateNewGame3(queryParams):
        return guess_image.generateNewGame2(queryParams, gameType=3)

    # New game creation and question page to show
    def pageNewGame(queryParams) -> str:
        log(str=f'New game page invoked',logLevel=LOG_DEBUG)
        errMsg = ''
        ret = guess_image.generateNewGame(queryParams=queryParams)
        if (ret is None):
            errMsg = 'Cannot create new game. Issue with DB.'
            return showErrorPage(error=errMsg)

        queryParams['game'] = ret
        return guess_image.pageQuestion(queryParams=queryParams)

    # Get text question
    def getTextQuestion(gameInfo) -> str:
        gameType = int(gameInfo['type'])
        textQ = "Default text question"
        if gameType == 1: # Type = 1
            imageInfo = Connection.getImageInfoById(id=gameInfo['correct_answer'])
            if (dbFound(result=imageInfo)):
                creatorInfo = Connection.getCreatorInfoById(creatorId=imageInfo['creatorId'])
                writeForm = ""
                if (dbFound(result=creatorInfo)):
                    if (dbIsWoman(gender=creatorInfo['gender'])):
                        writeForm = 'а'
                textQ = f"Какую картину написал{writeForm} \"{imageInfo['creatorName']}\"?"
        elif (gameType == 2):
            imageInfo = Connection.getImageInfoById(id=gameInfo['question'])
            if (dbFound(result=imageInfo)):
                textQ = f"Кто написал картину \"{imageInfo['imageName']}\" в {imageInfo['yearStr']}?"
        else: # Type = 3
            imageInfo = Connection.getImageInfoById(id=gameInfo['question'])
            if (dbFound(result=imageInfo)):
                textQ = f"Кто написал картину \"{imageInfo['imageName']}\" в {imageInfo['yearStr']}?"
        return textQ

    # Show question page
    def pageQuestion(queryParams, errMsg1 = '') -> str:
        log(str=f'Question page invoked',logLevel=LOG_DEBUG)
        # Get game from DB
        gameId = queryParams.get('game')
        gameInfo = Connection.getGameInfoById(id=gameId)
        if (gameInfo is None):
            errMsg = 'Cannot get game. Issue with DB.'
            return showErrorPage(error=errMsg)
        if (dbNotFound(result=gameInfo)):
            errMsg = 'Cannot get game. No game found.'
            return showErrorPage(error=errMsg)
        # Game was found
        # Check user <-> game connectoin
        userName = queryParams.get('user')
        userId = Connection.getUserIdByName(name=userName)
        gameUserId = gameInfo['user']
        if (userId != gameUserId):
            errMsg = showError(error=f'user <-> game mismatch ({userName}<->{gameId})')
            del queryParams['game']
            return errMsg + guess_image.pageGameType(queryParams=queryParams)

        # Get text question
        textQuestion = guess_image.getTextQuestion(gameInfo=gameInfo)

        # Show question page
        return errMsg1 + showQuestionPage(params=queryParams, gameInfo=gameInfo, textQuestion=textQuestion)

    # Show game list page
    def pageGameList(queryParams) -> str:
        log(str=f'Game list page invoked',logLevel=LOG_DEBUG)
        userName = queryParams.get('user')
        userId = Connection.getUserIdByName(name=userName)
        if (dbNotFound(result=userId)):
            log(str=f'ERROR: pageGameList: Cannot get user id by name {userName}',logLevel=LOG_ERROR)
            errMsg = f'Cannot find user {userName}'
            return showErrorPage(error=errMsg)
        games = []
        list_type = ''
        if (queryParams.get('list_all')!=None):
            games = Connection.getAllGamesList(userId=userId)
            list_type = '"all"'
        elif (queryParams.get('list_finished')!=None):
            games = Connection.getFinishedGamesList(userId=userId)
            list_type = '"finished"'
        elif (queryParams.get('list_unfinished')!=None):
            games = Connection.getUnfinishedGamesList(userId=userId)
            list_type = '"unfinished"'
        else:
            errMsg = f'Strange thing happend - cannot find list option for user {userName}'
            return showErrorPage(error=errMsg)
        return showListPage(params=queryParams, games=games, list_type=list_type)

    # Finish game
    # Returns: True/False
    def finishGame(userName, gameId, answer) -> bool:
        ret =  Connection.finishGame(gameId=gameId, answer=answer)
        if (not ret):
            return False
        # Clear current game
        Connection.clearCurrentGame(userName=userName)
        Connection.clearCurrentGameData(userName=userName)
        return True

    # Check answer and return question page
    def pageAnswer(queryParams):
        userName = queryParams.get('user')
        gameId = queryParams.get('game')
        gameInfo = Connection.getGameInfoById(id=gameId)
        if (dbNotFound(result=gameInfo)):
            err = showError(error=f'Cannot find game {gameId}')
            return err + showGameTypePage(params=queryParams)
        try:
            answer = int(queryParams.get('answer'))
        except:
            log(str=f"Passed not int answer",logLevel=LOG_ERROR)
            return guess_image.pageQuestion(queryParams=queryParams)
        ret = guess_image.finishGame(userName=userName, gameId=gameId, answer=answer)
        if ret:
            gameInfo = Connection.getGameInfoById(id=gameId)
            if (dbNotFound(result=gameInfo)):
                err = showError(error=f'Cannot find game {gameId}')
                return err + showGameTypePage(params=queryParams)
            ret = guess_image.pageQuestion(queryParams=queryParams) # Result page
        else:
            err = showError(error=f'Cannot apply answer for game {gameId}. Please try again.')
            ret = guess_image.pageQuestion(queryParams=queryParams,errMsg1=err)
        return ret

    # Entry point for game
    def entryPoint(method, queryParams):
        ret = "Error - something wrong happended"
        newUser = queryParams.get('newuser')
        registerUser = queryParams.get('registeruser')
        userName = queryParams.get('user')
        if (newUser is not None): # Register page
            ret = guess_image.pageNewUser(queryParams=queryParams)
        elif (registerUser is not None): # Create new user
            if (not userName):
                errMsg = showError(error="Need to pass user name")
                ret = errMsg + guess_image.pageLogin(queryParams=queryParams)
            else:
                # New User registragion
                if (not checkUserNameFormat(user=userName)):
                    errMsg = showError(error='Username must conatin letters and digits only started wtih letter')
                    ret = errMsg + guess_image.pageNewUser(queryParams=queryParams)
                else:
                    # Add new user
                    result = Connection.insertUser(userName=userName)
                    if (not result):
                        errMsg = showError(error=f"Something wrong with user {userName} registration. Please try again.")
                        ret = errMsg + guess_image.pageNewUser(queryParams=queryParams)
                    else:
                        # User registration successful
                        # Return game type page
                        ret = guess_image.pageGameType(queryParams=queryParams)
        else: # Other actions
            ret = guess_image.getNextPage(queryParams=queryParams)
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
        page = guess_image.getPageToShow(queryParams=queryParams)
        result = routes[page](queryParams)
        return result
