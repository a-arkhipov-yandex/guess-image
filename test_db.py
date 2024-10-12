from __future__ import annotations

import pytest

from db_lib import *

class TestDB:

    def test_DBConnectoin(self) -> None: # Test both test and production connection
        initLog(printToo=True)
        Connection.initConnection(test=False)
        isInit1 = Connection.isInitialized()
        Connection.closeConnection()
        Connection.initConnection(test=True)
        isInit2 = Connection.isInitialized()
        assert(isInit1 and isInit2)

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
        assert(Connection.executeQuery(query, params) == expected_result)

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
        assert(Connection.executeQuery(query, params, True) == expected_result)

    def testGetSettingValue(self):
        ret1 = Connection.getSettingValue(Connection.BASE_URL_KEY)
        ret2 = Connection.getSettingValue('NonexistingKey')
        assert(dbFound(ret1))
        assert(dbNotFound(ret2))

    @pytest.mark.parametrize(
        "creator_name, expected_result",
        [
            ('Винсент Ван Гог', 2),
            ('Ари Шеффер', 649),
            ('Nonexisting_creator', None),

        ],
    )
    def testGetCreatorIdByName(self, creator_name, expected_result):
        assert(Connection.getCreatorIdByName(creator_name) == expected_result)

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
        assert(Connection.getImageIdByCreatorId(creatorId,image,year) == expected_result)

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
        assert(Connection.getImageIdByCreatorName(creatorName,image,year) == expected_result)

    @pytest.mark.parametrize(
        "param, expected_result",
        [
            (2, 'Винсент Ван Гог'),
            (10000, Connection.NOT_FOUND),
        ],
    )
    def testGetCreatorNameById(self, param, expected_result):
        assert(Connection.getCreatorNameById(param) == expected_result)

    @pytest.mark.parametrize(
        "userName, expected_result",
        [
            ('Neo', 1),
            ('Nonexisting_user', Connection.NOT_FOUND),
            ('no', Connection.NOT_FOUND), # too short name
            ('1Neo', Connection.NOT_FOUND), # incorect name format 1
            ('Neвава', Connection.NOT_FOUND),
        ],
    )
    def testGetUserIdByName(self, userName, expected_result):
        assert(Connection.getUserIdByName(userName) == expected_result)

    def testInsertDeleteUser(self):
        # test inserting existing user (must return true)
        resEmptyName = Connection.insertUser('')
        resDuplicateUserInsert = Connection.insertUser('Neo')
        resInvalidNameTooShort = Connection.insertUser('Ne')
        resInvalidNameNonASCII = Connection.insertUser('Neкеаo')
        resInvalidNameSrartsWithDigit = Connection.insertUser('1Neo')
        resInvalidNameSpecialChars = Connection.insertUser('Ne$o')

        # test inserting new user
        resNewUserInsert = Connection.insertUser('TestUser')
        # check its id
        id = Connection.getUserIdByName('TestUser')
        resGetUserAfetInsert = True
        if (dbNotFound(id)):
            resGetUserAfetInsert = False
            resGetUserAfterDelete = False
        else:
            # remove it
            Connection.deleteUser(id)
            # check that user is removed
            id2 = Connection.getUserIdByName('Test_User')
            resGetUserAfterDelete = True
            if (dbFound(id2)):
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
        assert(Connection.getCreatorIdByName(crName) == expected_result)

    def testInsertDeleteCreator(self):
        # test inserting existing creator (must return true)
        resInsertDuplicateCreator = Connection.insertCreator('Винсент Ван Гог')

        # test inserting new creator
        resInsertNewCreator = Connection.insertCreator('Test_Creator')
        # check its id
        id = Connection.getCreatorIdByName('Test_Creator')
        resGetCreatorAfterInsert = True
        if (dbNotFound(id)):
            resGetCreatorAfterInsert = False
            resGetCreatorAfterDelete = False
        else:
            # remove it
            Connection.deleteCreator(id)
            # check that user is removed
            id2 = Connection.getCreatorIdByName('Test_Creator')
            resGetCreatorAfterDelete = True
            if (dbFound(id2)):
                resGetCreatorAfterDelete = False

        assert(resInsertDuplicateCreator)
        assert(resInsertNewCreator)
        assert(resGetCreatorAfterInsert)
        assert(resGetCreatorAfterDelete)

    def testInsertDeleteImage(self):
        # test inserting existing image (must return true)
        resExistingImage = Connection.insertImage(2, 'Поля тюльпанов', '1883 г', 1883, 1)

        # test inserting new image with non existing creator
        resNonexistingCreator = Connection.insertImage(100000, 'Поля тюльпанов', '1883 г', 1883, 1)

        # test inserting CORRECT new image
        resInsertCorrectImage = Connection.insertImage(2, 'New_Image', '1883 г', 1883, 1)
        # check its id
        id = Connection.getImageIdByCreatorId(2, 'New_Image', '1883 г')
        resCheckInsertedImage = True
        resDeleteImage = False
        if (dbNotFound(id)):
            resCheckInsertedImage = False
            resDeleteImage = False
        else:
            # remove it
            Connection.deleteImage(id)
            # check that image is removed
            id2 = Connection.getImageIdByCreatorId(2, 'New_Image', '1883 г')
            resDeleteImage = True
            if (dbFound(id2)):
                resDeleteImage = False

        assert(resExistingImage)
        assert(resNonexistingCreator == False)
        assert(resInsertCorrectImage)
        assert(resCheckInsertedImage)
        assert(resDeleteImage)

    def testGetGameInfoById(self):
        resInCorrectGame = Connection.getGameInfoById(10000000)
        assert(dbNotFound(resInCorrectGame))

    def testGetRandomCreatorIds(self):
        res1Id = Connection.getRandomCreatorIds(1) # 1 Id
        res4Ids = Connection.getRandomCreatorIds(1, 4) # 4 Ids
        assert(dbFound(res1Id))
        assert(dbFound(res4Ids))

    def testGetRandomImageIdsOfCreator(self):
        res1Id = Connection.getRandomImageIdsOfCreator(2) # 1 Id
        res4Ids = Connection.getRandomImageIdsOfCreator(2, n=4) # 4 Ids
        assert(dbFound(res1Id))
        assert(dbFound(res4Ids))

    def testGetRandomImageIdsOfOtherCreators(self):
        yearRange = (1500, 1600)
        res1Id = Connection.getRandomImageIdsOfOtherCreators(creatorId=2, complexity=1, n=1, range=yearRange) # 1 Id
        res4Ids = Connection.getRandomImageIdsOfOtherCreators(creatorId=2, complexity=1, n=4) # 4 Ids
        resRange = False
        if (dbFound(res1Id)):
            game1Id = res1Id[0]
            gameInfo = Connection.getImageInfoById(game1Id)
            resRange = (gameInfo['intYear'] > yearRange[0] and gameInfo['intYear'] < yearRange[1])
        
        assert(dbFound(res1Id))
        assert(dbFound(res4Ids))
        assert(resRange)

    def testGetNCreators(self):
        yearRange = (1800, 1900)
        res2Ids = Connection.getNCreators(n=2, exclude=2, complexity=1, range=(None,None))
        res4Ids = Connection.getNCreators(n=8, exclude=2, complexity=1, range=yearRange)
        resRange = True
        if (dbFound(res4Ids)):
            creators = res4Ids
            for c in creators:
                creatorInfo = Connection.getCreatorInfoById(c['creatorId'])
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

        assert(dbFound(res2Ids) and (len(res2Ids) == 2))
        assert(dbFound(res4Ids) and len(res4Ids) == 8)
        assert(resRange)

    def testInsertDeleteGame(self):
        # test inserting new game
        resInsertNewGame = Connection.insertGame(1,1,1,1,1)
        resGetGameAfterInsert = False
        resGetGameAfterDelete = False
        # check its id
        if (resInsertNewGame):
            id = Connection.getGameInfoById(resInsertNewGame)
            resGetGameAfterInsert = True
            if (dbNotFound(id)):
                resGetGameAfterInsert = False
            else:
                # remove it
                Connection.deleteGame(id['id'])
                # check that game is removed
                id2 = Connection.getGameInfoById(id)
                resGetGameAfterDelete = True
                if (dbFound(id2)):
                    resGetGameAfterDelete = False

        assert(resInsertNewGame)
        assert(resGetGameAfterInsert)
        assert(resGetGameAfterDelete)

    def testGetImageInfoById(self):
        resCorrectImage = Connection.getImageInfoById(1)
        resInCorrectImage = Connection.getImageInfoById(1000000)
        assert(resCorrectImage.get('creatorId'))
        assert(dbNotFound(resInCorrectImage))

    def testGetImageUrlById(self):
        resCorrectImage = Connection.getImageUrlById(1)
        resInCorrectImage = Connection.getImageUrlById(1000000)
        assert(dbFound(resCorrectImage))
        assert(dbNotFound(resInCorrectImage))

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
        assert(dbLibCheckAnswer(param) == expected_result)

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
        assert(dbLibCheckUserId(param) == expected_result)

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
        assert(dbLibCheckGameId(param) == expected_result)

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
        assert(dbLibCheckGameType(param) == expected_result)

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
        assert(dbLibCheckOrientation(param) == expected_result)

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
        assert(dbNotFound(param) == expected_result)

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
        assert(dbFound(param) == expected_result)

    def testGetGameTypesFromDb(self):
        resCorrectImage = Connection.getGameTypesFromDb()
        assert(len(resCorrectImage) == 3)

    def testGetGameTypesFromCache(self):
        resCorrectImage = Connection.getGameTypes()
        assert(len(resCorrectImage) == 3)

    def testFinishGame(self):
        resNonexistingGame = Connection.finishGame(2000000, 1)
        resFinishedGame = True
        # Create game type 1
        resGameType1 = False
        ret = Connection.insertGame(1,1,1,1,1)
        if (ret != None):
            # Finish game
            ret2 = Connection.finishGame(ret, 1)
            if (ret2):
                # Check if game is finished
                resGameType1 = Connection.checkGameIsFinished(ret)
                resFinishedGame = Connection.finishGame(ret, 1)
            # Delete game
            Connection.deleteGame(ret)

        # Create game type 2
        resGameType2 = False
        ret = Connection.insertGame(1,2,1,1,1)
        if (ret != None):
            # Finish game
            ret2 = Connection.finishGame(ret, 2)
            if (ret2):
                # Check if game is finished
                resGameType2 = Connection.checkGameIsFinished(ret)
            # Delete game
            Connection.deleteGame(ret)

        assert(resNonexistingGame == False)
        assert(resFinishedGame == False)
        assert(resGameType1)
        assert(resGameType2)

    def testGetGamesListAllFinishedUnfinished(self):
        resUnfinishedGamesList = False
        resFinishedGamesList = False
        resAllGamesList = False
        userId = 1
        # Generate new game and get id
        gameId = Connection.insertGame(userId,1,1,1,1)
        if (gameId != None):
            # Get unfinished list
            unfinishedList = Connection.getUnfinishedGamesList(userId)
            # Check that id is in the list
            for game in unfinishedList:
                if (game['id'] == gameId):
                    resUnfinishedGamesList = True
                    break
            # Get all list
            allList = Connection.getAllGamesList(userId)
            # Check that id is in the list
            for game in allList:
                if (game['id'] == gameId):
                    resAllGamesList = True
                    break
            # Finish game
            ret2 = Connection.finishGame(gameId, 5)
            if (ret2):
                # Get finished list
                finishedList = Connection.getFinishedGamesList(userId)
                # Check that id is in the list
                for game in finishedList:
                    if (game['id'] == gameId):
                        resFinishedGamesList = True
                        break
            # Delete game
            Connection.deleteGame(gameId)

        assert(resUnfinishedGamesList)
        assert(resFinishedGamesList)
        assert(resAllGamesList)

    def testCurrentGame(self):
        userId1 = 1
        userName1 = 'Neo'
        userName2 = 'TestCurrentGameUser'
        # Create user
        Connection.insertUser(userName2)
        userId2 = Connection.getUserIdByName(userName2)
        # Generate new game and get id
        gameUnfinishedId = Connection.insertGame(userId1,1,1,1,1)
        # Generate new game and get id
        gameFinishedId = Connection.insertGame(userId1,1,1,1,1)
        Connection.finishGame(gameFinishedId, 1)
        resSetCurrentGameWrongUser = Connection.setCurrentGame(userName2, gameUnfinishedId)
        resSetCurrentGameNonexistingUser = Connection.setCurrentGame('NonexistingUser',gameUnfinishedId)
        resSetCurrentGameNonexistingGame = Connection.setCurrentGame(userName1, 100000000)
        resSetCurrentGameUnfinishedGame = Connection.setCurrentGame(userName1, gameUnfinishedId)
        gameUnfinishedId2 = Connection.getCurrentGame(userName1)
        resClearCurrentGame = Connection.clearCurrentGame(userName1)
        gameUnfinishedId3 = Connection.getCurrentGame(userName1)
        resSetCurrentGameFinishedGame = Connection.setCurrentGame(userName1, gameFinishedId)
        gameFinishedId2 = Connection.getCurrentGame(userName1)

        # Delete games
        Connection.deleteGame(gameUnfinishedId)
        Connection.deleteGame(gameFinishedId)
        # Delete user
        Connection.deleteUser(userId2)

        assert(resSetCurrentGameWrongUser == False)
        assert(resSetCurrentGameNonexistingUser == False)
        assert(resSetCurrentGameNonexistingGame == False)
        assert(resSetCurrentGameUnfinishedGame == True)
        assert(gameUnfinishedId2 == gameUnfinishedId)
        assert(resSetCurrentGameFinishedGame == False)
        assert(gameFinishedId2 == None)
        assert(resClearCurrentGame == True)
        assert(gameUnfinishedId3 == None)

    def testCurrentGameData(self):
        userName2 = 'TestCurrentGameUser'
        gameData = "data"
        # Create user
        Connection.insertUser(userName2)
        userId2 = Connection.getUserIdByName(userName2)
        # Generate new game and get id
        gameUnfinishedId = Connection.insertGame(userId2,1,1,1,1)
        resSetCurrentGameDataNonexistingUser = Connection.setCurrentGame('NonexistingUser',gameUnfinishedId)
        resSetCurrentGameDataCorrect = Connection.setCurrentGameData(userName2, gameData)
        gameUnfinishedDataCorrect = Connection.getCurrentGameData(userName2)
        resClearCurrentGame = Connection.clearCurrentGameData(userName2)
        gameUnfinishedData = Connection.getCurrentGameData(userName2)

        # Delete games
        Connection.deleteGame(gameUnfinishedId)
        # Delete user
        Connection.deleteUser(userId2)

        assert(resSetCurrentGameDataNonexistingUser == False)
        assert(resSetCurrentGameDataCorrect == True)
        assert(gameUnfinishedDataCorrect == gameData)
        assert(resClearCurrentGame == True)
        assert(gameUnfinishedData == None)

    def testUserSettings(self):
        userNameCorrect = 'testUserSettings'
        userNameInCorrect = 'TestUserSettingsвава'
        origGameType = Connection.getDefaultGameType()
        origGameComplexity = Connection.getDefaultComplexity()
        newGameType = 2
        newGameComplexity = 3
        # Create user
        Connection.insertUser(userNameCorrect)
        userId = Connection.getUserIdByName(userNameCorrect)
        userSettings = Connection.getUserSetting(userNameCorrect)
        resUserSettings = ((userSettings[0] == Connection.getDefaultGameType()) and (userSettings[1] == Connection.getDefaultComplexity()))
        gameType1 = Connection.getUserGameType(userNameCorrect)
        gameComplexity1 = Connection.getUserComplexity(userNameCorrect)
        gameTypeInCorrect = Connection.getUserGameType(userNameInCorrect)
        gameComplexityInCorrect = Connection.getUserComplexity(userNameInCorrect)
        resUpdateGameTypeCorrect = Connection.updateUserGameType(userNameCorrect, newGameType)
        resUpdateGameTypeInCorrect = Connection.updateUserGameType(userNameCorrect, 100)
        resUpdateGameComplexityCorrect = Connection.updateUserComplexity(userNameCorrect, newGameComplexity)
        resUpdateGameComplexityInCorrect = Connection.updateUserComplexity(userNameCorrect, 50)
        gameType2 = Connection.getUserGameType(userNameCorrect)
        gameComplexity2 = Connection.getUserComplexity(userNameCorrect)

        # delete user
        Connection.deleteUser(userId)

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

    def testCloseConnection(self):
        Connection.closeConnection()
        closeLog()
        isInit = Connection.isInitialized()
        assert(not isInit)

