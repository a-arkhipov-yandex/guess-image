from os import path
from os import getenv, environ
from dotenv import load_dotenv
import re
import csv


DEBUG = False
EXT = '.jpg'
BASE_URL = 'https://functions.yandexcloud.net/d4ei6a2doh55olhcagsm/'

CREATORS_FILE_CVS = 'creators.csv'
ENV_DBTOKEN ='DBTOKEN'
ENV_BOTTOKEN ='BOTTOKEN'

def getDBToken():
    load_dotenv()
    token = getenv(ENV_DBTOKEN)
    return token

def getBotToken():
    load_dotenv()
    token = getenv(ENV_BOTTOKEN)
    return token

def readCSV(fileName):
    data = []
    if (not path.exists(fileName)):
        return data
    with open(fileName, 'r') as file:
        reader = csv.reader(file)
        header = next(reader)
        for row in reader:
            dataItem = {}
            for i in range(0,len(header)):
                fieldName = header[i]
                dataItem[fieldName] = row[i]
            data.append(dataItem)
    return data

def readCreatorsCSV():
    creators = readCSV(CREATORS_FILE_CVS)
    resCreators = []
    # Check and transform
    for creator in creators:
        id = creator.get('id')
        if (not id):
            print('ERROR: no ID in CSV file: {creator}')
            continue
        name = creator.get('name')
        if (not name):
            print('ERROR: no Name in CSV file: {creator}')
            continue
        complexity = creator.get('complexity')
        if (not complexity):
            print('ERROR: no Complexity in CSV file: {creator}')
            continue

        newCreator = {}
        newCreator['id'] = int(id)
        newCreator['name'] = name
        newCreator['complexity'] = int(complexity)
        gender = None
        if (creator.get('gender')):
            gender = int(creator.get('gender'))
        newCreator['gender'] = gender
        birth = None
        if (creator.get('birth')):
            birth = int(creator.get('birth'))
        newCreator['birth'] = birth
        death = None
        if (creator.get('death')):
            death = int(creator.get('death'))
        newCreator['death'] = death
        country = None
        if (creator.get('country')):
            country = creator.get('country')
        newCreator['country'] = country

        resCreators.append(newCreator)
        
    return resCreators

def getBaseUrl():
    return BASE_URL

# Returns True if run from web
def isWeb():
    if (environ.get('WEB')):
        return True
    return False

def debug(str):
    if (DEBUG):
        print(str)

def checkUserNameFormat(user):
    ret = False
    res = re.match(r'^[a-zA-Z][a-zA-Z0-9-_]+$', user)
    if res and len(user) > 2:
        ret = True
    return ret

# Build image name from parts
def buildImgName(creator, title, year):
    url = ' '.join([creator,'-',title,'-',year]) + EXT
    return url

# remove 'ок ' and ' г' from year of image
# Returns:
#   None - something wrong with format (len <4 or no 'г.' at the end)
#   year - str withour ' г' and precending 'ok. '
def removeYearSigns(rawYear):
    if (len(rawYear) < 4):
        return None
    # Remove ' г' from year
    year_sign = rawYear[-2:]
    if (year_sign == ' г'):
        year = rawYear[:-2]
    else:
        return None

    if year[0:3] == 'ок ':
        year = year[3:]

    return year

# Transofrm str to int
# Returns:
#   int i - if correct it
#   False - if cannot transform
def myInt(str):
    try:
        iYear = int(str)
    except:
        return False
    return iYear

# Build URL to image
def buildImgUrl(base_url, creator, title, year):
    space = '%20'
    url1 = base_url + buildImgName(creator, title, year)

    url = url1.replace(' ', space)

    return url

# Get year (possible nearly)
# Returns:
#   int year - int year
#   False - error parsing year
#   0 - year is too small or too big
def getYear(rawYear):
    retYear = 0
    year = removeYearSigns(rawYear)
    if (year == None):
        return False
    if year[-1] == 'е':
        year = year[0:-1]
    lYear = len(year)
    if (lYear == 4):
        # Check that this is real year
        retYear = myInt(year)
        if not retYear:
            print(f'Error: problem with int conversion - {year}')
            return False
    elif (lYear == 9):
        years = year.split('-')
        if (len(years) != 2):
            print(f'Error: cannot split years - {year}')
            return False
        year1 = myInt(years[0])
        year2 = myInt(years[1])
        if ((not year1) or (not year2)):
            print(f'Error: problem with int conversion 2 - {year}')
            return False
        retYear = int((year2+year1)/2) # return average
    
    if ((retYear < 1000) or (retYear > 2030)):
        print(f'ERROR: Year is out of range: {rawYear}')
        retYear = 0
    return retYear 
