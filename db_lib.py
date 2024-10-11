from time import sleep
from threading import Thread
import psycopg2
from guess_image_lib import *
from log_lib import *

CREATORS_IN_TYPE2_ANSWER = 5

#=======================
# Checks section
#-----------------------
def dbLibCheckCreator(creatorInfo) -> bool:
    if (not creatorInfo.get('id')):
        return False
    if (not creatorInfo.get('name')):
        return False
    if (not creatorInfo.get('complexity')):
        return False

    return True

# Check answer (can be string or int with positive integer value)
def dbLibCheckAnswer(answer) -> bool:
    ret = False
    iA = 0
    try:
        iA = int(answer)
    except:
        return False
    if (iA > 0):
        ret = True
    return ret

# Check user id (can be string or int with positive integer value)
def dbLibCheckUserId(user_id) -> bool:
    ret = False
    iId = 0
    try:
        iId = int(user_id)
    except:
        return False
    if (iId > 0):
        ret = True
    return ret

# Check if gender of creator is woman
def dbIsWoman(gender) -> bool:
    return (gender == 2)

# Check user name (can be string with '[a-zA-Z][0-9a-zA-Z]')
def dbLibCheckUserName(user_name) -> bool:
    if (user_name == None):
        return False
    return checkUserNameFormat(user=user_name)

# Check game id (can be string or int with positive integer value)
def dbLibCheckGameId(game_id) -> bool:
    ret = False
    iId = 0
    try:
        iId = int(game_id)
    except:
        return ret
    if (iId > 0):
        ret = True
    return ret

# Check game type (can be string or int with value 1 or 2)
def dbLibCheckGameType(game_type) -> bool:
    ret = False
    iType = 0
    try:
        iType = int(game_type)
    except:
        return ret
    if (iType >= 1 and iType <= 3):
        ret = True
    return ret

# Check game type (can be string or int with value 1 or 2)
def dbLibCheckGameComplexity(game_type) -> bool:
    ret = False
    iComplexity = 0
    try:
        iComplexity = int(game_type)
    except:
        return ret
    if (iComplexity >= 1 and iComplexity <= 3):
        ret = True
    return ret

# Check image orientation (can be string or int with value 1 or 2)
def dbLibCheckOrientation(orientation) -> bool:
    ret = False
    iOr = 0
    try:
        iOr = int(orientation)
    except:
        return False
    if (iOr == 1 or iOr == 2):
        ret = True
    return ret

# Check if game is finished
# Input:
#   gameInfo - data
# Returns: True/False
def dbLibCheckIfGameFinished(gameInfo) -> bool:
    result = gameInfo.get('result')
    if (result != None):
        return True
    return False

#=======================
# Common functions section
#-----------------------
# Check that item not found
# Returns:
#   True - item was not found
#   False - otherwise (found or error)
def dbNotFound(result) -> bool:
    if (result != None):
        if (result == Connection.NOT_FOUND): # empty array
            return True
    return False

# Check that item is found
# Returns:
#   True - item has been found
#   False - otherwise (not found or error)
def dbFound(result) -> bool:
    if (result != None):
        if (result != Connection.NOT_FOUND): # empty array
            return True
    return False

# Make useful map for game
def dbGetGameInfo(queryResult):
    game = {}
    if (len(queryResult) != 10):
        return game
    game['id'] = int(queryResult[0])
    game['user'] = int(queryResult[1])
    game['type'] = int(queryResult[2])
    game['correct_answer'] = int(queryResult[3])
    game['question'] = queryResult[4]
    game['user_answer']  = queryResult[5]
    if (game['user_answer']):
        game['user_answer'] = int(game['user_answer'])
    game['result'] = queryResult[6]
    game['created'] = queryResult[7]
    game['finished'] = queryResult[8]
    game['complexity'] = int(queryResult[9])
    return game

# Make useful map for creator
def dbGetCreatorInfo(queryResult):
    creator = {}
    if (len(queryResult) != 7):
        return creator
    creator['id'] = int(queryResult[0])
    creator['name'] = queryResult[1]
    creator['gender'] = queryResult[2]
    if (creator['gender']):
        creator['gender'] = int(creator['gender'])
    creator['country'] = queryResult[3]
    creator['birth'] = queryResult[4]
    if (creator['birth']):
        creator['birth'] = int(creator['birth'])
    creator['death'] = queryResult[5]
    if (creator['death']):
        creator['death'] = int(creator['death'])
    creator['complexity'] = int(queryResult[6])
    return creator

# Make useful map for image
def dbGetImageInfo(queryResult):
    imageInfo = {}
    imageInfo['creatorId'] = int(queryResult[0])
    imageInfo['creatorName'] = queryResult[1]
    imageInfo['imageName'] = queryResult[2]
    imageInfo['intYear'] = int(queryResult[3])
    imageInfo['yearStr'] = queryResult[4]
    imageInfo['orientation'] = int(queryResult[5])
    return imageInfo

# Make map: creator -> [title, year, intYear, orientation]
def getImageCreatorMap(creators, titles, years, intYears, orientations):
    mCreators = {}
    for i in range(0, len(creators)):
        if (not mCreators.get(creators[i])):
            mCreators[creators[i]] = []
        mCreators[creators[i]].append([titles[i],years[i],intYears[i], orientations[i]])
    return mCreators

# Get info from image data
def getImageFromData(imageData):
    return imageData[0]

def getYearFromData(imageData):
    return imageData[1]

def getIntYearFromData(imageData):
    return imageData[2]

def getOrientationFromData(imageData):
    return imageData[3]

