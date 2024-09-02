import psycopg2
from guess_image_lib import *

CREATORS_IN_TYPE2_ANSWER = 5

#=======================
# Checks section
#-----------------------
def dbLibCheckCreator(creatorInfo):
    if (not creatorInfo.get('id')):
        return False
    if (not creatorInfo.get('name')):
        return False
    if (not creatorInfo.get('complexity')):
        return False

    return True

# Check answer (can be string or int with positive integer value)
def dbLibCheckAnswer(answer):
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
def dbLibCheckUserId(user_id):
    ret = False
    iId = 0
    try:
        iId = int(user_id)
    except:
        return False
    if (iId > 0):
        ret = True
    return ret

# Check user name (can be string with '[a-zA-Z][0-9a-zA-Z]')
def dbLibCheckUserName(user_name):
    return checkUserNameFormat(user_name)

# Check game id (can be string or int with positive integer value)
def dbLibCheckGameId(game_id):
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
def dbLibCheckGameType(game_type):
    ret = False
    iType = 0
    try:
        iType = int(game_type)
    except:
        return ret
    if (iType == 1 or iType == 2):
        ret = True
    return ret

# Check game type (can be string or int with value 1 or 2)
def dbLibCheckGameComplexity(game_type):
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
def dbLibCheckOrientation(orientation):
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
def dbLibCheckIfGameFinished(gameInfo):
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
def dbNotFound(result):
    if (result != None):
        if (result == Connection.NOT_FOUND): # empty array
            return True
    return False

