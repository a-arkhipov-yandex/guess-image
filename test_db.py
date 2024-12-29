from __future__ import annotations

import pytest

from db_lib import *

class TestDB:

    userNameExisting = "Test_User_1111"
    userIdExisting = None
    userNameNotExisting = "Test_User_2222"
    userIdNonexisting = 10000000

    def test_DBConnectoin(self) -> None: # Test both test and production connection
        initLog(printToo=True)
        Connection.initConnection(test=False)
        isInit1 = Connection.isInitialized()
        Connection.closeConnection()
        Connection.initConnection(test=True)
        isInit2 = Connection.isInitialized()
        assert(isInit1 and isInit2)
        resCreateUser = Connection.insertUser(userName=TestDB.userNameExisting)
        TestDB.userIdExisting = Connection.getUserIdByName(name=TestDB.userNameExisting)
        assert(resCreateUser == True)
        assert(dbFound(result=TestDB.userIdExisting))

    @pytest.mark.parametrize(
        "query, params, expected_result",
        [
            # Correct
            ('select id from creators where id = 1000000', {}, Connection.NOT_FOUND), # Correct query wihtout params returning nothing
            ('select id from creators where id = %(c)s', {'c':1000000}, Connection.NOT_FOUND), # Correct query with 1 param returning nothing
            ('select id from creators where id=%(c)s and name=%(n)s', {'c':1000000, 'n':'test'}, Connection.NOT_FOUND), # Correct query with >1 params returning nothing
            ('select id from creators where id = 2', {}, [2]), # Correct query wihtout params returning value
            ('select id from creators where id = %(c)s', {'c':2}, [2]), # Correct query with 1 param returning novaluething
            ('select id from creators where id=%(c)s and name=%(n)s', {'c':2, 'n':'Винсент Ван Гог'}, [2]), # Correct query with >1 params returning value
            # Incorrect
            ('select id from creators where people = 10', {}, None), # InCorrect query syntax
            ('select id from creators where id = %(c)s', {}, None), # InCorrect query need params but not provided
            ('select id from creators where id=%(c)s and name=%(n)s', {'c':1000000}, None), # InCorrect number of params in query
        ],
    )
    def testExecuteQueryFetchOne(self, query, params, expected_result):
        assert(Connection.executeQuery(query=query, params=params) == expected_result)

    @pytest.mark.parametrize(
        "query, params, expected_result",
        [
            # Correct
            ('select id from creators where id = 1000000', {}, Connection.NOT_FOUND), # Correct query wihtout params returning nothing
            ('select id from creators where id = %(c)s', {'c':1000000}, Connection.NOT_FOUND), # Correct query with 1 param returning nothing
            ('select id from creators where id=%(c)s and name=%(n)s', {'c':1000000, 'n':'test'}, Connection.NOT_FOUND), # Correct query with >1 params returning nothing
            ('select id from creators where id = 2', {}, [[2]]), # Correct query wihtout params returning value
            ('select id from creators where id = %(c)s', {'c':2}, [[2]]), # Correct query with 1 param returning novaluething
            ('select id from creators where id=%(c)s and name=%(n)s', {'c':2, 'n':'Винсент Ван Гог'}, [[2]]), # Correct query with >1 params returning value
            # Incorrect
            ('select id from creators where people = 10', {}, None), # InCorrect query syntax
            ('select id from creators where id = %(c)s', {}, None), # InCorrect query need params but not provided
            ('select id from creators where id=%(c)s and name=%(n)s', {'c':1000000}, None), # InCorrect number of params in query
        ],
    )
    def testExecuteQueryFetchAll(self, query, params, expected_result):
        assert(Connection.executeQuery(query=query, params=params, all=True) == expected_result)

    def testGetSettingValue(self) -> None:
        ret1 = Connection.getSettingValue(key=Connection.BASE_URL_KEY)
        ret2 = Connection.getSettingValue(key='NonexistingKey')
        assert(dbFound(result=ret1))
        assert(dbNotFound(result=ret2))

    @pytest.mark.parametrize(
        "creator_name, expected_result",
        [
            ('Винсент Ван Гог', 2),
            ('Ари Шеффер', 649),
            ('Nonexisting_creator', None),

        ],
    )
    def testGetCreatorIdByName(self, creator_name, expected_result):
        assert(Connection.getCreatorIdByName(creator=creator_name) == expected_result)

    @pytest.mark.parametrize(
        "creatorId, image, year, expected_result",
        [
            (2, 'Поля тюльпанов', '1883 г', 2),
            (649, 'Любовь земная и Любовь небесная', '1850 г', 3303),
            (10000, 'Поля тюльпанов', '1883 г', Connection.NOT_FOUND), # Nonexisting creator
            (2, 'Nonexisting image', '1883 г', Connection.NOT_FOUND), # Nonexisting image
            (2, 'Поля тюльпанов', '188333 г', Connection.NOT_FOUND), # Nonexisting year
        ],
    )
    def testGetImageIdByCreatorId(self, creatorId, image, year, expected_result):
        assert(Connection.getImageIdByCreatorId(creatorId=creatorId,image=image,year=year) == expected_result)

    @pytest.mark.parametrize(
        "creatorName, image, year, expected_result",
        [
            ('Винсент Ван Гог', 'Поля тюльпанов', '1883 г', 2),
            ('Ари Шеффер', 'Любовь земная и Любовь небесная', '1850 г', 3303),
            ('Nonexisting_creator', 'Поля тюльпанов', '1883 г', Connection.NOT_FOUND), # Nonexisting creator
            ('Винсент Ван Гог', 'Nonexisting image', '1883 г', Connection.NOT_FOUND), # Nonexisting image
            ('Винсент Ван Гог', 'Поля тюльпанов', '188333 г', Connection.NOT_FOUND), # Nonexisting year
        ],
    )
    def testGetImageIdByCreatorName(self, creatorName, image, year, expected_result):
        assert(Connection.getImageIdByCreatorName(creator=creatorName,image=image,year=year) == expected_result)

    @pytest.mark.parametrize(
        "param, expected_result",
        [
            (2, 'Винсент Ван Гог'),
            (10000, Connection.NOT_FOUND),
        ],
    )
    def testGetCreatorNameById(self, param, expected_result):
        assert(Connection.getCreatorNameById(creatorId=param) == expected_result)

    @pytest.mark.parametrize(
        "userName, expected_result",
        [
            ('alex_arkhipov', True),
            ('Nonexisting_user', False),
            ('no', False), # too short name
            ('1Neo', False), # incorect name format 1
            ('Neвава', False),
        ],
    )
    def testGetUserIdByName(self, userName, expected_result):
        assert(dbFound(result=Connection.getUserIdByName(name=userName)) == expected_result)

    def testInsertDeleteUser(self) -> None:
        # test inserting existing user (must return true)
        resEmptyName = Connection.insertUser(userName='')
        resDuplicateUserInsert = Connection.insertUser(userName='Neo')
        resInvalidNameTooShort = Connection.insertUser(userName='Ne')
        resInvalidNameNonASCII = Connection.insertUser(userName='Neкеаo')
        resInvalidNameSrartsWithDigit = Connection.insertUser(userName='1Neo')
        resInvalidNameSpecialChars = Connection.insertUser(userName='Ne$o')

        # test inserting new user
        resNewUserInsert = Connection.insertUser(userName='TestUser')
        # check its id
        id = Connection.getUserIdByName(name='TestUser')
        resGetUserAfetInsert = True
        if (dbNotFound(result=id)):
            resGetUserAfetInsert = False
            resGetUserAfterDelete = False
        else:
            # remove it
            Connection.deleteUser(id=id)
            # check that user is removed
            id2 = Connection.getUserIdByName(name='Test_User')
            resGetUserAfterDelete = True
            if (dbFound(result=id2)):
                resGetUserAfterDelete = False

        assert(resEmptyName == False)
        assert(resDuplicateUserInsert)
        assert(resInvalidNameTooShort == False)
        assert(resInvalidNameNonASCII == False)
        assert(resInvalidNameSrartsWithDigit == False)
        assert(resInvalidNameSpecialChars == False)
        assert(resNewUserInsert)
        assert(resGetUserAfetInsert)
        assert(resGetUserAfterDelete)

    @pytest.mark.parametrize(
        "crName, expected_result",
        [
            ('Винсент Ван Гог', 2),
            ('Nonexisting_creator', Connection.NOT_FOUND),
        ],
    )
    def testGetCreatorIdByName(self, crName, expected_result):
        assert(Connection.getCreatorIdByName(creator=crName) == expected_result)

    def testInsertDeleteCreator(self) -> None:
        # test inserting existing creator (must return true)
        resInsertDuplicateCreator = Connection.insertCreator(creator='Винсент Ван Гог')

        # test inserting new creator
        resInsertNewCreator = Connection.insertCreator(creator='Test_Creator')
        # check its id
        id = Connection.getCreatorIdByName(creator='Test_Creator')
        resGetCreatorAfterInsert = True
        if (dbNotFound(result=id)):
            resGetCreatorAfterInsert = False
            resGetCreatorAfterDelete = False
        else:
            # remove it
            Connection.deleteCreator(id=id)
            # check that user is removed
            id2 = Connection.getCreatorIdByName(creator='Test_Creator')
            resGetCreatorAfterDelete = True
            if (dbFound(result=id2)):
                resGetCreatorAfterDelete = False

        assert(resInsertDuplicateCreator)
        assert(resInsertNewCreator)
        assert(resGetCreatorAfterInsert)
        assert(resGetCreatorAfterDelete)

    def testInsertDeleteImage(self) -> None:
        # test inserting existing image (must return true)
        resExistingImage = Connection.insertImage(creatorId=2, image='Поля тюльпанов', year='1883 г', intYear=1883, orientation=1)

        # test inserting new image with non existing creator
        resNonexistingCreator = Connection.insertImage(creatorId=100000, image='Поля тюльпанов', year='1883 г', intYear=1883, orientation=1)

        # test inserting CORRECT new image
        resInsertCorrectImage = Connection.insertImage(creatorId=2, image='New_Image', year='1883 г', intYear=1883, orientation=1)
        # check its id
        id = Connection.getImageIdByCreatorId(creatorId=2, image='New_Image', year='1883 г')
        resCheckInsertedImage = True
        resDeleteImage = False
        if (dbNotFound(result=id)):
            resCheckInsertedImage = False
            resDeleteImage = False
        else:
            # remove it
            Connection.deleteImage(id=id)
            # check that image is removed
            id2 = Connection.getImageIdByCreatorId(creatorId=2, image='New_Image', year='1883 г')
            resDeleteImage = True
            if (dbFound(result=id2)):
                resDeleteImage = False

        assert(resExistingImage)
        assert(resNonexistingCreator == False)
        assert(resInsertCorrectImage)
        assert(resCheckInsertedImage)
        assert(resDeleteImage)

    def testGetGameInfoById(self) -> None:
        resInCorrectGame = Connection.getGameInfoById(id=10000000)
        assert(dbNotFound(result=resInCorrectGame))

    def testGetRandomCreatorIds(self) -> None:
        res1Id = Connection.getRandomCreatorIds(complexity=1) # 1 Id
        res4Ids = Connection.getRandomCreatorIds(complexity=1, n=4) # 4 Ids
        assert(dbFound(result=res1Id))
        assert(dbFound(result=res4Ids))

    def testGetRandomImageIdsOfCreator(self) -> None:
        res1Id = Connection.getRandomImageIdsOfCreator(creatorId=2) # 1 Id
        res4Ids = Connection.getRandomImageIdsOfCreator(creatorId=2, n=4) # 4 Ids
        assert(dbFound(result=res1Id))
        assert(dbFound(result=res4Ids))

    def testGetRandomImageIdsOfOtherCreators(self) -> None:
        yearRange = (1500, 1600)
        res1Id = Connection.getRandomImageIdsOfOtherCreators(creatorId=2, complexity=1, n=1, range=yearRange) # 1 Id
        res4Ids = Connection.getRandomImageIdsOfOtherCreators(creatorId=2, complexity=1, n=4) # 4 Ids
        resRange = False
        if (dbFound(result=res1Id)):
            game1Id = res1Id[0]
            gameInfo = Connection.getImageInfoById(id=game1Id)
            resRange = (gameInfo['intYear'] > yearRange[0] and gameInfo['intYear'] < yearRange[1])
        
        assert(dbFound(result=res1Id))
        assert(dbFound(result=res4Ids))
        assert(resRange)

    def testGetNCreators(self) -> None:
        yearRange = (1800, 1900)
        res2Ids = Connection.getNCreators(n=2, exclude=2, complexity=1, range=(None,None))
        res4Ids = Connection.getNCreators(n=8, exclude=2, complexity=1, range=yearRange)
        resRange = True
        if (dbFound(result=res4Ids)):
            creators = res4Ids
            for c in creators:
                creatorInfo = Connection.getCreatorInfoById(creatorId=c['creatorId'])
                birth = creatorInfo['birth']
                if (birth):
                    if (birth < yearRange[0]):
                        resRange = False
                        break
                death = creatorInfo['death']
                if (death):
                    if (death > yearRange[1]):
                        resRange = False
                        break

        assert(dbFound(result=res2Ids) and (len(res2Ids) == 2))
        assert(dbFound(result=res4Ids) and len(res4Ids) == 8)
        assert(resRange)

    def testInsertDeleteGame(self) -> None:
        # test inserting new game
        userId = TestDB.userIdExisting
        resInsertNewGame = Connection.insertGame(user_id=userId,game_type=1,correct_answer=1,question=1,complexity=1)
        assert(resInsertNewGame)
        resGetGameAfterInsert = False
        resGetGameAfterDelete = False
        # check its id
        id = Connection.getGameInfoById(id=resInsertNewGame)
        resGetGameAfterInsert = True
        if (dbNotFound(result=id)):
            resGetGameAfterInsert = False
        else:
            # remove it
            Connection.deleteGame(id=id['id'])
            # check that game is removed
            id2 = Connection.getGameInfoById(id=id)
            resGetGameAfterDelete = True
            if (dbFound(result=id2)):
                resGetGameAfterDelete = False

        assert(resGetGameAfterInsert)
        assert(resGetGameAfterDelete)

    def testGetImageInfoById(self) -> None:
        resCorrectImage = Connection.getImageInfoById(id=1)
        resInCorrectImage = Connection.getImageInfoById(id=1000000)
        assert(resCorrectImage.get('creatorId'))
        assert(dbNotFound(result=resInCorrectImage))

    def testGetImageUrlById(self) -> None:
        resCorrectImage = Connection.getImageUrlById(id=1)
        resInCorrectImage = Connection.getImageUrlById(id=1000000)
        assert(dbFound(result=resCorrectImage))
        assert(dbNotFound(result=resInCorrectImage))

    @pytest.mark.parametrize(
        "param, expected_result",
        [
            # Correct values
            ('12', True), # Srting int
            (1, True), # Integer
            (1000000, True), # Int big
            ('1212323', True), # Srting big
            # Incorrect values
            ('12dfdf', False), # String not int
            ('12*12', False), # String special chars
            ('0', False), # String 0
            (0, False), # Int 0
            (-12, False), # Int negative
            ("-122", False), # String negative
        ],
    )
    def testDbLibCheckAnswer(self, param, expected_result):
        assert(dbLibCheckAnswer(answer=param) == expected_result)

    @pytest.mark.parametrize(
        "param, expected_result",
        [
            # Correct values
            ('12', True), # Srting int
            (1, True), # Integer
            (1000000, True), # Int big
            ('1212323', True), # Srting big
            # Incorrect values
            ('12dfdf', False), # String not int
            ('12*12', False), # String special chars
            ('0', False), # String 0
            (0, False), # Int 0
            (-12, False), # Int negative
            ("-122", False), # String negative
        ],
    )
    def testDbLibCheckUserId(self, param, expected_result):
        assert(dbLibCheckUserId(user_id=param) == expected_result)

    @pytest.mark.parametrize(
        "param, expected_result",
        [
            # Correct values
            ('12', True), # Srting int
            (1, True), # Integer
            (1000000, True), # Int big
            ('1212323', True), # Srting big
            # Incorrect values
            ('12dfdf', False), # String not int
            ('12*12', False), # String special chars
            ('0', False), # String 0
            (0, False), # Int 0
            (-12, False), # Int negative
            ("-122", False), # String negative
        ],
    )
    def testDbLibCheckGameId(self, param, expected_result):
        assert(dbLibCheckGameId(game_id=param) == expected_result)

    @pytest.mark.parametrize(
        "param, expected_result",
        [
            # Correct values
            ('1', True), # Srting int
            ('2', True), # Srting int
            (1, True), # Integer
            (2, True), # Integer
            # Incorrect values
            (10, False), # Int > 2
            ('121', False), # Srting > 2
            ('12dfdf', False), # String not int
            ('12*12', False), # String special chars
            ('0', False), # String 0
            (0, False), # Int 0
            (-12, False), # Int negative
            ("-122", False), # String negative
        ],
    )
    def testDbLibCheckGameType(self, param, expected_result):
        assert(dbLibCheckGameType(game_type=param) == expected_result)

    @pytest.mark.parametrize(
        "param, expected_result",
        [
            # Correct values
            ('1', True), # Srting int
            ('2', True), # Srting int
            (1, True), # Integer
            (2, True), # Integer
            # Incorrect values
            (10, False), # Int > 2
            ('121', False), # Srting > 2
            ('12dfdf', False), # String not int
            ('12*12', False), # String special chars
            ('0', False), # String 0
            (0, False), # Int 0
            (-12, False), # Int negative
            ("-122", False), # String negative
        ],
    )
    def testDbLibCheckOrientation(self, param, expected_result):
        assert(dbLibCheckOrientation(orientation=param) == expected_result)

    @pytest.mark.parametrize(
        "param, expected_result",
        [
            # Correct values
            (Connection.NOT_FOUND, True),
            # Incorrect values
            (None, False),
            ([1], False),
            ([1,2], False),
        ],
    )
    def testDbNotFound(self, param, expected_result):
        assert(dbNotFound(result=param) == expected_result)

    @pytest.mark.parametrize(
        "param, expected_result",
        [
            # Correct values
            ([1], True),
            ([1,2], True),
            # Incorrect values
            (None, False),
            (Connection.NOT_FOUND, False),
        ],
    )
    def testDbFound(self, param, expected_result):
        assert(dbFound(result=param) == expected_result)

    def testGetGameTypesFromDb(self) -> None:
        resCorrectImage = Connection.getGameTypesFromDb()
        assert(len(resCorrectImage) == 3)

    def testGetGameTypesFromCache(self) -> None:
        resCorrectImage = Connection.getGameTypes()
        assert(len(resCorrectImage) == 3)

    def testFinishGame(self) -> None:
        resNonexistingGame = Connection.finishGame(gameId=2000000, answer=1)
        resFinishedGame = True
        # Create game type 1
        resGameType1 = False
        ret = Connection.insertGame(user_id=TestDB.userIdExisting,game_type=1,correct_answer=1,question=1,complexity=1)
        assert(ret != None)
        if (ret != None):
            # Finish game
            ret2 = Connection.finishGame(gameId=ret, answer=1)
            if (ret2):
                # Check if game is finished
                resGameType1 = Connection.checkGameIsFinished(gameId=ret)
                resFinishedGame = Connection.finishGame(gameId=ret, answer=1)
            # Delete game
            Connection.deleteGame(id=ret)

        # Create game type 2
        resGameType2 = False
        ret = Connection.insertGame(user_id=TestDB.userIdExisting,game_type=2,correct_answer=1,question=1,complexity=1)
        if (ret != None):
            # Finish game
            ret2 = Connection.finishGame(gameId=ret, answer=2)
            if (ret2):
                # Check if game is finished
                resGameType2 = Connection.checkGameIsFinished(gameId=ret)
            # Delete game
            Connection.deleteGame(id=ret)

        assert(resNonexistingGame == False)
        assert(resFinishedGame == False)
        assert(resGameType1)
        assert(resGameType2)

    def testGetGamesListAllFinishedUnfinished(self) -> None:
        resUnfinishedGamesList = False
        resFinishedGamesList = False
        resAllGamesList = False
        userId = TestDB.userIdExisting
        # Generate new game and get id
        gameId = Connection.insertGame(user_id=userId,game_type=1,correct_answer=1,question=1,complexity=1)
        if (gameId != None):
            # Get unfinished list
            unfinishedList = Connection.getUnfinishedGamesList(userId=userId)
            # Check that id is in the list
            for game in unfinishedList:
                if (game['id'] == gameId):
                    resUnfinishedGamesList = True
                    break
            # Get all list
            allList = Connection.getAllGamesList(userId=userId)
            # Check that id is in the list
            for game in allList:
                if (game['id'] == gameId):
                    resAllGamesList = True
                    break
            # Finish game
            ret2 = Connection.finishGame(gameId=gameId, answer=5)
            if (ret2):
                # Get finished list
                finishedList = Connection.getFinishedGamesList(userId=userId)
                # Check that id is in the list
                for game in finishedList:
                    if (game['id'] == gameId):
                        resFinishedGamesList = True
                        break
            # Delete game
            Connection.deleteGame(id=gameId)

        assert(resUnfinishedGamesList)
        assert(resFinishedGamesList)
        assert(resAllGamesList)

    def testCurrentGame(self) -> None:
        userId1 = TestDB.userIdExisting
        userName1 = TestDB.userNameExisting
        userName2 = 'TestCurrentGameUser'
        # Create user
        Connection.insertUser(userName=userName2)
        userId2 = Connection.getUserIdByName(name=userName2)
        # Generate new game and get id
        gameUnfinishedId = Connection.insertGame(user_id=userId1,game_type=1,correct_answer=1,question=1,complexity=1)
        assert(gameUnfinishedId != None)
        # Generate new game and get id
        gameFinishedId = Connection.insertGame(user_id=userId1,game_type=1,correct_answer=1,question=1,complexity=1)
        Connection.finishGame(gameId=gameFinishedId, answer=1)
        resSetCurrentGameWrongUser = Connection.setCurrentGame(userName=userName2, gameId=gameUnfinishedId)
        resSetCurrentGameNonexistingUser = Connection.setCurrentGame(userName='NonexistingUser',gameId=gameUnfinishedId)
        resSetCurrentGameNonexistingGame = Connection.setCurrentGame(userName=userName1, gameId=100000000)
        resSetCurrentGameUnfinishedGame = Connection.setCurrentGame(userName=userName1, gameId=gameUnfinishedId)
        gameUnfinishedId2 = Connection.getCurrentGame(userName=userName1)
        resClearCurrentGame = Connection.clearCurrentGame(userName=userName1)
        gameUnfinishedId3 = Connection.getCurrentGame(userName=userName1)
        resSetCurrentGameFinishedGame = Connection.setCurrentGame(userName=userName1, gameId=gameFinishedId)
        gameFinishedId2 = Connection.getCurrentGame(userName=userName1)

        # Delete games
        Connection.deleteGame(id=gameUnfinishedId)
        Connection.deleteGame(id=gameFinishedId)
        # Delete user
        Connection.deleteUser(id=userId2)

        assert(resSetCurrentGameWrongUser == False)
        assert(resSetCurrentGameNonexistingUser == False)
        assert(resSetCurrentGameNonexistingGame == False)
        assert(resSetCurrentGameUnfinishedGame == True)
        assert(gameUnfinishedId2 == gameUnfinishedId)
        assert(resSetCurrentGameFinishedGame == False)
        assert(gameFinishedId2 == None)
        assert(resClearCurrentGame == True)
        assert(gameUnfinishedId3 == None)

    def testCurrentGameData(self) -> None:
        userName2 = 'TestCurrentGameUser'
        gameData = "data"
        imageInfo = "test - test - 1923 г"
        # Create user
        Connection.insertUser(userName=userName2)
        userId2 = Connection.getUserIdByName(name=userName2)
        # Generate new game and get id
        gameUnfinishedId = Connection.insertGame(user_id=userId2,game_type=1,correct_answer=1,question=1,complexity=1)
        resSetCurrentGameDataNonexistingUser = Connection.setCurrentGame(userName='NonexistingUser',gameId=gameUnfinishedId)
        resSetCurrentGameDataCorrect = Connection.setCurrentGameData(userName=userName2, gameData=gameData)
        gameUnfinishedDataCorrect = Connection.getCurrentGameData(userName=userName2)
        resClearCurrentGame = Connection.clearCurrentGameData(userName=userName2)
        gameUnfinishedData = Connection.getCurrentGameData(userName=userName2)

        resSetCurrentImageInfoCorrect = Connection.setCurrentImageInfo(userName=userName2, imageInfo=imageInfo)
        gameUnfinishedImageInfoCorrect = Connection.getCurrentImageInfo(userName=userName2)
        resClearCurrentImageInfo = Connection.clearCurrentImageInfo(userName=userName2)
        gameUnfinishedImageInfo = Connection.getCurrentImageInfo(userName=userName2)

        # Delete games
        Connection.deleteGame(id=gameUnfinishedId)
        # Delete user
        Connection.deleteUser(id=userId2)

        assert(resSetCurrentGameDataNonexistingUser == False)
        assert(resSetCurrentGameDataCorrect == True)
        assert(gameUnfinishedDataCorrect == gameData)
        assert(resClearCurrentGame == True)
        assert(gameUnfinishedData == None)

        assert(resSetCurrentImageInfoCorrect == True)
        assert(gameUnfinishedImageInfoCorrect == imageInfo)
        assert(resClearCurrentImageInfo == True)
        assert(gameUnfinishedImageInfo == None)

    def testUserSettings(self) -> None:
        userNameCorrect = 'testUserSettings'
        userNameInCorrect = 'TestUserSettingsвава'
        origGameType = Connection.getDefaultGameType()
        origGameComplexity = Connection.getDefaultComplexity()
        newGameType = 2
        newGameComplexity = 3
        # Create user
        Connection.insertUser(userName=userNameCorrect)
        userId = Connection.getUserIdByName(name=userNameCorrect)
        userSettings = Connection.getUserSetting(userName=userNameCorrect)
        resUserSettings = ((userSettings[0] == Connection.getDefaultGameType()) and (userSettings[1] == Connection.getDefaultComplexity()))
        gameType1 = Connection.getUserGameType(userName=userNameCorrect)
        gameComplexity1 = Connection.getUserComplexity(userName=userNameCorrect)
        gameTypeInCorrect = Connection.getUserGameType(userName=userNameInCorrect)
        gameComplexityInCorrect = Connection.getUserComplexity(userName=userNameInCorrect)
        resUpdateGameTypeCorrect = Connection.updateUserGameType(userName=userNameCorrect, gameType=newGameType)
        resUpdateGameTypeInCorrect = Connection.updateUserGameType(userName=userNameCorrect, gameType=100)
        resUpdateGameComplexityCorrect = Connection.updateUserComplexity(userName=userNameCorrect, complexity=newGameComplexity)
        resUpdateGameComplexityInCorrect = Connection.updateUserComplexity(userName=userNameCorrect, complexity=50)
        gameType2 = Connection.getUserGameType(userName=userNameCorrect)
        gameComplexity2 = Connection.getUserComplexity(userName=userNameCorrect)

        # delete user
        Connection.deleteUser(id=userId)

        assert(gameType1 == origGameType)
        assert(resUserSettings)
        assert(gameComplexity1 == origGameComplexity)
        assert(gameTypeInCorrect == None)
        assert(gameComplexityInCorrect == None)
        assert(resUpdateGameTypeCorrect == True)
        assert(resUpdateGameTypeInCorrect == False)
        assert(resUpdateGameComplexityCorrect == True)
        assert(resUpdateGameComplexityInCorrect == False)
        assert(gameType2 == newGameType)
        assert(gameComplexity2 == newGameComplexity)

    def testBulkCreatorInsert(self):
        noneexistingСreatorName = 'Noneexistingcreatorfordelete'
        creators = [noneexistingСreatorName]
        cIdBeforeInsert = Connection.getCreatorIdByName(noneexistingСreatorName)
        resCIdBeforeInsert = (dbFound(cIdBeforeInsert))        
        Connection.bulkCreatorInsert(creators)
        cIdAfterInsert = Connection.getCreatorIdByName(noneexistingСreatorName)
        resCIdAfterInsert = (dbFound(cIdAfterInsert))
        Connection.deleteCreator(cIdAfterInsert)
        cIdAfterDelete = Connection.getCreatorIdByName(noneexistingСreatorName)
        resCIdAfterDelete = (dbFound(cIdAfterDelete))
        assert(resCIdBeforeInsert != True)
        assert(resCIdAfterInsert)
        assert(resCIdAfterDelete != True)

    def testGetAllImagesOfCreator(self):
        noneexistingСreatorId = 1000000
        existingCreatorId = 2 # Van Gogh
        resNonexistingCreator = Connection.getAllImagesOfCreator(creatorId=noneexistingСreatorId)
        ret = Connection.getAllImagesOfCreator(creatorId=existingCreatorId)
        resExistingCreator = (dbFound(result=ret))
        assert(resNonexistingCreator == [])
        assert(resExistingCreator)

    def testCloseConnection(self) -> None:
        resDeleteUser = Connection.deleteUser(id=TestDB.userIdExisting)
        Connection.closeConnection()
        closeLog()
        isInit = Connection.isInitialized()
        assert(resDeleteUser == True)
        assert(not isInit)