#==================
# Class definition
class Connection:
    __connection = None
    __isInitialized = False
    __baseImageUrl = None
    __defaultGameType = None
    __defaultComplexity = None
    __gameTypes = []
    __complexities = []
    __thread = None
    loopFlag = True
    BASE_URL_KEY = 'base_url'
    DEFAULT_GAMETYPE_KEY = 'default_gametype'
    DEFAULT_COMPLEXITY_KEY = 'default_complexity'
    NOT_FOUND = "!!!NOT_FOUND!!!"

    # Init connection - returns True/False
    def initConnection(token=None, test=False) -> bool:
        ret = False
        if (not Connection.__isInitialized):
            Connection.__newConnection(token=token, test=test)
            if (Connection.isActive()):
                # Cache section
                Connection.__baseImageUrl = Connection.getSettingValue(key=Connection.BASE_URL_KEY)
                Connection.__defaultGameType = int(Connection.getSettingValue(key=Connection.DEFAULT_GAMETYPE_KEY))
                Connection.__defaultComplexity = int(Connection.getSettingValue(key=Connection.DEFAULT_COMPLEXITY_KEY))
                Connection.__gameTypes = Connection.getGameTypesFromDb()
                Connection.__complexities = Connection.getComplexitiesFromDb()
                Connection.__test = test
                log(str=f"DB Connection created", logLevel=LOG_DEBUG)
                ret = True
            else:
                log(str=f'Cannot initialize connection to DB',logLevel=LOG_ERROR)
        else:
                log(str=f'Trying to initialize connection that already initialized',logLevel=LOG_WARNING)
        return ret
    
    def getConnection():
        return Connection.__connection
    
    def closeConnection() -> None:
        if (Connection.isActive()):
            Connection.pingStop()
            Connection.__isInitialized = False
            Connection.__connection.close()
            log(str=f"DB Connection closed")
        else:
            log(str=f"DB Connection already closed",logLevel=LOG_WARNING)

    def __newConnection(token=None, test=False):
        ret = False
        try:
            if (not isWeb()): # Connection via internet
                if (test):
                    data = getDBbTestConnectionData()
                else: # Production
                    data = getDBbConnectionData()
                if (data == None):
                    log(str=f'Cannot get env data. Exiting.',logLevel=LOG_ERROR)
                    return ret

                Connection.__connection = psycopg2.connect(dsn=f"""
                    host={data['dbhost']}
                    port={data['dbport']}
                    sslmode=verify-full
                    dbname={data['dbname']}
                    user={data['dbuser']}
                    password={data['dbtoken']}
                    target_session_attrs=read-write
                """)
            else: # Connection from inside cloud function
                if (test):
                    Connection.__connection = psycopg2.connect(
                        database="akf7lhr9b3t46j4pm42d", # Идентификатор подключения
                        user="user1", # Пользователь БД
                        password=token,
                        host="akf7lhr9b3t46j4pm42d.postgresql-proxy.serverless.yandexcloud.net", # Точка входа
                        port=6432,
                        sslmode="require")
                else:
                    Connection.__connection = psycopg2.connect(
                        database="akfskctj4iduo0t9h9dl", # Идентификатор подключения
                        user="user1", # Пользователь БД
                        password=token,
                        host="akfskctj4iduo0t9h9dl.postgresql-proxy.serverless.yandexcloud.net", # Точка входа
                        port=6432,
                        sslmode="require")
            Connection.__connection.autocommit = True
            Connection.__isInitialized = True
            Connection.startPingTask()
            ret = True
            log(str=f'DB Connetion established')
        except (Exception, psycopg2.DatabaseError) as error:
            log(str=f"Cannot connect to database: {error}",logLevel=LOG_ERROR)
        return ret

    def isInitialized() -> bool:
        return Connection.__isInitialized
    
    def isActive() -> bool:
        return Connection.__isInitialized and Connection.getConnection().closed == 0

    def getBaseImageUrl():
        return Connection.__baseImageUrl

    def reconnect() -> bool:
        # check if connection was initialized before
        if (not Connection.isInitialized()):
            log(str='Connection was not initialized. Cannot reconnect.', logLevel=LOG_ERROR)
            return False
        if (not Connection.isActive()):
            Connection.pingStop()
            return Connection.__newConnection(test=Connection.__test)

    # Execute query with params
    # If 'all' == True - execute fetchAll()/ otherwise fetchOne()
    # Returns:
    #   None - issue with execution
    #   NOT_FOUND - if nothing found
    #   [result] - array with one found item
    def executeQuery(query, params={}, all=False):
        if (not Connection.isActive() and not Connection.reconnect()):
            log(str=f'Cannot execute query "{query}" with "{params}" (all={all}): connection is not initialized', logLevel=LOG_ERROR)
            return None
        ret = Connection.NOT_FOUND
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            try:
                cur.execute(query=query,vars=params)
                if (all):
                    res = cur.fetchall()
                    if (res):
                        if (len(res) == 0):
                            ret = Connection.NOT_FOUND
                        else:
                            ret = []
                            for i in res:
                                tmp = []
                                for j in i:
                                    tmp.append(j)
                                ret.append(tmp)
                else:
                    res = cur.fetchone()
                    if (res):
                        if (len(res) == 0):
                            ret = Connection.NOT_FOUND
                        else:
                            ret = []
                            for i in res:
                                ret.append(i)
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'Failed execute query "{query}" with params "{params}" (all={all}): {error}',logLevel=LOG_ERROR)
                return None
        return ret

    # Get all settings for user
    # Returns:
    #   NOT_FOUND - no such user
    #   None - issue with DB
    #   [game_type,game_complexity]
    def getUserSetting(userName):
        # Get user id
        userId = Connection.getUserIdByName(name=userName)
        if (dbFound)(result=userId):
            query = 'select game_type, game_complexity from users where id=%(id)s'
            ret = Connection.executeQuery(query=query,params={'id':userId})
        else:
            ret = userId
        return ret

    # Get setting value. Returns key or None if not found or if connection is not initialized
    def getSettingValue(key):
        query = 'select value from settings where key=%(key)s'
        ret = Connection.executeQuery(query=query,params={'key': key})
        if (dbFound(result=ret)):
            ret = ret[0]
        return ret

    # Update DB
    def updateDB(creators, titles, years, intYears, orientations) -> None:
        if (not Connection.isInitialized()):
            log(str="Cannot updateDB - connection is not initialized", logLevel=LOG_ERROR)
            return
        Connection.bulkCreatorInsert(creators=creators)
        mCreators = getImageCreatorMap(creators=creators, titles=titles, years=years, intYears=intYears, orientations=orientations)
        Connection.bulkImageInsersion(mCreators=mCreators)

    # Update DB - remove non existing creators and images
    def updateDB2(creators, titles, years, intYears, orientations) -> None:
        if (not Connection.isInitialized()):
            log(str="Cannot updateDB2 - connection is not initialized", logLevel=LOG_ERROR)
            return
        mCreators = getImageCreatorMap(creators=creators, titles=titles, years=years, intYears=intYears, orientations=orientations)
        Connection.bulkImageDeletion(mCreators=mCreators)
        Connection.bulkCreatorsDelete(creators=creators)

    # Bulk creators deletion
    def bulkCreatorsDelete(creators) -> None:
        creatorsSet = set(creators)
        # Get all creators from DB
        creators = Connection.getAllCreatorsInfo()
        if (creators != None):
            # Create set of creators in DB - creatorsSetDB
            creatorsSetDb = set()
            for creator in creators:
                creatorsSetDb.add(creator['name'])
            # For each creator in creatorsrSet check that it is in creatorsSetDB
            for creator in creatorsSetDb:
                if (creator not in creatorsSet):
                    # Delete creator
                    log(str=f'Delete creator {creator}',logLevel=LOG_DEBUG)
                    creatorId = Connection.getCreatorIdByName(creator=creator)
                    Connection.deleteCreator(id=creatorId)
        else:
            log(str=f'Cannot get creators from DB',logLevel=LOG_ERROR)

    # Returns:
    #    creatorID by name
    #    None if not found or connection not initialized
    #    NOT_FOUND - not found creator
    def getCreatorIdByName(creator):
        query = "SELECT id FROM creators WHERE name =%(creator)s"
        ret = Connection.executeQuery(query=query,params={'creator':creator})
        if (dbFound(result=ret)):
            ret = ret[0]
        return ret

    # Bulk image deletion
    def bulkImageDeletion(mCreators) -> None:
        if (not Connection.isActive() and not Connection.reconnect()):
            log(str="Cannot bulk image delete - connection is not initialized",logLevel=LOG_ERROR)
            return
        # Get all images from DB again
        images = Connection.getAllImages(creatorName=True)
        if (dbFound(result=images)):
            for imageInfo in images:
                iYear = imageInfo['year']
                iName = imageInfo['name']
                pName = imageInfo['creatorName']
                # Get all images for the creator
                cImages = mCreators.get(pName)
                # Go through all images of creator
                found = False
                if (cImages):
                    for image in cImages:
                        if ((image[0] == iName) and (image[2] == iYear)):
                            found = True
                            break
                if (not found):
                    # Delete image
                    log(str=f'Delete image (no image in S3) {pName} - {iName} - {iYear}',logLevel=LOG_DEBUG)
                    Connection.deleteImage(id=imageInfo['id'])
                    continue
        else:
            log(str=f'No images found in DB',logLevel=LOG_WARNING)

    # Check if creator exists in DB
    # Returns:
    #    None if connection is not initialized or error during query
    #    True if exists
    #    False if not exists
    def checkCreatorExists(creatorId) -> bool:
        query = "SELECT id FROM creators WHERE id =%(cId)s"
        ret = Connection.executeQuery(query=query,params={'cId':creatorId})
        if (dbFound(result=ret)):
            ret = True
        else:
            ret = False
        return ret

    # Get all images from DB
    # Returns:
    #   ['imageInfo1',...] - array of image info
    #   None - in case of error
    def getAllImages(creatorName=False):
        fName = Connection.getAllImages.__name__
        images = []
        query = f"""select i.id, i.creator, i.year, i.name
                    from images as i
                """
        if (creatorName):
            query = f"""select i.id, i.creator, i.year, i.name, c.name
                        from images as i join creators as c on i.creator=c.id
                    """
        ret = Connection.executeQuery(query=query,params={},all=True)
        if (dbFound(result=ret)):
            for i in ret:
                # Fill out creator info
                image = {}
                image['id'] = i[0]
                image['creatorId'] = i[1]
                image['year'] = i[2]
                image['name'] = i[3]
                if (creatorName):
                    image['creatorName'] = i[4]
                images.append(image)
        else:
            log(str=f'{fName}: DB issue',logLevel=LOG_ERROR)
            return None
        return images

    # Returns:
    #    creatorInfo by id {'id':N,...}
    #    None DB issue or connection not initialized
    #    NOT_FOUND - not found creator
    def getCreatorInfoById(creatorId):
        if (not creatorId):
            log(str='getCreatorInfoById: creatorID is not passed',logLevel=LOG_ERROR)
            return Connection.NOT_FOUND
        query = "SELECT id,name,gender,country,birth,death,complexity FROM creators WHERE id =%(id)s"
        ret = Connection.executeQuery(query=query,params={'id':creatorId})
        if (dbFound(result=ret)):
            creatorInfo = dbGetCreatorInfo(queryResult=ret)
            ret = creatorInfo
        return ret

    # Returns:
    #    creatorName by id
    #    None DB issue or connection not initialized
    #    NOT_FOUND - not found creator
    def getCreatorNameById(creatorId):
        query = "SELECT name FROM creators WHERE id =%(id)s"
        ret = Connection.executeQuery(query=query,params={'id':creatorId})
        if (dbFound(result=ret)):
            ret = ret[0]
        return ret

    # Returns 'n' creatorIDs or None if connection not initialized or issue with DB
    def getRandomCreatorIds(complexity, n = 1):
        query = "SELECT id FROM creators WHERE complexity<=%(c)s ORDER BY RANDOM() LIMIT %(n)s"
        ret = Connection.executeQuery(query=query,params={'c':complexity, 'n':n},all=True)
        if (dbFound(result=ret)):
            if (n == 1):
                ret = ret[0]
            else:
                ids = []
                for i in ret:
                    ids.append(i)
                ret = ids
        return ret

    # Returns 'n' imageIds or None if connection not initialized or issue with DB
    def getRandomImageIdsOfCreator(creatorId, n = 1):
        query = "SELECT id FROM images where creator=%(creator)s ORDER BY RANDOM() LIMIT %(n)s"
        ret = Connection.executeQuery(query=query,params={'creator':creatorId, 'n':n},all=True)
        if (dbFound(result=ret)):
            if (n == 1):
                ret = ret[0]
            else:
                ids = []
                for i in ret:
                    ids.append(i)
                ret = ids
        return ret

    # Returns 'n' imageIds or None if connection not initialized or issue with DB
    def getRandomImageIdsOfOtherCreators(creatorId, complexity, n, range = (None, None)):
        if ((len(range) != 2)):
            log(str=f'Wrong range format provided: {range}',logLevel=LOG_ERROR)
            range = (None, None)
        params = {'c':creatorId, 'com':complexity, 'n':n}
        query2 = ''
        if ((range[0] != None) and (range[1] != None)):
            query2 = ' and (i.year > %(start)s and i.year < %(end)s)'
            params['start'] = range[0]
            params['end'] = range[1]
            pass
        #query = "SELECT id FROM images where creator!=%(creator)s ORDER BY RANDOM() LIMIT %(n)s"
        query = f'''
            SELECT i.id FROM images as i join creators as c on i.creator=c.id
            where creator!=%(c)s and complexity<=%(com)s {query2}
            ORDER BY RANDOM()
            LIMIT %(n)s;
        '''
        ret = Connection.executeQuery(query=query,params=params,all=True)
        if (dbFound(result=ret)):
            if (n == 1):
                ret = ret[0]
            else:
                ids = []
                for i in ret:
                    ids.append(i)
                ret = ids
        return ret

    # Gets 'n' images of creator (or any creator if None) for complexity
    # Returns:
    #   [id1, id2,...] - 'n' imageIds
    #   None if connection not initialized or issue with DB
    def getRandomImageIdsOfAnyCreator(complexity, creatorId=None, n = 1):
        params = {'c':complexity, 'n':n}
        query_start = "SELECT i.id FROM images as i join creators as c on i.creator = c.id where c.complexity<=%(c)s"
        query_middle =''
        if (creatorId):
            query_middle = ' and c.id=%(cId)s'
            params['cId'] = creatorId
        query_end = " ORDER BY RANDOM() LIMIT %(n)s"
        query = query_start + query_middle + query_end
        ret = Connection.executeQuery(query=query, params=params)  
        if (dbFound(result=ret)):
            if (n == 1):
                ret = ret[0]
            else:
                ids = []
                for i in ret:
                    ids.append(i)
                ret = ids
        return ret      

    # Get image id with creatorId.
    # Returns:
    #    None if connection is not initialized or error during query
    #    [id] - with image id
    #    NOT_FOUND - if not found
    def getImageIdByCreatorId(creatorId, image, year):
        query = f"SELECT id FROM images WHERE creator =%(cId)s AND name =%(image)s AND year_str = %(year)s"
        ret = Connection.executeQuery(query=query,params={'cId':creatorId,'image':image,'year':year})
        if (dbFound(result=ret)):
            ret = ret[0]
        return ret

    # Get image id with creator name
    # Returns:
    #   None - connection not initialized or issue during query
    #   [id] - id of found image
    #   NOT_FOUND - image not found
    def getImageIdByCreatorName(creator, image, year):
        query = f"select i.id from images as i join creators as c on i.creator = c.id where c.name=%(cr)s AND i.name =%(image)s AND i.year_str = %(y)s"
        ret = Connection.executeQuery(query=query,params={'cr':creator,'image':image,'y':year})
        if (dbFound(result=ret)):
            ret = ret[0]
        return ret

    # Get user by name
    # Return:
    #   None - something wrong with connection/query
    #   id - user id
    #   NOT_FOUND - no such user
    def getUserIdByName(name):
        ret = dbLibCheckUserName(user_name=name)
        if (not ret):
            return Connection.NOT_FOUND
        query = f"SELECT id FROM users WHERE name = %(name)s"
        ret = Connection.executeQuery(query=query,params={'name':name})
        if (dbFound(result=ret)):
            ret = ret[0]
        return ret

    # Delete user - returns True/False
    def deleteUser(id) -> bool:
        fName = Connection.deleteUser.__name__
        ret = False
        if (not Connection.isActive() and not Connection.reconnect()):
            log(str=f"{fName}: Cannot delete user - connection is not initialized",logLevel=LOG_ERROR)
            return ret
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = "DELETE from users where id = %(user)s"
            try:
                cur.execute(query=query, vars={'user':id})
                log(str=f'{fName}: Deleted user: {id}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'{fName}: Failed delete user {id}: {error}',logLevel=LOG_ERROR)
        return ret
    
    # Insert new user in DB. Returns True is success or False otherwise
    def insertUser(userName, gameType=None, complexity=None) -> bool:
        fName = Connection.insertUser.__name__
        if (not Connection.isActive() and not Connection.reconnect()):
            log(str=f"{fName}: Cannot insert user - connection is not initialized",logLevel=LOG_ERROR)
            return False
        ret = dbLibCheckUserName(user_name=userName)
        if (not ret):
            log(str=f"{fName}: Cannot insert user -  invalid name format",logLevel=LOG_ERROR)
            return False
        if ((complexity == None) or (not dbLibCheckGameComplexity(game_type=complexity))):
            complexity = Connection.getDefaultComplexity()
        if ((gameType == None) or (not dbLibCheckGameType(game_type=gameType))):
            gameType = Connection.getDefaultGameType()

        ret = False
        conn = Connection.getConnection()
        # Check for duplicates
        retUser = Connection.getUserIdByName(name=userName)
        if (retUser == None): # error with DB
            log(str=f'{fName}: Cannot get user from DB: {userName}',logLevel=LOG_ERROR)
            return False
        if (dbNotFound(result=retUser)):
            with conn.cursor() as cur:
                query = "INSERT INTO users ( name,game_type,game_complexity ) VALUES ( %(u)s,%(t)s,%(c)s )"
                try:
                    cur.execute(query=query, vars={'u':userName,'t':gameType,'c':complexity})
                    log(str=f'{fName}: Inserted user: {userName} - {gameType} - {complexity}')
                    ret = True
                except (Exception, psycopg2.DatabaseError) as error:
                    log(str=f'{fName}: Failed insert user {userName}: {error}',logLevel=LOG_ERROR)
        else:
            log(str=f'{fName}: Trying to insert duplicate user: {userName}',logLevel=LOG_WARNING)
            ret = True # Return true for now - probably wrong
        return ret

    # Delete creator - returns nothing
    def deleteCreator(id) -> None:
        fName = Connection.deleteCreator.__name__
        if (not Connection.isActive() and not Connection.reconnect()):
            log(str=f"{fName}: ERROR: cannot delete creator - connection is not initialized",logLevel=LOG_ERROR)
            return
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = "DELETE from creators where id = %(id)s"
            try:
                cur.execute(query=query, vars={'id':id})
                log(str=f'{fName}: Deleted creator: {id}')
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'{fName}: Failed delete creator {id}: {error}',logLevel=LOG_ERROR)

    # Insert new creator. Returns True is success or False otherwise
    def insertCreator(creator) -> bool:
        fName = Connection.insertCreator.__name__
        if (not Connection.isActive() and not Connection.reconnect()):
            log(str=f"{fName}: Cannot insert creator - connection is not initialized",logLevel=LOG_ERROR)
            return False
        ret = False
        # Check for duplicates
        retCreator = Connection.getCreatorIdByName(creator=creator)
        if (retCreator == None): # error with DB
            log(str=f'Cannot get creator from DB: {creator}',logLevel=LOG_ERROR)
            return False
        if (dbNotFound(result=retCreator)):
            conn = Connection.getConnection()
            with conn.cursor() as cur:
                query = "INSERT INTO creators ( name, complexity ) VALUES ( %(cr)s , 5 )" # Put complexity 5 to decide later
                try:
                    cur.execute(query=query, vars={'cr':creator})
                    log(str=f'{fName}: Inserted creator: {creator}')
                    ret = True
                except (Exception, psycopg2.DatabaseError) as error:
                    log(str=f'{fName}: Failed insert creator {creator}: {error}',logLevel=LOG_ERROR)
                    ret = False
        else:
            log(str=f'{fName}: Trying to insert duplicate creator: {creator}',logLevel=LOG_WARNING)
            ret = True # Probably wrong here
        return ret

    # Bulk creators insertion
    def bulkCreatorInsert(creators) -> None:
        creatorsSet = set(creators)
        # Get all creators from DB
        creators = Connection.getAllCreatorsInfo()
        if (dbFound(result=creators)):
            # Create set of creators in DB - creatorSetDB
            creatorsSetDb = set()
            for c in creators:
                creatorsSetDb.add(c['name'])
            # For each creator in creatorSet check that it is in creatorSetDB
            for c in creatorsSet:
                if (c not in creatorsSetDb):
                    # Insert new creator
                    Connection.insertCreator(creator=c)
        else:
            log(str=f'No creators found in DB: {creators}',logLevel=LOG_ERROR)

    # Get all creators from DB
    # Returns:
    #   [[creatorInfo],...] - array of creators info
    #   None - issue with DB
    def getAllCreatorsInfo():
        fName = Connection.getAllCreatorsInfo.__name__
        creators = []
        query = "select id,name,gender,country,birth,death,complexity from creators"
        ret = Connection.executeQuery(query=query,params={},all=True)
        if (dbFound(result=ret)):
            for c in ret:
                # Fill out creators info
                creator = dbGetCreatorInfo(queryResult=c)
                creators.append(creator)
        else:
            return None
        return creators

    # Delete image - returns nothing
    def deleteImage(id) -> None:
        fName = Connection.deleteImage.__name__
        if (not Connection.isActive() and not Connection.reconnect()):
            log(str=f"{fName}: Cannot delete image - connection is not initialized",logLevel=LOG_ERROR)
            return
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = "DELETE from images where id = %(id)s"
            try:
                cur.execute(query=query, vars={'id':id})
                log(str=f'{fName}: Deleted image: {id}')
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'{fName}: Failed delete image {id}: {error}',logLevel=LOG_ERROR)

    # Insert image in DB. Returns True is success or False otherwise
    def insertImage(creatorId, image, year, intYear, orientation) -> bool:
        fName = Connection.insertImage.__name__
        if (not Connection.isActive() and not Connection.reconnect()):
            log(str=f"{fName}: Cannot insert image - connection is not initialized",logLevel=LOG_ERROR)
            return False
        # Check for duplicates
        ret = False
        id = Connection.getImageIdByCreatorId(creatorId=creatorId, image=image, year=year)
        if (id is None):
            log(str=f'{fName}: Cannot insert image {creatorId} - {image} - {year}: DB issue',logLevel=LOG_ERROR)
            return False
        if (dbNotFound(result=id)):
            conn = Connection.getConnection()
            with conn.cursor() as cur:
                query = f"INSERT INTO images (creator, name, year_str, year, orientation) VALUES (%(crId)s,%(im)s,%(y)s,%(iY)s,%(o)s)"
                try:
                    cur.execute(query=query, vars={'crId':creatorId, 'im':image,'y':year,'iY':intYear,'o':orientation})
                    log(str=f'Inserted image: {creatorId} - {image} - {year}')
                    ret = True
                except (Exception, psycopg2.DatabaseError) as error:
                    log(str=f'{fName}: Failed insert image {creatorId} - {image} - {year}: {error}',logLevel=LOG_ERROR)
        else:
            log(str=f'{fName}: Trying to insert duplicate image: {creatorId} - {image} - {year}',logLevel=LOG_WARNING)
            ret = True # probably wrong here
        return ret

    # Bulk image insertion
    def bulkImageInsersion(mCreators) -> None:
        fName = Connection.bulkImageInsersion.__name__
        # Pass through all the creators
        for creator in mCreators:
            # Check that creator is in DB
            creatorId = Connection.getCreatorIdByName(creator=creator)
            if (creatorId is None):
                log(str=f'{fName}: Error getting creator from DB: {creator}',logLevel=LOG_ERROR)
                continue
            if (dbNotFound(result=creatorId)):
                log(str=f'{fName}: No creator in DB: {creator}',logLevel=LOG_ERROR)
                continue
            # Get all imsages for creator
            imagesDB = Connection.getAllImagesOfCreator(creatorId=creatorId)
            images = mCreators[creator]
            # Pass through all the images of the creator
            for imageData in images:
                image = getImageFromData(imageData=imageData)
                year = getYearFromData(imageData=imageData)
                intYear = getIntYearFromData(imageData=imageData)
                orientation = getOrientationFromData(imageData=imageData)

                if (not Connection.findImageByTitleAndYear(imagesDB=imagesDB, title=image, year=year)):
                    # Insert tiles, year, intYear, orientation
                    Connection.insertImage(creatorId=creatorId, image=image, year=year, intYear=intYear, orientation=orientation)

    def findImageByTitleAndYear(imagesDB, title, year) -> bool:
        if (imagesDB == None): # No images for creator - this is the first one
            return False
        for imageInfo in imagesDB:
            if (imageInfo['imageName'] == title and imageInfo['yearStr'] == year):
                return True
        return False

    # Get all images of the creator
    # Returns:
    #   ['imageInfo1',...] - array of image info
    #   None - in case of error
    def getAllImagesOfCreator(creatorId):
        fName = Connection.getAllImagesOfCreator.__name__
        images = []
        query = f"select i.creator,c.name,i.name,i.year,i.year_str,i.orientation from images as i join creators as c on i.creator = c.id where c.id = %(id)s"
        ret = Connection.executeQuery(query=query,params={'id':creatorId},all=True)
        if (dbFound(result=ret)):
            for i in ret:
                # Fill out creators info
                image = dbGetImageInfo(queryResult=i)
                images.append(image)
        return images

    # Get URL by image id
    # Returns:
    #   URL - if success
    #   NOT_FOUND - if image not found
    #   None - if failed connection or no such image
    def getImageUrlById(id):
        fName = Connection.getImageUrlById.__name__
        image = Connection.getImageInfoById(id=id)
        if (image == None):
            log(str=f'{fName}: Cannot get image URL for image {id}: DB issue',logLevel=LOG_ERROR)
            return None
        elif (dbNotFound(result=image)):
            log(str=f'{fName}: Cannot get image URL for image {id}: no such image in DB',logLevel=LOG_ERROR)
            return Connection.NOT_FOUND
        baseUrl = Connection.getBaseImageUrl()
        url = None
        if (baseUrl):
            cName = image['creatorName']
            iName = image['imageName']
            yearStr = image['yearStr']
            url = buildImgUrl(base_url=baseUrl, creator=cName, title=iName, year=yearStr)
        return url

    # Get image info from DB by id
    # Returns:
    #   [{creatorId, creatorName, imageName, year, year_str, orientation}]
    #   NOT_FOUND - if no such image
    #   None - if issue with connection
    def getImageInfoById(id):
        query = f"select i.creator,c.name,i.name,i.year,i.year_str,i.orientation from images as i join creators as c on i.creator = c.id where i.id = %(id)s"
        ret = Connection.executeQuery(query=query,params={'id':id})
        if (dbFound(result=ret)):
            imageInfo = dbGetImageInfo(queryResult=ret)
            ret = imageInfo
        return ret

    # Update image orientation. Returns nothing
    def updateImageOrientation(creator, image, year, orientation) -> bool:
        fName = Connection.updateImageOrientation.__name__
        if (not Connection.isActive() and not Connection.reconnect()):
            log(str=f"{fName}: Cannot update image orientation - connection is not initialized",logLevel=LOG_ERROR)
            return False
        id = Connection.getImageIdByCreatorName(creator=creator, image=image, year=year)
        if (id is None):
            log(str=f'{fName}: Cannot update image {creator} - {image} - {year} orientation: DB issue',logLevel=LOG_ERROR)
            return False
        ret = False
        if (dbFound(result=id)):
            conn = Connection.getConnection()
            with conn.cursor() as cur:
                query = 'update images set orientation=%(o)s where id = %(id)s'
                try:
                    cur.execute(query=query,vars={'o':orientation,'id':id[0]})
                    log(str=f'{fName}: Updated orienttion: {creator} - {image} - {year}: orientation {orientation}')
                    ret = True
                except (Exception, psycopg2.DatabaseError) as error:
                    log(str=f'{fName}: Failed update orienttion {creator} - {image} - {year}: {error}',logLevel=LOG_ERROR)
        else:
            log(str=f"{fName}: Cannot set orientation for (image not found): {creator} - {image} - {year}",logLevel=LOG_ERROR)
        return ret

    # Delete game - returns true/false
    def deleteGame(id) -> bool:
        fName = Connection.deleteGame.__name__
        ret = False
        if (not Connection.isActive() and not Connection.reconnect()):
            log(str=f"{fName}: Cannot delete game - connection is not initialized",logLevel=LOG_ERROR)
            return ret
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = "DELETE from games where id = %(id)s"
            try:
                cur.execute(query=query, vars={'id':id})
                log(str=f'{fName}: Deleted game: {id}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'{fName}: Failed delete game {id}: {error}',logLevel=LOG_ERROR)
        return ret

    # Clear all current games on all users
    def clearAllCurrentGames() -> bool:
        fName = Connection.clearAllCurrentGames.__name__
        if (not Connection.isActive() and not Connection.reconnect()):
            log(str=f"{fName}: Cannot clear all current games - connection is not initialized",logLevel=LOG_ERROR)
            return False
        ret = False
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'update users set current_game=%(n)s'
            try:
                cur.execute(query=query,vars={'n':None})
                retVal = cur.fetchone()
                log(str=f'{fName}: All current games cleared: {retVal}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'{fName}: Failed clearing current games:: {error}',logLevel=LOG_ERROR)
        return ret

    # Insert new user in DB
    # Returns:
    #   id - id of new game
    #   None - otherwise
    def insertGame(user_id, game_type, correct_answer, question, complexity):
        fName = Connection.insertGame.__name__
        # Checks first
        if (not dbLibCheckUserId(user_id=user_id)):
            return None
        if (not dbLibCheckGameType(game_type=game_type)):
            return None
        if (not dbLibCheckGameComplexity(game_type=complexity)):
            return None
        if (not Connection.isActive() and not Connection.reconnect()):
            log(str=f"{fName}: Cannot insert game for user {user_id}- connection is not initialized",logLevel=LOG_ERROR)
            return None
        ret = None
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'INSERT INTO games ("user","type",correct_answer,question,created,complexity) VALUES ( %(u)s, %(t)s, %(ca)s, %(q)s, NOW(), %(com)s) returning id'
            try:
                cur.execute(query=query, vars={'u':user_id,'t':game_type,'ca':correct_answer,'q':question,'com':complexity})
                row = cur.fetchone()
                if (row):
                    ret = row[0]
                    log(str=f'Inserted game: {ret}')
                else:
                    log(str=f'{fName}: Cannot get id of new game: {query}',logLevel=LOG_ERROR)
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'{fName}: Failed insert game for user {user_id}: {error}',logLevel=LOG_ERROR)
        return ret

    # Get game by id
    # Returns:
    #   None - issue with DB
    #   NOT_FOUND - no such game
    #   {gameInfo} - game info
    def getGameInfoById(id):
        query = 'select id, "user","type",correct_answer,question,user_answer,result,created,finished,complexity from games where id = %(id)s'
        ret = Connection.executeQuery(query=query,params={'id':id})
        if (dbFound(result=ret)):
            gameInfo = dbGetGameInfo(queryResult=ret)
            ret = gameInfo
        return ret

    # Get N creators
    # Input:
    #   n - number of creators to returl
    #   exclude - creator id to exclude
    #   complexity - game complexity
    # Returns:
    #   None - issue with DB
    #   [{'creatorId':id,'creatorName':name}] - creators
    def getNCreators(n, exclude, complexity, range=(None,None)):
        if ((len(range) != 2)):
            log(str=f'Wrong range format provided for creator: {range}',logLevel=LOG_ERROR)
            range = (None, None)
        params = {'e':exclude, 'c':complexity,'n':n}
        query2 = ''
        if ((range[0] != None) and (range[1] != None)):
            query2 = ' and ((birth is %(start1)s or birth > %(start2)s) and (death is %(end1)s or death < %(end2)s))'
            params['start1'] = None
            params['start2'] = range[0]
            params['end1'] = None
            params['end2'] = range[1]
        query = f'''
            SELECT id,name FROM creators
            where id != %(e)s and complexity <= %(c)s {query2}
            ORDER BY RANDOM()
            LIMIT %(n)s;
        '''
        ret = Connection.executeQuery(query=query,params=params,all=True)
        if (dbFound(result=ret)):
            retArr = []
            for creator in ret:
                cInfo = {}
                cInfo['creatorId'] = creator[0]
                cInfo['creatorName'] = creator[1]
                retArr.append(cInfo)
            ret = retArr
        return ret

    # Finish game
    # Input:
    #   gameId - game id
    #   answer - user_answer
    # Result:
    #   False - issue with DB
    #   True - successful finish
    def finishGame(gameId, answer) -> bool:
        fName = Connection.finishGame.__name__
        if (not Connection.isActive() and not Connection.reconnect()):
            log(str=f"{fName}: Cannot finish game - connection is not initialized",logLevel=LOG_ERROR)
            return False
        gameInfo = Connection.getGameInfoById(id=gameId)
        if (gameInfo is None):
            log(str=f'{fName}: cannot get game {gameId}: DB issue',logLevel=LOG_ERROR)
            return False
        ret = False
        if (dbFound(result=gameInfo)):
            # Check that game is not finished yet
            isFinished = dbLibCheckIfGameFinished(gameInfo=gameInfo)
            if (isFinished):
                log(str=f'{fName}: Game {gameId} is already finished')
                return False

            # Check result by answer
            correct_answer = gameInfo['correct_answer']
            answer = int(answer)
            dbResult = 'false'
            if (answer == correct_answer):
                dbResult = 'true'
            conn = Connection.getConnection()
            with conn.cursor() as cur:
                query = 'update games set finished = NOW(), result=%(r)s, user_answer=%(a)s where id = %(id)s'
                try:
                    cur.execute(query=query,vars={'r':dbResult,'id':gameId, 'a':answer})
                    log(str=f'{fName}: Updated game: {gameId} - {dbResult}')
                    ret = True
                except (Exception, psycopg2.DatabaseError) as error:
                    log(str=f'{fName}: Failed finish game {gameId}: {error}',logLevel=LOG_ERROR)
        else:
            log(str=f"{fName}: Cannot find game {gameId}: game not found",logLevel=LOG_ERROR)
        return ret

    # Check is game is finished. Returns True/False
    def checkGameIsFinished(gameId) -> bool:
        gameInfo = Connection.getGameInfoById(id=gameId)
        if (dbFound(result=gameInfo)):
            return (dbLibCheckIfGameFinished(gameInfo=gameInfo))
        return False

    # Get game types from DB
    # Returns:
    #   [[game_type_id, name, question]]
    #   NOT_FOUND - no game_types in DB
    #   None - issue with connection
    def getGameTypesFromDb():
        query = 'select id,name,question from game_types order by id asc'
        ret = Connection.executeQuery(query=query,params={},all=True)
        return ret

    # Get game types from cache
    # Returns:
    #   [[game_type_id, name, question]]
    #   None - connection not initialized
    def getGameTypes():
        if (Connection.isInitialized()):
            return Connection.__gameTypes
        return None
    
    # Get game types from DB
    # Returns:
    #   [[complexity_id, name]]
    #   NOT_FOUND - no complexities in DB
    #   None - issue with connection
    def getComplexitiesFromDb():
        query = 'select id,name from complexity'
        ret = Connection.executeQuery(query=query,params={},all=True)
        return ret

    # Get game types from cache
    # Returns:
    #   [[game_type_id, name, question]]
    #   None - connection not initialized
    def getComplexities():
        if (Connection.isInitialized()):
            return Connection.__complexities
        return None

    # Get default game type from cache
    # Returns:
    #   game_type_id
    #   None - connection not initialized
    def getDefaultGameType():
        if (Connection.isInitialized()):
            return Connection.__defaultGameType
        return None
    
    # Get default complexity from cache
    # Returns:
    #   game_complexity
    #   None - connection not initialized
    def getDefaultComplexity():
        if (Connection.isInitialized()):
            return Connection.__defaultComplexity
        return None

    # List all games for the user
    # Input:
    #   userId - user id
    # Returns:
    #   None - error occured
    #   [[gameInfo1], [gameInfo2], etc...] - list of appropriate games
    #   [] - no games of the user
    def getAllGamesList(userId):
        ret = dbLibCheckUserId(user_id=userId)
        if (not ret):
            return None
        query = 'select id,"user","type",correct_answer,question,user_answer,result,created,finished,complexity from games where "user"=%(uId)s'
        ret = Connection.executeQuery(query=query,params={'uId':userId},all=True)
        if (dbFound(result=ret)):
            games = []
            for gi in ret:
                gameInfo = dbGetGameInfo(queryResult=gi)
                games.append(gameInfo)
            ret = games
        else:
            ret = []
        return ret

    # List unfinished games for the user
    # Input:
    #   userId - user id
    # Returns:
    #   None - error occured
    #   [[gameInfo1], [gameInfo2], etc...] - list of appropriate games
    def getUnfinishedGamesList(userId):
        ret = dbLibCheckUserId(user_id=userId)
        if (not ret):
            return None
        query = 'select id,"user","type",correct_answer,question,user_answer,result,created,finished,complexity from games where "user"=%(uId)s and result is NULL'
        ret = Connection.executeQuery(query=query,params={'uId':userId}, all=True)
        if (dbFound(result=ret)):
            games = []
            for gi in ret:
                gameInfo = dbGetGameInfo(queryResult=gi)
                games.append(gameInfo)
            ret = games
        else:
            ret = []
        return ret

    # List finished games for the user
    # Input:
    #   userId - user id
    # Returns:
    #   None - error occured
    #   [[gameInfo1], [gameInfo2], etc...] - list of appropriate games
    def getFinishedGamesList(userId):
        ret = dbLibCheckUserId(userId)
        if (not ret):
            return None
        query = 'select id,"user","type",correct_answer,question,user_answer,result,created,finished,complexity from games where "user"=%(uId)s and result is not NULL'
        ret = Connection.executeQuery(query=query,params={'uId':userId},all=True)
        if (dbFound(result=ret)):
            games = []
            for gi in ret:
                gameInfo = dbGetGameInfo(queryResult=gi)
                games.append(gameInfo)
            ret = games
        else:
            ret = []
        return ret

    # Update creator - returns True/False
    def updateCreator(creator) -> bool:
        fName = Connection.updateCreator.__name__
        ret = False
        if (not dbLibCheckCreator(creatorInfo=creator)):
            return False
        cId = creator['id']
        name = creator['name']
        complexity = creator['complexity']
        if (not creator['gender']):
            creator['gender'] = None
        gender = creator['gender']
        if (not creator['birth']):
            creator['birth'] = None
        birth = creator['birth']
        if (not creator['death']):
            creator['death'] = None
        death = creator['death']
        if (not creator['country']):
            creator['country'] = None
        country = creator['country']
        if (not Connection.isActive() and not Connection.reconnect()):
            log(str=f'{fName}: Failed to reconnect to database',logLevel=LOG_ERROR)
            return False
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'update creators set name=%(n)s,gender=%(g)s,birth=%(b)s,death=%(d)s,country=%(c)s,complexity=%(com)s where id = %(id)s'
            try:
                cur.execute(query=query,vars={'id':cId,'g':gender,'b':birth,'d':death,'n':name,'c':country,'com':complexity})
                log(str=f'{fName}: Updated creator: {cId} - {creator}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'{fName}: Failed update creator {creator}: {error}',logLevel=LOG_ERROR)
        return ret

    # Compare 2 creators info
    # Returns: True if everything is equal / False - if any differences
    def compareCreatorInfo(creator, dbCreator) -> bool:
        ret = True
        for k in dbCreator.keys():
            newV = creator.get(k)
            if (not newV):
                newV = None
            if (dbCreator[k] != newV):
                ret = False
                break
        return ret

    # Get current game for user userName
    # Returns:
    # id - current game id
    # None - no current game
    def getCurrentGame(userName):
        fName = Connection.getCurrentGame.__name__
        ret = dbLibCheckUserName(user_name=userName)
        if (not ret):
            log(str=f'{fName}: Incorrect user {userName} provided',logLevel=LOG_ERROR)
            return None
        userId = Connection.getUserIdByName(name=userName)
        if (dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot find user {userName}',logLevel=LOG_ERROR)
            return None
        ret = None
        query = 'select current_game from users where id=%(uId)s'
        currentGame = Connection.executeQuery(query=query, params={'uId':userId})
        if (dbFound(result=currentGame)):
            currentGame = currentGame[0]
            if (currentGame):
                # Check that game is not finished
                ret2 = Connection.checkGameIsFinished(gameId=currentGame)
                if (not ret2): # UnFinished game
                    ret = currentGame
        return ret

    def setCurrentGame(userName, gameId) -> bool:
        return Connection.updateCurrentGame(userName=userName, gameId=gameId)

    def clearCurrentGame(userName) -> bool:
        return Connection.updateCurrentGame(userName=userName, gameId=None)

    # Update current_game for the userId
    # Returns: True - update successful / False - otherwise
    def updateCurrentGame(userName, gameId) -> bool:
        fName = Connection.updateCurrentGame.__name__
        if (not Connection.isActive() and not Connection.reconnect()):
            log(str=f"{fName}: connection is not initialized",logLevel=LOG_ERROR)
            return False
        ret = dbLibCheckUserName(user_name=userName)
        if (not ret):
            log(str=f'{fName}: Incorrect user {userName} provided',logLevel=LOG_ERROR)
            return False
        userId = Connection.getUserIdByName(name=userName)
        if (dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot find user {userName}',logLevel=LOG_ERROR)
            return False
        if (gameId):
            gameInfo = Connection.getGameInfoById(id=gameId)
            if (dbNotFound(result=gameInfo)):
                log(str=f'{fName}: cannot find game {gameId} (user={userName})',logLevel=LOG_ERROR)
                return False
            # Check userId is correct
            if (gameInfo['user'] != userId):
                log(str=f'{fName}: game {gameId} doesnt belong to user {userName} ({userId})',logLevel=LOG_ERROR)
                return False
            # Check that game is finished
            ret = dbLibCheckIfGameFinished(gameInfo=gameInfo)
            if (ret):
                log(str=f'{fName}: cannot set finished game as current (gameId = {gameId}, user={userName})',logLevel=LOG_ERROR)
                return False
        ret = False
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'update users set current_game=%(gId)s where id = %(uId)s'
            try:
                cur.execute(query=query,vars={'gId':gameId,'uId':userId})
                log(str=f'Updated current game: (user={userName} | gameId = {gameId})')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'{fName}: Failed update current game (gameId = {gameId}, user={userName}): {error}',logLevel=LOG_ERROR)
        return ret

    # Get current game data for user userName
    # Returns:
    # id - current game id
    # None - no current game
    def getCurrentGameData(userName):
        fName = Connection.getCurrentGameData.__name__
        ret = dbLibCheckUserName(user_name=userName)
        if (not ret):
            log(str=f'{fName}: Incorrect user {userName} provided',logLevel=LOG_ERROR)
            return None
        userId = Connection.getUserIdByName(name=userName)
        if (dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot find user {userName}',logLevel=LOG_ERROR)
            return None
        ret = None
        query = 'select game_data from users where id=%(uId)s'
        currentGameData = Connection.executeQuery(query=query, params={'uId':userId})
        if (dbFound(result=currentGameData)):
            currentGameData = currentGameData[0]
            if (currentGameData):
                ret = currentGameData
        return ret

    def setCurrentGameData(userName, gameData) -> bool:
        return Connection.updateCurrentGameData(userName=userName, gameData=gameData)

    def clearCurrentGameData(userName) -> bool:
        return Connection.updateCurrentGameData(userName=userName, gameData=None)

    # Update game_data for the userId
    # Returns: True - update successful / False - otherwise
    def updateCurrentGameData(userName, gameData) -> bool:
        fName = Connection.updateCurrentGameData.__name__
        if (not Connection.isActive() and not Connection.reconnect()):
            log(str=f"{fName}: connection is not initialized",logLevel=LOG_ERROR)
            return False
        ret = dbLibCheckUserName(user_name=userName)
        if (not ret):
            log(str=f'{fName}: Incorrect user {userName} provided',logLevel=LOG_ERROR)
            return False
        userId = Connection.getUserIdByName(name=userName)
        if (dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot find user {userName}',logLevel=LOG_ERROR)
            return False
        ret = False
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'update users set game_data=%(gd)s where id = %(uId)s'
            try:
                cur.execute(query=query,vars={'gd':gameData,'uId':userId})
                log(str=f'{fName}: Updated current game data: (user={userName} | gameData = {gameData})')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'{fName}: Failed update current game data (gameData = {gameData}, user={userName}): {error}',logLevel=LOG_ERROR)
        return ret

    # Get user game type
    # Returns:
    #   game_type - game type
    #   None - if error
    def getUserGameType(userName):
        fName = Connection.getUserGameType.__name__
        ret = None
        ret2 = dbLibCheckUserName(user_name=userName)
        if (not ret2):
            log(str=f'{fName}: Incorrect user {userName} provided',logLevel=LOG_ERROR)
            return ret
        userId = Connection.getUserIdByName(name=userName)
        if (dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot find user {userName}',logLevel=LOG_ERROR)
            return ret
        query = f'select game_type from users where id=%(uId)s'
        ret2 = Connection.executeQuery(query=query,params={'uId':userId})
        if (dbFound(result=ret2)):
            ret = ret2[0]
        return ret

    # Update game type for the userId
    # Returns: True - update successful / False - otherwise
    def updateUserGameType(userName, gameType) -> bool:
        fName = Connection.updateUserGameType.__name__
        if (not Connection.isActive() and not Connection.reconnect()):
            log(str=f"{fName}: connection is not initialized",logLevel=LOG_ERROR)
            return False
        ret = dbLibCheckUserName(user_name=userName)
        if (not ret):
            log(str=f'{fName}: Incorrect user {userName} provided',logLevel=LOG_ERROR)
            return False
        userId = Connection.getUserIdByName(name=userName)
        if (dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot find user {userName}',logLevel=LOG_ERROR)
            return False
        if (not dbLibCheckGameType(game_type=gameType)):
            log(str=f'{fName}: Wrong game type format: {gameType}',logLevel=LOG_ERROR)
            return False
        ret = False
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'update users set game_type=%(gt)s where id = %(uId)s'
            try:
                cur.execute(query=query,vars={'gt':gameType,'uId':userId})
                log(str=f'{fName}: Updated game type: (user={userName} | gameType = {gameType})')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'{fName}: Failed update game type (gameType = {gameType}, user={userName}): {error}',logLevel=LOG_ERROR)
        return ret

   # Get user complexity
    # Returns:
    #   complexity - complexity
    #   None - if error
    def getUserComplexity(userName):
        fName = Connection.getUserComplexity.__name__
        ret = None
        ret2 = dbLibCheckUserName(user_name=userName)
        if (not ret2):
            log(str=f'{fName}: Incorrect user {userName} provided',logLevel=LOG_ERROR)
            return ret
        userId = Connection.getUserIdByName(name=userName)
        if (dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot find user {userName}',logLevel=LOG_ERROR)
            return ret
        query = f'select game_complexity from users where id=%(uId)s'
        ret2 = Connection.executeQuery(query=query,params={'uId':userId})
        if (dbFound(result=ret2)):
            ret = ret2[0]
        return ret

    # Update users complexity for the userId
    # Returns: True - update successful / False - otherwise
    def updateUserComplexity(userName, complexity) -> bool:
        fName = Connection.updateUserComplexity.__name__
        if (not Connection.isActive() and not Connection.reconnect()):
            log(str=f"{fName}: connection is not initialized",logLevel=LOG_ERROR)
            return False
        ret = dbLibCheckUserName(user_name=userName)
        if (not ret):
            log(str=f'{fName}: Incorrect user {userName} provided',logLevel=LOG_ERROR)
            return False
        userId = Connection.getUserIdByName(name=userName)
        if (dbNotFound(result=userId)):
            log(str=f'{fName}: Cannot find user {userName}',logLevel=LOG_ERROR)
            return False
        if (not dbLibCheckGameComplexity(game_type=complexity)):
            log(str=f'{fName}: Wrong complexity format: {complexity}',logLevel=LOG_ERROR)
            return False
        ret = False
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'update users set game_complexity=%(c)s where id = %(uId)s'
            try:
                cur.execute(query=query,vars={'c':complexity,'uId':userId})
                log(str=f'{fName}: Updated complexity: (user={userName} | complexity = {complexity})')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                log(str=f'{fName}: Failed update complexity (complexity = {complexity}, user={userName}): {error}')
        return ret

    # Update creators info from CSV file
    def updateCreatorsFromCSV() -> None:
        creators = readCreatorsCSV()
        if (not creators):
            log(str='No creators for update',logLevel=LOG_ERROR)
            return
        creatorsInDB = Connection.getAllCreatorsInfo()
        if (not dbFound(result=creatorsInDB)):
            log(str='No creators in DB',logLevel=LOG_ERROR)
            return
        for creator in creators:
            if (not dbLibCheckCreator(creatorInfo=creator)):
                log(str=f'updateCreatorsFromCSV: Invalid creator: {creator}',logLevel=LOG_ERROR)
                continue
            # Get creator's info from DB
            if (not Connection.findAndCompareCreators(creatorsInDB=creatorsInDB, creator=creator)):
                    # Update creator in DB
                    Connection.updateCreator(creator=creator)

    def findAndCompareCreators(creatorsInDB: list, creator: dict) -> bool:
        for dbCreator in creatorsInDB:
            if (dbCreator.get('id') == creator.get('id')):
                res = Connection.compareCreatorInfo(creator=creator, dbCreator=dbCreator)
                if (res):
                    return True
                else:
                    return False
        return False

    def startPingTask() -> None:
        Connection.loopFlag = True
        Connection.__thread = Thread(target=Connection.dbPingTask)
        Connection.__thread.start()

    def pingStop() -> None:
        Connection.loopFlag = False
        if (not Connection.__thread):
            log(str='Ping thread is not active', logLevel=LOG_WARNING)
        Connection.__thread.join()
        Connection.__thread = None

    def dbPingTask() -> None:
        SLEEP_INTERVAL = 5
        fName = Connection.dbPingTask.__name__
        log(str=f'{fName}: thread started')
        # infinite loop
        while(Connection.loopFlag):
            # Make simple select to check if DB is active
            query = 'select id from users limit 1'
            res = Connection.executeQuery(query=query,params={},all=False)
            if (res is None):
                log(str=f'{fName}: Database is not active, reconnecting')
                if (not Connection.reconnect()):
                    log(str=f'{fName}: Cannot reconnect to database', logLevel=LOG_WARNING)
            sleep(SLEEP_INTERVAL)

        log(str=f'{fName}: thread stopped')

#=======================================
    # Temp Helper
    def dbTmpHelper():
        if (not Connection.isInitialized()):
            log("Connection is not initialized",LOG_ERROR)
            return
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'INSERT INTO gamess ("user",type,correct_answer,question,created,result,finished,complexity) VALUES (1,1,1,1,NOW(),True,NOW()) returning id'
            try:
                cur.execute(query)
                ret = cur.fetchall()
                for row in ret:
                    print(row)
                log(f'Query executed')
            except (Exception, psycopg2.DatabaseError) as error:
                log(f'Failed execute qyery: {error}',LOG_ERROR)
