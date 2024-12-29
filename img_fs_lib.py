from os import listdir, system, rename
from guess_image_lib import *
from PIL import Image

IMAGE_DIR = "/Users/a-arkhipov/Yandex.Disk.localized/Images/Картины/"
LOCAL_EXT = ".jpg"

DEFAULT_SAVE_IMAGE_DIR = "/Users/a-arkhipov/Downloads/SavedBotImages/"

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

def getImageFullPath(creator, title, year) -> str:
    file = buildImgName(creator=creator, name=title, year=year)
    fullPath = buildImgPathName(imgName=file) + LOCAL_EXT
    return fullPath

# Get image orientation
def getImageOrientation(file):
    img = Image.open(file)
    wid, hgt = img.size
    if (wid > hgt):
        return 2
    return 1
 
 # Build image name from parts
def buildImgName(creator, name, year) -> str:
    yearTxt = ''
    if (str(year) != '0'):
        yearTxt = f' - {year}'
    imageName = f'{creator} - {name}{yearTxt}'
    return imageName

# Build image file name from parts
def buildImgLocalFileName(creator, name, year) -> str:
    imageName = buildImgName(creator=creator,name=name,year=year)
    url = f'{imageName}{LOCAL_EXT}'
    return url

# Adjust all files on disk
def adjustAllFilesOnDisk(creators, titles, years) -> None:
    c = 0
    for i in range(len(creators)):
        creator = creators[i]
        title = titles[i]
        year = years[i]
        filename_old = getImageFullPath(creator=creator, title=title, year=year)
        creator = adjustText(text=creator)
        title = adjustText(text=title)
        filename_new = getImageFullPath(creator=creator, title=title, year=year)
        if creator != creators[i] or title != titles[i]:
            c += 1
            print(f'Renaming: {filename_old} -> {filename_new}')
            rename(src=filename_old, dst=filename_new)
    print(f'Total files renamed: {c}')
