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
    updateAll = True
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
        removeNonExistingFilesOnS3()
        bulkUpload(creators=creators, titles=titles, years=years)

    if (not Connection.initConnection(test=not prodDb)):
        print('ERROR: Cannot init connection')
        exit()

    # Put your adhoc code here!

    if ((updateDB or cleanupDB or updateCSV) and updateAll):

        if (updateDB):
            Connection.updateDB(creators=creators, titles=titles, years=years, intYears=intYears, orientations=orientations)
        if (cleanupDB):
            Connection.updateDB2(creators=creators, titles=titles, years=years, intYears=intYears, orientations=orientations)
        if (updateCSV):
            Connection.updateCreatorsFromCSV()

    Connection.closeConnection()

if __name__ == "__main__":
    main()