# Check that item is found
# Returns:
#   True - item has been found
#   False - otherwise (not found or error)
def dbFound(result):
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
    BASE_URL_KEY = 'base_url'
    DEFAULT_GAMETYPE_KEY = 'default_gametype'
    DEFAULT_COMPLEXITY_KEY = 'default_complexity'
    NOT_FOUND = "!!!NOT_FOUND!!!"

    def initConnection(token=None, test=False):
        if (not Connection.__isInitialized):
            Connection.__connection = Connection.__newConnection(token, test)
            if (Connection.isInitialized()):
                # Cache section
                Connection.__baseImageUrl = Connection.getSettingValue(Connection.BASE_URL_KEY)
                Connection.__defaultGameType = int(Connection.getSettingValue(Connection.DEFAULT_GAMETYPE_KEY))
                Connection.__defaultComplexity = int(Connection.getSettingValue(Connection.DEFAULT_COMPLEXITY_KEY))
                Connection.__gameTypes = Connection.getGameTypesFromDb()
                Connection.__complexities = Connection.getComplexitiesFromDb()
                debug(f"DB Connection created")
            else:
                print(f'Error: Cannot initialize connection to DB')
        else:
                print(f'WARNING: Trying to initialize connection that already initialized')
    
    def getConnection():
        if (not Connection.isInitialized()):
            return None
        return Connection.__connection
    
    def closeConnection():
        if (Connection.__isInitialized):
            Connection.__connection.close()
            Connection.__isInitialized = False
            print(f"DB Connection closed")

    def __newConnection(token, test=False):
        conn = None
        try:
            if (not isWeb()): # Connection via internet
                if (test):
                    conn = psycopg2.connect("""
                        host=rc1b-fdrelru32ywy97o5.mdb.yandexcloud.net
                        port=6432
                        sslmode=verify-full
                        dbname=db1
                        user=user1
                        password=123qweasd
                        target_session_attrs=read-write
                    """)
                else: # Production
                    conn = psycopg2.connect("""
                        host=rc1b-qgx6lvjwro46n9kq.mdb.yandexcloud.net
                        port=6432
                        sslmode=verify-full
                        dbname=db1
                        user=user1
                        password=123qweasd
                        target_session_attrs=read-write
                    """)
            else: # Connection from inside cloud function
                if (test):
                    conn = psycopg2.connect(
                        database="akf7lhr9b3t46j4pm42d", # Идентификатор подключения
                        user="user1", # Пользователь БД
                        password=token,
                        host="akf7lhr9b3t46j4pm42d.postgresql-proxy.serverless.yandexcloud.net", # Точка входа
                        port=6432,
                        sslmode="require")
                else:
                    conn = psycopg2.connect(
                        database="akfskctj4iduo0t9h9dl", # Идентификатор подключения
                        user="user1", # Пользователь БД
                        password=token,
                        host="akfskctj4iduo0t9h9dl.postgresql-proxy.serverless.yandexcloud.net", # Точка входа
                        port=6432,
                        sslmode="require")
            conn.autocommit = True
            Connection.__isInitialized = True
            print(f'DB Connetion established')
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"ERROR: Cannot connect to database: {error}")
            conn = None
        
        return conn

    def isInitialized():
        return Connection.__isInitialized
    
    def getBaseImageUrl():
        return Connection.__baseImageUrl

    # Execute query with params
    # If 'all' == True - execute fetchAll()/ otherwise fetchOne()
    # Returns:
    #   None - issue with execution
    #   NOT_FOUND - if nothing found
    #   [result] - array with one found item
    def executeQuery(query, params={}, all=False):
        if (not Connection.isInitialized()):
            print(f'ERROR: Cannot execute query "{query}" with "{params}" (all={all}): connection is not initialized')
            return None
        ret = Connection.NOT_FOUND
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            try:
                cur.execute(query,params)
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
                print(f'ERROR: Failed execute query "{query}" with params "{params}" (all={all}): {error}')
                return None
        return ret

    # Get setting value. Returns key or None if not found or if connection is not initialized
    def getSettingValue(key):
        query = 'select value from settings where key=%(key)s'
        ret = Connection.executeQuery(query,{'key': key})
        if (dbFound(ret)):
            ret = ret[0]
        return ret

    # Update DB
    def updateDB(creators, titles, years, intYears, orientations):
        if (not Connection.isInitialized()):
            print("Error: cannot updateDB - connection is not initialized")
            return
        Connection.bulkCreatorInsert(creators)
        mCreators = getImageCreatorMap(creators, titles, years, intYears, orientations)
        Connection.bulkImageInsersion(mCreators)

    # Returns:
    #    creatorID by name
    #    None if not found or connection not initialized
    #    NOT_FOUND - not found creator
    def getCreatorIdByName(creator):
        query = "SELECT id FROM creators WHERE name =%(creator)s"
        ret = Connection.executeQuery(query,{'creator':creator})
        if (dbFound(ret)):
            ret = ret[0]
        return ret

    # Returns:
    #    creatorInfo by id {'id':N,...}
    #    None DB issue or connection not initialized
    #    NOT_FOUND - not found creator
    def getCreatorInfoById(creatorId):
        if (not creatorId):
            print('ERROR: getCreatorInfoById: creatorID is not passed')
            return Connection.NOT_FOUND
        query = "SELECT id,name,gender,country,birth,death,complexity FROM creators WHERE id =%(id)s"
        ret = Connection.executeQuery(query,{'id':creatorId})
        if (dbFound(ret)):
            creatorInfo = {}
            creatorInfo['id'] = int(ret[0])
            creatorInfo['name'] = ret[1]
            creatorInfo['gender'] = ret[2]
            if (ret[2]):
                creatorInfo['gender'] = int(ret[2])
            creatorInfo['country'] = ret[3]
            creatorInfo['birth'] = ret[4]
            if (ret[4]):
                creatorInfo['birth'] = int(ret[4])
            creatorInfo['death'] = ret[5]
            if (ret[5]):
                creatorInfo['death'] = int(ret[5])
            creatorInfo['complexity'] = ret[6]
            if (ret[6]):
                creatorInfo['complexity'] = int(ret[6])
            ret = creatorInfo
        return ret

    # Returns:
    #    creatorName by id
    #    None DB issue or connection not initialized
    #    NOT_FOUND - not found creator
    def getCreatorNameById(creatorId):
        query = "SELECT name FROM creators WHERE id =%(id)s"
        ret = Connection.executeQuery(query,{'id':creatorId})
        if (dbFound(ret)):
            ret = ret[0]
        return ret

    # Returns 'n' creatorIDs or None if connection not initialized or issue with DB
    def getRandomCreatorIds(complexity, n = 1):
        query = "SELECT id FROM creators WHERE complexity<=%(c)s ORDER BY RANDOM() LIMIT %(n)s"
        ret = Connection.executeQuery(query,{'c':complexity, 'n':n},True)
        if (dbFound(ret)):
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
        ret = Connection.executeQuery(query,{'creator':creatorId, 'n':n},True)
        if (dbFound(ret)):
            if (n == 1):
                ret = ret[0]
            else:
                ids = []
                for i in ret:
                    ids.append(i)
                ret = ids
        return ret

    # Returns 'n' imageIds or None if connection not initialized or issue with DB
    def getRandomImageIdsOfOtherCreators(creatorId, complexity, n = 1):
        #query = "SELECT id FROM images where creator!=%(creator)s ORDER BY RANDOM() LIMIT %(n)s"
        query = "SELECT i.id FROM images as i join creators as c on i.creator=c.id where creator!=%(c)s and complexity<=%(com)s ORDER BY RANDOM() LIMIT %(n)s"
        ret = Connection.executeQuery(query,{'c':creatorId, 'com':complexity, 'n':n},True)
        if (dbFound(ret)):
            if (n == 1):
                ret = ret[0]
            else:
                ids = []
                for i in ret:
                    ids.append(i)
                ret = ids
        return ret

    # Returns 'n' imageIds or None if connection not initialized or issue with DB
    def getRandomImageIdsOfAnyCreator(complexity, n = 1):
        #query = "SELECT id FROM images ORDER BY RANDOM() LIMIT %(n)s"
        query = "SELECT i.id FROM images as i join creators c on i.creator = c.id where complexity<=%(c)s ORDER BY RANDOM() LIMIT %(n)s"
        ret = Connection.executeQuery(query, {'c':complexity, 'n':n})  
        if (dbFound(ret)):
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
        ret = Connection.executeQuery(query,{'cId':creatorId,'image':image,'year':year})
        if (dbFound(ret)):
            ret = ret[0]
        return ret

    # Get image id with creator name
    # Returns:
    #   None - connection not initialized or issue during query
    #   [id] - id of found image
    #   NOT_FOUND - image not found
    def getImageIdByCreatorName(creator, image, year):
        query = f"select i.id from images as i join creators as c on i.creator = c.id where c.name=%(cr)s AND i.name =%(image)s AND i.year_str = %(y)s"
        ret = Connection.executeQuery(query,{'cr':creator,'image':image,'y':year})
        if (dbFound(ret)):
            ret = ret[0]
        return ret

    # Get user by name
    # Return:
    #   None - something wrong with connection/query
    #   id - user id
    #   NOT_FOUND - no such user
    def getUserIdByName(name):
        ret = dbLibCheckUserName(name)
        if (not ret):
            return Connection.NOT_FOUND
        query = f"SELECT id FROM users WHERE name = %(name)s"
        ret = Connection.executeQuery(query,{'name':name})
        if (dbFound(ret)):
            ret = ret[0]
        return ret

    # Delete user - returns True/False
    def deleteUser(id):
        ret = False
        if (not Connection.isInitialized()):
            print("Error: cannot delete user - connection is not initialized")
            return ret
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = "DELETE from users where id = %(user)s"
            try:
                cur.execute(query, {'user':id})
                print(f'Deleted user: {id}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                print(f'ERROR: Failed delete user {id}: {error}')
        return ret
    
    # Insert new user in DB. Returns True is success or False otherwise
    def insertUser(userName, gameType=None, complexity=None):
        if (not Connection.isInitialized()):
            print("Error: cannot insert user - connection is not initialized")
            return False
        ret = dbLibCheckUserName(userName)
        if (not ret):
            print("Error: cannot insert user -  invalid name format")
            return False
        if ((complexity == None) or (not dbLibCheckGameComplexity(complexity))):
            complexity = Connection.getDefaultComplexity()

        if ((gameType == None) or (not dbLibCheckGameType(gameType))):
            gameType = Connection.getDefaultGameType()

        ret = False
        conn = Connection.getConnection()
        # Check for duplicates
        retUser = Connection.getUserIdByName(userName)
        if (retUser == None): # error with DB
            print(f'Error: cannot get user from DB: {userName}')
            return False
        if (dbNotFound(retUser)):
            with conn.cursor() as cur:
                query = "INSERT INTO users ( name,game_type,game_complexity ) VALUES ( %(u)s,%(t)s,%(c)s )"
                try:
                    cur.execute(query, {'u':userName,'t':gameType,'c':complexity})
                    print(f'Inserted user: {userName} - {gameType} - {complexity}')
                    ret = True
                except (Exception, psycopg2.DatabaseError) as error:
                    print(f'ERROR: Failed insert user {userName}: {error}')
        else:
            debug(f'Trying to insert duplicate user: {userName}')
            ret = True # Return true for now - probably wrong
        return ret

    # Delete creator - returns nothing
    def deleteCreator(id):
        if (not Connection.isInitialized()):
            print("Error: cannot delete creator - connection is not initialized")
            return
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = "DELETE from creators where id = %(id)s"
            try:
                cur.execute(query, {'id':id})
                print(f'Deleted creator: {id}')
            except (Exception, psycopg2.DatabaseError) as error:
                print(f'ERROR: Failed delete creator {id}: {error}')

    # Insert new creator. Returns True is success or False otherwise
    def insertCreator(creator):
        if (not Connection.isInitialized()):
            print("Error: cannot insert creator - connection is not initialized")
            return False
        ret = False
        # Check for duplicates
        retCreator = Connection.getCreatorIdByName(creator)
        if (retCreator == None): # error with DB
            print('Error: cannot get creator from DB')
            return False
        if (dbNotFound(retCreator)):
            conn = Connection.getConnection()
            with conn.cursor() as cur:
                query = "INSERT INTO creators ( name, complexity ) VALUES ( %(cr)s , 5 )" # Put complexity 5 to decide later
                try:
                    cur.execute(query, {'cr':creator})
                    print(f'Inserted creator: {creator}')
                    ret = True
                except (Exception, psycopg2.DatabaseError) as error:
                    print(f'ERROR: Failed insert creator {creator}: {error}')
                    ret = False
        else:
            debug(f'Trying to insert duplicate creator: {creator}')
            ret = True # Probably wrong here
        return ret

    # Bulk creators insertion
    def bulkCreatorInsert(creators):
        creatorsSet = set(creators)
        for creator in creatorsSet:
            Connection.insertCreator(creator)

    # Delete image - returns nothing
    def deleteImage(id):
        if (not Connection.isInitialized()):
            print("Error: cannot delete image - connection is not initialized")
            return
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = "DELETE from images where id = %(id)s"
            try:
                cur.execute(query, {'id':id})
                print(f'Deleted image: {id}')
            except (Exception, psycopg2.DatabaseError) as error:
                print(f'ERROR: Failed delete image {id}: {error}')

    # Insert image in DB. Returns True is success or False otherwise
    def insertImage(creatorId, image, year, intYear, orientation):
        if (not Connection.isInitialized()):
            print("Error: cannot insert image - connection is not initialized")
            return False
        # Check for duplicates
        ret = False
        id = Connection.getImageIdByCreatorId(creatorId, image, year)
        if (id == None):
            print(f'Error: cannot insert image {creatorId} - {image} - {year}: DB issue')
            return None
        if (dbNotFound(id)):
            conn = Connection.getConnection()
            with conn.cursor() as cur:
                query = f"INSERT INTO images (creator, name, year_str, year, orientation) VALUES (%(crId)s,%(im)s,%(y)s,%(iY)s,%(o)s)"
                try:
                    cur.execute(query, {'crId':creatorId, 'im':image,'y':year,'iY':intYear,'o':orientation})
                    print(f'Inserted image: {creatorId} - {image} - {year}')
                    ret = True
                except (Exception, psycopg2.DatabaseError) as error:
                    print(f'ERROR: Failed insert image {creatorId} - {image} - {year}: {error}')
        else:
            debug(f'Trying to insert duplicate image: {creatorId} - {image} - {year}')
            ret = True # probably wrong here
        return ret

    # Bulk image insertion
    def bulkImageInsersion(mCreators):
        if (not Connection.isInitialized()):
            print("Error: cannot bulk image insert - connection is not initialized")
            return
        # Pass through all the creators
        for creator in mCreators:
            # Check that creator is in DB
            creatorId = Connection.getCreatorIdByName(creator)
            if (creatorId == None):
                print(f'ERROR: Error getting creator from DB: {creator}')
                continue
            if (dbNotFound(creatorId)):
                print(f'ERROR: No creator in DB: {creator}')
                continue

            images = mCreators[creator]
            
            # Pass through all the images of the creator
            for imageData in images:
                image = getImageFromData(imageData)
                year = getYearFromData(imageData)
                intYear = getIntYearFromData(imageData)
                orientation = getOrientationFromData(imageData)

                # Insert tiles, year, intYear
                Connection.insertImage(creatorId, image, year, intYear, orientation)

    # Get URL by image id
    # Returns:
    #   URL - if success
    #   NOT_FOUND - if image not found
    #   None - if failed connection or no such image
    def getImageUrlById(id):
        if (not Connection.isInitialized()):
            print("Error: cannot get image url by id - connection is not initialized")
            return None
        image = Connection.getImageInfoById(id)
        if (image == None):
            print(f'ERROR: cannot get image URL for image {id}: DB issue')
            return None
        elif (dbNotFound(image)):
            print(f'ERROR: cannot get image URL for image {id}: no such image in DB')
            return Connection.NOT_FOUND
        baseUrl = Connection.getBaseImageUrl()
        url = None
        if (baseUrl):
            cName = image['creatorName']
            iName = image['imageName']
            yearStr = image['yearStr']
            url = buildImgUrl(baseUrl, cName, iName, yearStr)
        return url

    # Get image info from DB by id
    # Returns:
    #   [{creatorId, creatorName, imageName, year, year_str, orientation}]
    #   NOT_FOUND - if no such image
    #   None - if issue with connection
    def getImageInfoById(id):
        query = f"select i.creator,c.name,i.name,i.year,i.year_str,i.orientation from images as i join creators as c on i.creator = c.id where i.id = %(id)s"
        ret = Connection.executeQuery(query,{'id':id})
        if (dbFound(ret)):
            imageInfo = {}
            imageInfo['creatorId'] = int(ret[0])
            imageInfo['creatorName'] = ret[1]
            imageInfo['imageName'] = ret[2]
            imageInfo['intYear'] = int(ret[3])
            imageInfo['yearStr'] = ret[4]
            imageInfo['orientation'] = int(ret[5])
            ret = imageInfo
        return ret

    # Update image orientation. Returns nothing
    def updateImageOrientation(creator, image, year, orientation):
        if (not Connection.isInitialized()):
            print("Error: cannot update image orientation - connection is not initialized")
            return
        id = Connection.getImageIdByCreatorName(creator, image, year)
        if (id == None):
            print(f'Error: cannot update image {creator} - {image} - {year} orientation: DB issue')
            return
        if (dbFound(id)):
            conn = Connection.getConnection()
            with conn.cursor() as cur:
                query = 'update images set orientation=%(o)s where id = %(id)s'
                try:
                    cur.execute(query,{'o':orientation,'id':id[0]})
                    print(f'Updated orienttion: {creator} - {image} - {year}: orientation {orientation}')
                except (Exception, psycopg2.DatabaseError) as error:
                    print(f'ERROR: Failed update orienttion {creator} - {image} - {year}: {error}')
        else:
            print(f"ERROR: Cannot set orientation for (image not found): {creator} - {image} - {year}")

    # Delete game - returns true/false
    def deleteGame(id):
        ret = False
        if (not Connection.isInitialized()):
            print("Error: cannot delete game - connection is not initialized")
            return ret
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = "DELETE from games where id = %(id)s"
            try:
                cur.execute(query, {'id':id})
                print(f'Deleted game: {id}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                print(f'ERROR: Failed delete game {id}: {error}')
        return ret

    # Clear all current games on all users
    def clearAllCurrentGames():
        ret = False
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'update users set current_game=%(n)s'
            try:
                cur.execute(query,{'n':None})
                ret = cur.fetchone()
                print(f'All current games cleared: {ret}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                print(f'ERROR: Failed clearing current games:: {error}')
        return ret


    # Insert new user in DB
    # Returns:
    #   id - id of new game
    #   None - otherwise
    def insertGame(user_id, game_type, correct_answer, question, complexity):
        # Checks first
        if (not dbLibCheckUserId(user_id)):
            return None
        if (not dbLibCheckGameType(game_type)):
            return None
        if (not dbLibCheckGameComplexity(complexity)):
            return None

        if (not Connection.isInitialized()):
            print(f"Error: cannot insert game for user {user_id}- connection is not initialized")
            return None
        ret = None
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'INSERT INTO games ("user","type",correct_answer,question,created,complexity) VALUES ( %(u)s, %(t)s, %(ca)s, %(q)s, NOW(), %(com)s) returning id'
            try:
                cur.execute(query, {'u':user_id,'t':game_type,'ca':correct_answer,'q':question,'com':complexity})
                row = cur.fetchone()
                if (row):
                    ret = row[0]
                    print(f'Inserted game: {ret}')
                else:
                    print(f'ERROR: Cannot get id of new game')
            except (Exception, psycopg2.DatabaseError) as error:
                print(f'ERROR: Failed insert game for user {user_id}: {error}')
        return ret

    # Get game by id
    # Returns:
    #   None - issue with DB
    #   NOT_FOUND - no such game
    #   {gameInfo} - game info
    def getGameInfoById(id):
        query = 'select id, "user","type",correct_answer,question,user_answer,result,created,finished,complexity from games where id = %(id)s'
        ret = Connection.executeQuery(query,{'id':id})
        if (dbFound(ret)):
            gameInfo = dbGetGameInfo(ret)
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
    def getNCreators(n, exclude, complexity):
        query = "SELECT id,name FROM creators where id != %(e)s and complexity <= %(c)s ORDER BY RANDOM() LIMIT %(n)s"
        ret = Connection.executeQuery(query,{'e':exclude, 'c':complexity,'n':n},True)
        if (dbFound(ret)):
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
    def finishGame(gameId, answer):
        if (not Connection.isInitialized()):
            print("ERROR: cannot finish game - connection is not initialized")
            return False
        gameInfo = Connection.getGameInfoById(gameId)
        if (gameInfo == None):
            print(f'ERROR: finishGame: cannot get game {gameId}: DB issue')
            return False
        ret = False
        if (dbFound(gameInfo)):
            # Check that game is not finished yet
            isFinished = dbLibCheckIfGameFinished(gameInfo)
            if (isFinished):
                print(f'ERROR: finishGame: Game {gameId} is already finished')
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
                    cur.execute(query,{'r':dbResult,'id':gameId, 'a':answer})
                    print(f'finishGame: Updated game: {gameId} - {dbResult}')
                    ret = True
                except (Exception, psycopg2.DatabaseError) as error:
                    print(f'ERROR: finishGame: Failed finish game {gameId}: {error}')
        else:
            print(f"ERROR: finishGame: Cannot find game {gameId}: image not found")
        return ret

    # Check is game is finished. Returns True/False
    def checkGameIsFinished(gameId):
        gameInfo = Connection.getGameInfoById(gameId)
        if (dbFound(gameInfo)):
            return (dbLibCheckIfGameFinished(gameInfo))
        return False

    # Get game types from DB
    # Returns:
    #   [[game_type_id, name, question]]
    #   NOT_FOUND - no game_types in DB
    #   None - issue with connection
    def getGameTypesFromDb():
        query = 'select id,name,question from game_types'
        ret = Connection.executeQuery(query,{},True)
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
        ret = Connection.executeQuery(query,{},True)
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
        ret = dbLibCheckUserId(userId)
        if (not ret):
            return None
        query = 'select id,"user","type",correct_answer,question,user_answer,result,created,finished,complexity from games where "user"=%(uId)s'
        ret = Connection.executeQuery(query,{'uId':userId},True)
        if (dbFound(ret)):
            games = []
            for gi in ret:
                gameInfo = dbGetGameInfo(gi)
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
        ret = dbLibCheckUserId(userId)
        if (not ret):
            return None
        query = 'select id,"user","type",correct_answer,question,user_answer,result,created,finished,complexity from games where "user"=%(uId)s and result is NULL'
        ret = Connection.executeQuery(query,{'uId':userId}, True)
        if (dbFound(ret)):
            games = []
            for gi in ret:
                gameInfo = dbGetGameInfo(gi)
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
        ret = Connection.executeQuery(query,{'uId':userId},True)
        if (dbFound(ret)):
            games = []
            for gi in ret:
                gameInfo = dbGetGameInfo(gi)
                games.append(gameInfo)
            ret = games
        else:
            ret = []
        return ret

    # Update creator - returns True/False
    def updateCreator(creator):
        ret = False
        if (not dbLibCheckCreator(creator)):
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
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'update creators set name=%(n)s,gender=%(g)s,birth=%(b)s,death=%(d)s,country=%(c)s,complexity=%(com)s where id = %(id)s'
            try:
                cur.execute(query,{'id':cId,'g':gender,'b':birth,'d':death,'n':name,'c':country,'com':complexity})
                print(f'updateCreator: Updated creator: {cId} - {creator}')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                print(f'ERROR: updateCreator: Failed update creator {cId}: {error}')
        return ret

    # Compare 2 creators info
    # Returns: True if everything is equal / False - if any differences
    def compareCreatorInfo(creator, dbCreator):
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
        ret = dbLibCheckUserName(userName)
        if (not ret):
            print(f'ERROR: getCurrentGame: Incorrect user {userName} provided')
            return None
        userId = Connection.getUserIdByName(userName)
        if (dbNotFound(userId)):
            print(f'ERROR: getCurrentGame: Cannot find user {userName}')
            return None
        ret = None
        query = 'select current_game from users where id=%(uId)s'
        currentGame = Connection.executeQuery(query, {'uId':userId})
        if (dbFound(currentGame)):
            currentGame = currentGame[0]
            if (currentGame):
                # Check that game is not finished
                ret2 = Connection.checkGameIsFinished(ret)
                if (not ret2): # UnFinished game
                    ret = currentGame
        return ret

    def setCurrentGame(userName, gameId):
        return Connection.updateCurrentGame(userName, gameId)

    def clearCurrentGame(userName):
        return Connection.updateCurrentGame(userName, None)


    # Update current_game for the userId
    # Returns: True - update successful / False - otherwise
    def updateCurrentGame(userName, gameId):
        if (not Connection.isInitialized()):
            print("ERROR: updateCurrentGame: connection is not initialized")
            return False
        ret = dbLibCheckUserName(userName)
        if (not ret):
            print(f'ERROR: updateCurrentGame: Incorrect user {userName} provided')
            return False
        userId = Connection.getUserIdByName(userName)
        if (dbNotFound(userId)):
            print(f'ERROR: updateCurrentGame: Cannot find user {userName}')
            return False
        if (gameId):
            gameInfo = Connection.getGameInfoById(gameId)
            if (dbNotFound(gameInfo)):
                print(f'ERROR: updateCurrentGame: cannot find game {gameId} (user={userName})')
                return False
            # Check userId is correct
            if (gameInfo['user'] != userId):
                print(f'ERROR: updateCurrentGame: game {gameId} doesnt belong to user {userName} ({userId})')
                return False
            # Check that game is finished
            ret = dbLibCheckIfGameFinished(gameInfo)
            if (ret):
                print(f'ERROR: updateCurrentGame: cannot set finished game as current (gameId = {gameId}, user={userName})')
                return False
        ret = False
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'update users set current_game=%(gId)s where id = %(uId)s'
            try:
                cur.execute(query,{'gId':gameId,'uId':userId})
                print(f'Updated current game: (gameId = {gameId}, user={userName})')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                print(f'ERROR: Failed update current game (gameId = {gameId}, user={userName}): {error}')
        return ret

    # Get user game type
    # Returns:
    #   game_type - game type
    #   None - if error
    def getUserGameType(userName):
        ret = None
        if (not Connection.isInitialized()):
            print("ERROR: getUserGameType: connection is not initialized")
            return ret
        ret2 = dbLibCheckUserName(userName)
        if (not ret2):
            print(f'ERROR: getUserGameType: Incorrect user {userName} provided')
            return ret
        userId = Connection.getUserIdByName(userName)
        if (dbNotFound(userId)):
            print(f'ERROR: getUserGameType: Cannot find user {userName}')
            return ret
        query = f'select game_type from users where id=%(uId)s'
        ret2 = Connection.executeQuery(query,{'uId':userId})
        if (dbFound(ret2)):
            ret = ret2[0]
        return ret

    # Update game type for the userId
    # Returns: True - update successful / False - otherwise
    def updateUserGameType(userName, gameType):
        if (not Connection.isInitialized()):
            print("ERROR: updateUserGameType: connection is not initialized")
            return False
        ret = dbLibCheckUserName(userName)
        if (not ret):
            print(f'ERROR: updateUserGameType: Incorrect user {userName} provided')
            return False
        userId = Connection.getUserIdByName(userName)
        if (dbNotFound(userId)):
            print(f'ERROR: updateUserGameType: Cannot find user {userName}')
            return False
        if (not dbLibCheckGameType(gameType)):
            print(f'ERROR: updateUserGameType: Wrong game type format: {gameType}')
            return False

        ret = False
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'update users set game_type=%(gt)s where id = %(uId)s'
            try:
                cur.execute(query,{'gt':gameType,'uId':userId})
                print(f'Updated game type: (gameType = {gameType}, user={userName})')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                print(f'ERROR: updateUserGameType: Failed update game type (gameType = {gameType}, user={userName}): {error}')
        return ret

   # Get user complexity
    # Returns:
    #   complexity - complexity
    #   None - if error
    def getUserComplexity(userName):
        ret = None
        if (not Connection.isInitialized()):
            print("ERROR: getUserComplexity: connection is not initialized")
            return ret
        ret2 = dbLibCheckUserName(userName)
        if (not ret2):
            print(f'ERROR: getUserComplexity: Incorrect user {userName} provided')
            return ret
        userId = Connection.getUserIdByName(userName)
        if (dbNotFound(userId)):
            print(f'ERROR: getUserComplexity: Cannot find user {userName}')
            return ret
        query = f'select game_complexity from users where id=%(uId)s'
        ret2 = Connection.executeQuery(query,{'uId':userId})
        if (dbFound(ret2)):
            ret = ret2[0]
        return ret

    # Update users complexity for the userId
    # Returns: True - update successful / False - otherwise
    def updateUserComplexity(userName, complexity):
        if (not Connection.isInitialized()):
            print("ERROR: updateUserComplexity: connection is not initialized")
            return False
        ret = dbLibCheckUserName(userName)
        if (not ret):
            print(f'ERROR: updateUserComplexity: Incorrect user {userName} provided')
            return False
        userId = Connection.getUserIdByName(userName)
        if (dbNotFound(userId)):
            print(f'ERROR: updateUserComplexity: Cannot find user {userName}')
            return False
        if (not dbLibCheckGameComplexity(complexity)):
            print(f'ERROR: updateUserComplexity: Wrong complexity format: {complexity}')
            return False

        ret = False
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'update users set game_complexity=%(c)s where id = %(uId)s'
            try:
                cur.execute(query,{'c':complexity,'uId':userId})
                print(f'Updated game type: (gameType = {complexity}, user={userName})')
                ret = True
            except (Exception, psycopg2.DatabaseError) as error:
                print(f'ERROR: updateUserComplexity: Failed update complexity (complexity = {complexity}, user={userName}): {error}')
        return ret

    # Update creators info from CSV file
    def updateCreatorsFromCSV():
        creators = readCreatorsCSV()
        if (not creators):
            print('No creators for update')
            return
        
        for creator in creators:
            if (not dbLibCheckCreator(creator)):
                print(f'ERROR: updateCreatorsFromCSV: Invalid creator: {creator}')
                continue
            # Get creator's info from DB
            dbCreator = Connection.getCreatorInfoById(creator.get('id'))
            if dbFound(dbCreator):
                # Check if there is new info in CSV
                if (not Connection.compareCreatorInfo(creator, dbCreator)):
                    # Update creator in DB
                    Connection.updateCreator(creator)
                else:
                    # Do nothing
                    pass


#=======================================
    # Temp Helper
    def dbTmpHelper():
        if (not Connection.isInitialized()):
            print("Error: connection is not initialized")
            return
        conn = Connection.getConnection()
        with conn.cursor() as cur:
            query = 'INSERT INTO gamess ("user",type,correct_answer,question,created,result,finished,complexity) VALUES (1,1,1,1,NOW(),True,NOW()) returning id'
            try:
                cur.execute(query)
                ret = cur.fetchall()
                for row in ret:
                    print(row)
                print(f'Query executed')
            except (Exception, psycopg2.DatabaseError) as error:
                print(f'ERROR: Failed execute qyery: {error}')
