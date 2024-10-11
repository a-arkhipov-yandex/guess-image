from os import listdir, system
from guess_image_lib import *
from PIL import Image

IMAGE_DIR = "/Users/a-arkhipov/Yandex.Disk.localized/Images/Картины/"

# Build image full path name
def buildImgPathName(imgName):
    return IMAGE_DIR + imgName

# Get all images in directory
def getImgs():
    files = []
    for f in listdir(path=IMAGE_DIR):
        # Remove '.jpg'
        f1 = f[:-4]
        # Skip '.DS_S'
        if f1 != '.DS_S':
            files.append(f1)

    numFiles = len(files)
    log(str=f'Number of files: {numFiles}')

    creators = []
    titles = []
    years = []
    intYears = []
    orientation = []
    for f in files:
        tmp = f.split(" - ")
        if len(tmp) != 3:
            log(str=f"ERROR: Wrong numer of items: {tmp}", logLevel=LOG_ERROR)
            continue
        creator = tmp[0].strip()
        if creator != tmp[0]:
            log(str=f'Spaces in creator: {tmp}', logLevel=LOG_ERROR)
            continue
        title = tmp[1].strip()
        if title != tmp[1]:
            log(str=f'Spaces in title: {tmp}', logLevel=LOG_ERROR)
            continue
        year = tmp[2].strip()
        if year != tmp[2]:
            log(str=f'Spaces in year: {tmp}', logLevel=LOG_ERROR)
            continue
        intYear = getYear(rawYear=year)
        if (not intYear):
            log(str=f'Cannet get int year: "{tmp}"', logLevel=LOG_ERROR)
            continue

        creators.append(creator)
        titles.append(title)
        years.append(year)
        intYears.append(intYear)

        fullPath = getImageFullPath(creator=creator, title=title, year=year)
        orient = getImageOrientation(file=fullPath)
        orientation.append(orient)

    return [creators, titles, years, intYears, orientation]

def getImageFullPath(creator, title, year):
    file = buildImgName(creator, title, year)
    fullPath = buildImgPathName(file)
    return fullPath

# Get image orientation
def getImageOrientation(file):
    img = Image.open(file)
    wid, hgt = img.size
    if (wid > hgt):
        return 2
    return 1
 