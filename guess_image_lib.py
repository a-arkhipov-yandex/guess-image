from os import path
from os import getenv, environ
from datetime import datetime as dt
from Levenshtein import distance
from dotenv import load_dotenv
import re
import csv
from log_lib import *

EXT = '.jpg'
BASE_URL = 'https://functions.yandexcloud.net/d4ei6a2doh55olhcagsm/'

CREATORS_FILE_CVS = 'creators.csv'
ENV_DBHOST = 'DBHOST'
ENV_DBPORT = 'DBPORT'
ENV_DBNAME = 'DBNAME'
ENV_DBUSER = 'DBUSER'
ENV_DBTOKEN ='DBTOKEN'
ENV_DBTESTHOST = 'DBTESTHOST'
ENV_DBTESTPORT = 'DBTESTPORT'
ENV_DBTESTNAME = 'DBTESTNAME'
ENV_DBTESTUSER = 'DBTESTUSER'
ENV_DBTESTTOKEN ='DBTESTTOKEN'

ENV_BOTTOKEN = 'BOTTOKEN'
ENV_BOTTOKENTEST = 'BOTTOKENTEST'

ENV_TESTDB = 'TESTDB'
ENV_TESTBOT = 'TESTBOT'

MIN_SIMILARITY = 3

def isStrSimilar(str1,str2):
    dist = getStrDistance(str1,str2)
    return dist <= MIN_SIMILARITY

def getStrDistance(str1, str2):
    return distance(str1, str2)

def isTestBot():
    load_dotenv()
    ret = True
    testbot = getenv(ENV_TESTBOT)
    if (testbot):
        if (testbot == "False"):
            ret = False
    return ret

def isTestDB():
    load_dotenv()
    ret = True
    testdb = getenv(ENV_TESTDB)
    if (testdb):
        if (testdb == "False"):
            ret = False
    return ret    

def getBotToken(test):
    load_dotenv()
    token = getenv(ENV_BOTTOKEN)
    if (test):
        token = getenv(ENV_BOTTOKENTEST)

    return token

def getDBbConnectionData():
    load_dotenv()
    data={}
    data['dbhost']=getenv(ENV_DBHOST)
    data['dbport']=getenv(ENV_DBPORT)
    data['dbname']=getenv(ENV_DBNAME)
    data['dbuser']=getenv(ENV_DBUSER)
    data['dbtoken']=getenv(ENV_DBTOKEN)
    for v in data.values():
        if (v == None): # Something wrong
            return None
    return data

def getDBbTestConnectionData():
    load_dotenv()
    data={}
    data['dbhost']=getenv(ENV_DBTESTHOST)
    data['dbport']=getenv(ENV_DBTESTPORT)
    data['dbname']=getenv(ENV_DBTESTNAME)
    data['dbuser']=getenv(ENV_DBTESTUSER)
    data['dbtoken']=getenv(ENV_DBTESTTOKEN)
    for v in data.values():
        if (v == None): # Something wrong
            return None
    return data

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
            log(f'No ID in CSV file: {creator}',LOG_ERROR)
            continue
        name = creator.get('name')
        if (not name):
            log(f'No Name in CSV file: {creator}',LOG_ERROR)
            continue
        complexity = creator.get('complexity')
        if (not complexity):
            log(f'No Complexity in CSV file: {creator}',LOG_ERROR)
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
            log(f'Problem with int conversion - {year}',LOG_ERROR)
            return False
    elif (lYear == 9):
        years = year.split('-')
        if (len(years) != 2):
            log(f'Cannot split years - {year}',LOG_ERROR)
            return False
        year1 = myInt(years[0])
        year2 = myInt(years[1])
        if ((not year1) or (not year2)):
            log(f'Problem with int conversion 2 - {year}',LOG_ERROR)
            return False
        retYear = int((year2+year1)/2) # return average
    
    if ((retYear < 1000) or (retYear > 2030)):
        log(f'Year is out of range: {rawYear}',LOG_ERROR)
        retYear = 0
    return retYear 
