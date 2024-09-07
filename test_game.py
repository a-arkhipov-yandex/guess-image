from __future__ import annotations
import pytest
from game_lib import *

class TestGame:
    testUserName = "TestGameUser"
    isInitialized = False
    testUserId = None
    unfinishedGameType1Id = None
    unfinishedGameType2Id = None
    finishedGameType1Id = None
    finishedGameType2Id = None
    unfinishedGameType3Id = None
    finishedGameType3Id = None

    def testPreparation(self):
        initLog(printToo=True)
        # Create connection
        if (not Connection.isInitialized()):
            Connection.initConnection(test=True)
        assert(Connection.isInitialized())

        # Create user
        ret = Connection.insertUser(TestGame.testUserName)
        assert(ret)
        TestGame.testUserId = Connection.getUserIdByName(TestGame.testUserName)

        # Create unfinished game type 1
        params = {'user':TestGame.testUserName,'type':1, 'complexity':1}
        gameType1Id = guess_image.generateNewGame1(params)
        currentGame = Connection.getCurrentGame(TestGame.testUserName)
        gameData = Connection.getCurrentGameData(TestGame.testUserName)
        assert(gameType1Id)
        assert(currentGame == gameType1Id)
        assert(gameData == None) # No game data if not bot generated
        TestGame.unfinishedGameType1Id = gameType1Id
        # Create unfinished game type 2
        params = {'user':TestGame.testUserName,'type':2,'complexity':2}
        gameType2Id = guess_image.generateNewGame2(params)
        assert(gameType2Id)
        TestGame.unfinishedGameType2Id = gameType2Id
        # Create unfinished game type 3
        params = {'user':TestGame.testUserName,'type':3,'complexity':3}
        gameType3Id = guess_image.generateNewGame3(params)
        assert(gameType3Id)
        TestGame.unfinishedGameType3Id = gameType3Id

        # Create unfinished game type 1
        params = {'user':TestGame.testUserName,'type':1, 'complexity':1}
        gameType1Id = guess_image.generateNewGame1(params)
        assert(gameType1Id)
        TestGame.finishedGameType1Id = gameType1Id
        # Create unfinished game type 2
        params = {'user':TestGame.testUserName,'type':2, 'complexity':2}
        gameType2Id = guess_image.generateNewGame2(params)
        assert(gameType2Id)
        TestGame.finishedGameType2Id = gameType2Id
        # Create unfinished game type 3
        params = {'user':TestGame.testUserName,'type':3, 'complexity':3}
        gameType3Id = guess_image.generateNewGame3(params)
        assert(gameType3Id)
        TestGame.finishedGameType3Id = gameType3Id

        # Finish game type 1 with True result
        gameType1Info = Connection.getGameInfoById(gameType1Id)
        Connection.finishGame(gameType1Id, gameType1Info.get('correct_answer'))
        # Finish game type 2 with False result
        gameType2Info = Connection.getGameInfoById(gameType2Id)
        Connection.finishGame(gameType2Id, gameType2Info.get('correct_answer')+1)
        # Finish game type 3 with False result
        gameType3Info = Connection.getGameInfoById(gameType3Id)
        Connection.finishGame(gameType3Id, gameType3Info.get('correct_answer'))

        TestGame.isInitialized = True

    # Test loging page
    @pytest.mark.parametrize(
        "params, expected_result",
        [
            ({}, guess_image.LOGIN_PAGE), # testGetPageToShowLoginNoUser
            ({'user': 'nonexisting_user'}, guess_image.LOGIN_PAGE), # testGetPageToShowLoginNonexistingUser
            ({'user': 'Neo'}, guess_image.GAME_TYPE_PAGE), # testGetPageToShowNoGameNoGameType
        ],
    )
    def testGetPageToShowLoginNoUser(self, params, expected_result):
        ret = guess_image.getPageToShow(params)
        assert(ret == expected_result)

    @pytest.mark.parametrize(
        "list, expected_result",
        [
            ('list_all', guess_image.GAME_LIST_PAGE),
            ('list_unfinished', guess_image.GAME_LIST_PAGE),
            ('list_finished', guess_image.GAME_LIST_PAGE),
        ],
    )
    def testGetPageToShowList(self, list, expected_result):
        query_params = {'user':TestGame.testUserName, list:''}
        ret = guess_image.getPageToShow(query_params)
        query_params = {'user':TestGame.testUserName, list:'1'}
        ret2 = guess_image.getPageToShow(query_params)
        assert(ret == expected_result)
        assert(ret2 == expected_result)

    # Check existing user - no game/ check game type param
    @pytest.mark.parametrize(
        "param, complexity, expected_result",
        [
            # Correct
            ('1', '1', guess_image.NEW_GAME_PAGE),
            ('2', '2', guess_image.NEW_GAME_PAGE),
            ('2', '3', guess_image.NEW_GAME_PAGE),
            ('3', '2', guess_image.NEW_GAME_PAGE),
            # Incorrect
            ('4', '2', guess_image.GAME_TYPE_PAGE),
            ('0', '2', guess_image.GAME_TYPE_PAGE),
            ('-1', '2', guess_image.GAME_TYPE_PAGE),
            ('a', '2', guess_image.GAME_TYPE_PAGE),
            ('%', '2', guess_image.GAME_TYPE_PAGE),
            ('', '2', guess_image.GAME_TYPE_PAGE),
            ('1', '5', guess_image.GAME_TYPE_PAGE),
            ('1', '', guess_image.GAME_TYPE_PAGE),
            ('1', 'df', guess_image.GAME_TYPE_PAGE),
            ('1', '-1', guess_image.GAME_TYPE_PAGE),
            ('1', '$', guess_image.GAME_TYPE_PAGE),
            ('1', 'ваыва', guess_image.GAME_TYPE_PAGE),
        ],
    )
    def testGetPageToShowNoGameCheckGameType(self, param, complexity, expected_result):
        query_params = {'user': TestGame.testUserName, 'type':param, 'complexity':complexity}
        ret = guess_image.getPageToShow(query_params)
        assert(ret == expected_result)

    # Check existing user - incorrect game id
    def testGetPageToShowIncorrectGameId(self):
        query_params = {'user': TestGame.testUserName, 'game':'dfd'}
        ret = guess_image.getPageToShow(query_params)
        assert(ret == guess_image.GAME_TYPE_PAGE)

    # Check existing user - no game with id
    def testGetPageToShowIncorrectGameId2(self):
        query_params = {'user': TestGame.testUserName, 'game':'1000000'}
        ret = guess_image.getPageToShow(query_params)
        assert(ret == guess_image.GAME_TYPE_PAGE)

    # Check page to show game
    def testGetPageToShowResultQuestion(self):
        # Test not existing game
        params = {'user':TestGame.testUserName, 'game':'12345678'}
        resNonexistingGame = guess_image.getPageToShow(params)
        
        resQuestionPageUnfinishedGameType1 = False
        resQuestionPageUnfinishedGameType1 = False
        resQuestionPageContentUnfinishedGameType1 = False
        resQuestionPageContentUnfinishedGameType2 = False
        resQuestionPageFinishedGameType1 = False
        resQuestionPageFinishedGameType2 = False
        resQuestionPageContentFinishedGameType1True = False
        resQuestionPageContentFinishedGameType2False = False

        query_params = {'user': TestGame.testUserName, 'game':str(TestGame.unfinishedGameType1Id)}
        resQuestionPageUnfinishedGameType1 = guess_image.getPageToShow(query_params)
        content = guess_image.pageQuestion(query_params)
        resQuestionPageContentUnfinishedGameType1 = (('Result page' not in content) and ('Question type 1 page' in content))
        query_params = {'user': TestGame.testUserName, 'game':str(TestGame.unfinishedGameType2Id)}
        resQuestionPageUnfinishedGameType2 = guess_image.getPageToShow(query_params)
        content = guess_image.pageQuestion(query_params)
        resQuestionPageContentUnfinishedGameType2 = (('Result page' not in content) and ('Question type 2 page' in content))
        query_params = {'user': TestGame.testUserName, 'game':str(TestGame.unfinishedGameType3Id)}
        resQuestionPageUnfinishedGameType3 = guess_image.getPageToShow(query_params)
        content = guess_image.pageQuestion(query_params)
        resQuestionPageContentUnfinishedGameType3 = (('Result page' not in content) and ('Not implemented yet' in content))


        query_params = {'user': TestGame.testUserName, 'game':str(TestGame.finishedGameType1Id)}
        resQuestionPageFinishedGameType1 = guess_image.getPageToShow(query_params)
        content = guess_image.pageQuestion(query_params)
        resQuestionPageContentFinishedGameType1True = (('Result page' in content) and ('Your answer was' not in content))
        query_params = {'user': TestGame.testUserName, 'game':str(TestGame.finishedGameType2Id)}
        resQuestionPageFinishedGameType2 = guess_image.getPageToShow(query_params)
        content = guess_image.pageQuestion(query_params)
        resQuestionPageContentFinishedGameType2False = (('Result page' in content) and ('Your answer was' in content))

        assert(resNonexistingGame == guess_image.GAME_TYPE_PAGE)
        assert(resQuestionPageUnfinishedGameType1 == guess_image.QUESTION_PAGE)
        assert(resQuestionPageUnfinishedGameType2 == guess_image.QUESTION_PAGE)
        assert(resQuestionPageUnfinishedGameType3 == guess_image.QUESTION_PAGE)
        assert(resQuestionPageContentUnfinishedGameType1)
        assert(resQuestionPageContentUnfinishedGameType2)
        assert(resQuestionPageContentUnfinishedGameType3)
        assert(resQuestionPageFinishedGameType1 == guess_image.QUESTION_PAGE)
        assert(resQuestionPageFinishedGameType2 == guess_image.QUESTION_PAGE)
        assert(resQuestionPageContentFinishedGameType1True)
        assert(resQuestionPageContentFinishedGameType2False)

    # Incorrect answer format
    def testGetPageToShowIncorrectAnswerFormat(self):
        query_params = {'user': TestGame.testUserName, 'game':TestGame.unfinishedGameType1Id, 'answer':'dfdf'}
        ret = guess_image.getPageToShow(query_params)
        assert(ret == guess_image.QUESTION_PAGE)

    # Correct answer format
    def testGetPageToShowCorrectAnswerFormat(self):
        query_params = {'user': TestGame.testUserName, 'game':TestGame.unfinishedGameType1Id, 'answer':'1'}
        ret = guess_image.getPageToShow(query_params)
        assert(ret == guess_image.ANSWER_PAGE)

    @pytest.mark.parametrize(
        "params, expected_result",
        [
            ({'user':'Nonexist','type':'1','complexity':1}, None), # game type 1 - nonexisting user
            ({'user':'Nonexist','type':'2','complexity':1}, None), # game type 2 - nonexisting user
            ({'user':'Neo' ,'type':'5','complexity':1}, None), # Incorrect type
            ({'user':'Neo'}, None), # No type
            ({'user':'Neo','type':1},None), # No complexity
            ({'user':'Neo','type':1,'complexity':10},None), # Incorrect complexity
        ],
    )
    def testGenerateNewGame12IncorrectValues(self, params, expected_result):
        assert(guess_image.generateNewGame(params) == expected_result)

    @pytest.mark.parametrize(
        "game_type, expected_result",
        [
            ('1', True), # game type 1
            ('2', True), # game type 2
            ('3', True), # game type 3
        ],
    )
    def testGenerateNewGame123CorrectValues(self, game_type, expected_result):
        resNewGame = False
        resCheckInsertedGame = False
        params = {'user':TestGame.testUserName,'type':game_type, 'complexity':1}
        ret = guess_image.generateNewGame(params)
        if (ret != None):
            resNewGame = True
            # Check that game is created
            ret2 = Connection.getGameInfoById(ret)
            if (dbFound(ret2)):
                # Delete game
                Connection.deleteGame(ret2['id'])
                resCheckInsertedGame = True
        assert(resNewGame == expected_result)
        assert(resCheckInsertedGame == expected_result)

    def testPageLogin(self):
        ret = guess_image.pageLogin({})
        resNoUser = ((not 'class="error"' in ret) and ('Login' in ret))
        ret = guess_image.pageLogin({'user':'qwerasd'})
        resNonexistingUser = ('User "qwerasd" not found' in ret)
        assert(resNoUser)
        assert(resNonexistingUser)

    def testPageNewUser(self):
        ret = guess_image.pageNewUser({})
        resNewUserPage = ('Create new user' in ret)
        assert(resNewUserPage)

    def testPageGameType(self):
        ret = guess_image.pageGameType({'user':TestGame.testUserName}) # Show game type page
        resGoodCase = (('Game Type page:' in ret) and (not 'class="error"' in ret))
        ret = guess_image.pageGameType({'user':TestGame.testUserName,'game':'1000000'}) # No game exist
        resNoGameExist = (('Game Type page:' in ret) and ('Unknown game.' in ret))
        ret = guess_image.pageGameType({'user':TestGame.testUserName,'game':'fdsfds'}) # Wrong game format
        resWrongGameFormat = (('Game Type page:' in ret) and ('Wrong game format:' in ret))

        ret = guess_image.pageGameType({'user':TestGame.testUserName,'type':'50'}) # Wrong game type format - big number
        resWrongGameTypeFormat1 = (('Game Type page:' in ret) and ('Incorrect game type' in ret))
        ret = guess_image.pageGameType({'user':TestGame.testUserName,'type':'dfdsf'}) # Wrong game type format - text s
        resWrongGameTypeFormat2 = (('Game Type page:' in ret) and ('Incorrect game type' in ret))
        ret = guess_image.pageGameType({'user':TestGame.testUserName,'type':''}) # Wrong empty game type
        resWrongGameTypeFormat3 = (('Game Type page:' in ret) and ('Incorrect game type' in ret))

        assert(resGoodCase)
        assert(resNoGameExist)
        assert(resWrongGameFormat)
        assert(resWrongGameTypeFormat1)
        assert(resWrongGameTypeFormat2)
        assert(resWrongGameTypeFormat3)

    def testPageQuestion(self):
        resNonexistingGame = False
        resUnfinishedGame = False
        resFinishedGame = False
        resUnfinishedGameWrongUser = False
        resFinishedGameWrongUser = False

        # Test not existing game
        ret = guess_image.pageQuestion({'user':TestGame.testUserName,'game':'200000'})
        resNonexistingGame = ('No game found' in ret)

        # Test unfinished page
        ret = guess_image.pageQuestion({'user':TestGame.testUserName,'game':TestGame.unfinishedGameType2Id})
        resUnfinishedGame = ('Question type 2 page' in ret)
        # Test unfinished page - wrong user
        ret = guess_image.pageQuestion({'user':'Neo','game':TestGame.unfinishedGameType2Id})
        resUnfinishedGameWrongUser = (('Game Type page' in ret) and ('class="error"' in ret))

        # Test finished page
        ret = guess_image.pageQuestion({'user':TestGame.testUserName,'game':TestGame.finishedGameType1Id})
        resFinishedGame = ('Result page' in ret)

        # Test finished game - wrong user
        ret = guess_image.pageQuestion({'user':'Neo','game':TestGame.finishedGameType2Id})
        resFinishedGameWrongUser = (('Game Type page' in ret) and ('class="error"' in ret))

        assert(resNonexistingGame)
        assert(resUnfinishedGame)
        assert(resFinishedGame)
        assert(resUnfinishedGameWrongUser)
        assert(resFinishedGameWrongUser)

    def testPageList(self):
        resNonexistingUser = False
        resUnFinishedGamesList = False
        resFinishedGamesList = False
        resAllGamesList = False
        resNoListParam = False
        
        # Test not existing user
        ret = guess_image.pageGameList({'user':'Nonexistin_user','list_all':'1'})
        resNonexistingUser = ('Cannot find user' in ret)

        # Test unfinished games list
        ret = guess_image.pageGameList({'user':TestGame.testUserName,'list_unfinished':'1'})
        resUnFinishedGamesList = ('List games page' in ret)

        # Test finished games list
        ret = guess_image.pageGameList({'user':TestGame.testUserName,'list_finished':'1'})
        resFinishedGamesList = ('List games page' in ret)

        # Test all games list
        ret = guess_image.pageGameList({'user':TestGame.testUserName,'list_all':'1'})
        resAllGamesList = ('List games page' in ret)

        # Test not existing list_option
        ret = guess_image.pageGameList({'user':TestGame.testUserName,'list_other':'1'})
        resNoListParam = ('cannot find list option' in ret)

        # Create user
        testUserName = "TestListUser1"
        Connection.insertUser(testUserName)
        testUserId = Connection.getUserIdByName(testUserName)

        # Test game lists for new user (must be 0 for all list_types)
        qp = {'user':testUserName,'list_all':''}
        ret = guess_image.pageGameList(qp)
        resListAllNoGames = ('No games found' in ret)
        qp = {'user':testUserName,'list_unfinished':''}
        ret = guess_image.pageGameList(qp)
        resListUnfinishedNoGames = ('No games found' in ret)
        qp = {'user':testUserName,'list_finished':''}
        ret = guess_image.pageGameList(qp)
        resListFinishedNoGames = ('No games found' in ret)

        # Create game
        tmpGameId = Connection.insertGame(testUserId,1,1,1,1)
        resListAllUnfinishedGame = False
        resListFinishedUnfinishedGame = False
        resListFinishedUnfinishedGame = False
        resListAllFinishedGame = False
        resListUnfinishedFinishedGame = False
        resListFinishedFinishedGame = False
        if tmpGameId:
            # Test game lists (must be 1 for all and unfinished and 0 for finished)
            qp = {'user':testUserName,'list_all':''}
            ret = guess_image.pageGameList(qp)
            resListAllUnfinishedGame = ('</table>' in ret)
            qp = {'user':testUserName,'list_unfinished':''}
            ret = guess_image.pageGameList(qp)
            resListUnfinishedUnfinishedGame = ('</table>' in ret)
            qp = {'user':testUserName,'list_finished':''}
            ret = guess_image.pageGameList(qp)
            resListFinishedUnfinishedGame = ('No games found' in ret)
            # Finish game
            Connection.finishGame(tmpGameId, True)
            # Test game lists (must be 1 for all and finished and 0 for unfinished)
            qp = {'user':testUserName,'list_all':''}
            ret = guess_image.pageGameList(qp)
            resListAllFinishedGame = ('</table>' in ret)
            qp = {'user':testUserName,'list_unfinished':''}
            ret = guess_image.pageGameList(qp)
            resListUnfinishedFinishedGame = ('No games found' in ret)
            qp = {'user':testUserName,'list_finished':''}
            ret = guess_image.pageGameList(qp)
            resListFinishedFinishedGame = ('</table>' in ret)

            # Delete game
            Connection.deleteGame(tmpGameId)
        # Delete user
        Connection.deleteUser(testUserId)

        assert(resNonexistingUser)
        assert(resUnFinishedGamesList)
        assert(resFinishedGamesList)
        assert(resAllGamesList)
        assert(resNoListParam)
        assert(resListAllNoGames)
        assert(resListUnfinishedNoGames)
        assert(resListFinishedNoGames)
        assert(resListAllUnfinishedGame)
        assert(resListUnfinishedUnfinishedGame)
        assert(resListFinishedUnfinishedGame)
        assert(resListAllFinishedGame)
        assert(resListUnfinishedFinishedGame)
        assert(resListFinishedFinishedGame)

    # Test New Game Page
    def testPageNewGame(self):
        # Test new game type 1
        params = {'user':TestGame.testUserName, 'type':1, 'complexity':1}
        ret = guess_image.pageNewGame(params)
        resNewGameType1 = ("Question type 1 page" in ret)

        # Test new game type 2
        params = {'user':TestGame.testUserName, 'type':2,'complexity':1}
        ret = guess_image.pageNewGame(params)
        resNewGameType2 = ("Question type 2 page" in ret)

        assert(resNewGameType1)
        assert(resNewGameType2)

    # Test entry point
    def testEntryPointNewUser(self):
        params = {'newuser':1}
        ret = guess_image.entryPoint('get', params)
        resNewUser = (('Create new user' in ret) and (not 'class="error"' in ret))
        assert(resNewUser)

    # Test entry point
    def testEntryPointRegisterUser(self):
        params = {'registeruser':1}
        ret = guess_image.entryPoint('get', params)
        resNoUserName = (('Create new user') and ('Need to pass user name' in ret))
        userName = 'TestUser123'
        params = {'registeruser':1, 'user':userName}
        ret = guess_image.entryPoint('get', params)
        resUserRegistered = (('Game Type page' in ret) and (not 'class="error"' in ret))
        # Remove user
        ret = Connection.getUserIdByName(userName)
        resUserRegistered2 = True
        if (dbFound):
            Connection.deleteUser(ret)
        else:
            resUserRegistered2 = False
        assert(resNoUserName)
        assert(resUserRegistered)
        assert(resUserRegistered2)

    def testCleanUp(self):
        # Delete unfinished games
        resDeleteGame1 = Connection.deleteGame(TestGame.unfinishedGameType1Id)
        assert(resDeleteGame1)
        resDeleteGame2 = Connection.deleteGame(TestGame.unfinishedGameType2Id)
        assert(resDeleteGame2)
        resDeleteGame3 = Connection.deleteGame(TestGame.unfinishedGameType3Id)
        assert(resDeleteGame3)

        # Delete finished games
        resDeleteGame4 = Connection.deleteGame(TestGame.finishedGameType1Id)
        assert(resDeleteGame4)
        resDeleteGame5 = Connection.deleteGame(TestGame.finishedGameType2Id)
        assert(resDeleteGame5)
        resDeleteGame6 = Connection.deleteGame(TestGame.finishedGameType3Id)
        assert(resDeleteGame6)
        # Delete test user - do not delete user as it has games left
        #resDeleteUser = Connection.deleteUser(TestGame.testUserId)
        #assert(resDeleteUser)
        # Close connection
        Connection.closeConnection()
        isInit = Connection.isInitialized()
        assert(not isInit)
        closeLog()
