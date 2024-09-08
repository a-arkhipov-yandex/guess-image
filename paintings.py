from db_lib import *
from gibot_lib import ibotCheckAnswerGameType3
from guess_image_lib import *
from s3_lib import *
from img_fs_lib import *
from img_ui_lib import *
from game_lib import *
from Levenshtein import distance
from log_lib import *

#===============
# Main section
#---------------
def main():
    initLog(printToo=True)
    # Need to read dir and fill out paintings data
    imgData = getImgs()
    creators = imgData[0]
    titles = imgData[1]
    years = imgData[2]
    intYears = imgData[3]
    orientations = imgData[4]

    crNum = len(set(creators))
    log(f"Total number of creators: {crNum}",LOG_DEBUG)

    #checkUrls(creators, titles, years)

    #bulkUpload(creators, titles, years)

    #Connection.initConnection(test=False)
    if (not Connection.initConnection(test=True)):
        print('ERROR: Cannot init connection')
        exit()

    #Connection.clearAllCurrentGames()

    #Connection.updateCreatorsFromCSV()

    #Connection.updateDB(creators, titles, years, intYears, orientations)

    #print(ibotCheckAnswerGameType3('клод моне', 'клод моне'))

    #print(Connection.getCreatorIdByName('Винсент Ван Гог'))
    #html = showNImages(4)
    #print(html)
    #print(Connection.getImageIdByCreatorId(100000, 'Поля тюльпанов', '1883 г'))
    #Connection.insertGame(1,1,1,1)
    #print(Connection.getUserIdByName('Test_User'))
    
    #print(Connection.executeQuery('select id from creators where id = 2', {}, True))
    #query = 'select * from users'
    #query = 'select id,question from games where id = %(id)s'
    #print(Connection.executeQuery(query,{},True))
    #print(int(None))
    #print(Connection.getAllGamesList(1))
    #print('No game found' in '<div> dfsd No gadfme found.</div')
    #print(Connection.getRandomImageIdsOfCreator(2))
    #query = "SELECT created FROM games WHERE id =1"
    #print(Connection.executeQuery(query,{}))
    #print(Connection.getNCreators(5, 2))
    #print(Connection.insertGame(1,2,1,1))
    #print(guess_image.pageQuestion({'user':'1','game':306}))
    #conn = Connection.getConnection()
    #with conn.cursor() as cur:
    #    query = 'INSERT INTO games ("user",type,correct_answer,question,created ) VALUES ( %(u)s, %(t)s, %(ca)s, %(q)s, NOW()) returning id'
    #    cur.execute(query, {'u':1,'t':2,'ca':1,'q':1})
    #    row = cur.fetchone()
    #    print(row)
    #print(Connection.getGameInfoById(308))
    #Connection.deleteGame(gameId)

    #checkPagesToShow()

    #print(Connection.getCreatorInfoById(923))

    Connection.closeConnection()

if __name__ == "__main__":
    main()
