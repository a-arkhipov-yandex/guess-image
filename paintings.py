import time
from db_lib import *
from guess_image_lib import *
from s3_lib import *
from img_fs_lib import *
from img_ui_lib import *
from game_lib import *
from log_lib import *

#===============
# Main section
#---------------
def main() -> None:
    updateAll = False
    updateS3 = True
    updateDB = True
    cleanupDB = True
    updateCSV = True

    prodDb = True
    initLog(printToo=True)
    # Need to read dir and fill out paintings data
    imgData = getImgs()
    creators = imgData[0]
    titles = imgData[1]
    years = imgData[2]
    intYears = imgData[3]
    orientations = imgData[4]

    crNum = len(set(creators))
    log(str=f"Total number of creators: {crNum}",logLevel=LOG_DEBUG)

    #checkUrls(creators, titles, years)
    if (updateS3 and updateAll):
        t = time.time()
        log(str='Removing Non Existing Files On S3')
        removeNonExistingFilesOnS3()
        tDiff = int(time.time() - t)
        log(str=f"removeNonExistingFilesOnS3: {tDiff} seconds")
        t = time.time()
        log(str='Uploading Images to S3')
        bulkUpload(creators=creators, titles=titles, years=years)
        tDiff = int(time.time() - t)
        log(str=f"bulkUpload: {tDiff} seconds")

    if (not Connection.initConnection(test=not prodDb)):
        print('ERROR: Cannot init connection')
        exit()

    # Put your adhoc code here!
    yearRange = guess_image.getImageCreationRange(intYear=1888)
    for j in range(1000):
        images = Connection.getRandomImageIdsOfOtherCreators(creatorId=2, complexity=3, n=3, range=yearRange)
        #print(images)
        flag = False
        for i in images:
            imageInfo = Connection.getImageInfoById(id=i[0])
            creatorId = imageInfo['creatorId']
            if (creatorId == 2):
                flag = True
                break
        if (flag):
            print(f'Found: {images}')
            break
    

    if ((updateDB or cleanupDB or updateCSV) and updateAll):

        if (updateDB):
            log(str='Updating DB 1')
            t = time.time()
            Connection.updateDB(creators=creators, titles=titles, years=years, intYears=intYears, orientations=orientations)
            tDiff = int(time.time() - t)
            log(str=f"updateDB: {tDiff} seconds")
        if (cleanupDB):
            log(str='Updating DB 2')
            t = time.time()
            Connection.updateDB2(creators=creators, titles=titles, years=years, intYears=intYears, orientations=orientations)
            tDiff = int(time.time() - t)
            log(str=f"updateDB2: {tDiff} seconds")
        if (updateCSV):
            log(str='Updating DB from CSV')
            t = time.time()
            Connection.updateCreatorsFromCSV()
            tDiff = int(time.time() - t)
            log(str=f"updateCreatorsFromCSV: {tDiff} seconds")

    Connection.closeConnection()

if __name__ == "__main__":
    main()
