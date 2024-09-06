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
    for f in listdir(IMAGE_DIR):
        # Remove '.jpg'
        f1 = f[:-4]
        # Skip '.DS_S'
        if f1 != '.DS_S':
            files.append(f1)

    numFiles = len(files)
    log(f'Number of files: {numFiles}')

    creators = []
    titles = []
    years = []
    intYears = []
    orientation = []
    for f in files:
        tmp = f.split(" - ")
        if len(tmp) != 3:
            print(f"ERROR: Wrong numer of items: {tmp}")
            continue
        #print(tmp)
        creator = tmp[0].strip()
        if creator != tmp[0]:
            print(f'WARNING: Spaces in creator {tmp}')
        creators.append(creator)
        title = tmp[1].strip()
        if title != tmp[1]:
            print(f'WARNING: Spaces in title {tmp}')        
        titles.append(title)
        year = tmp[2].strip()
        if year != tmp[2]:
            print(f'WARNING: Spaces in year {tmp}')
        years.append(year)

        intYear = getYear(year)
        if (not intYear):
            print(f'ERROR: Cannet get int year: "{tmp}"')
        intYears.append(intYear)

        fullPath = getImageFullPath(creator, title, year)
        orient = getImageOrientation(fullPath)
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
 