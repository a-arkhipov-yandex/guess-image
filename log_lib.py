
from os import path
from os import getenv, environ
from dotenv import load_dotenv
import shutil
from datetime import datetime as dt

ENV_LOGFILE = 'LOGFILE'
ENV_LOGLEVEL = 'LOGLEVEL'

DEFAULT_LOGFILE = '/tmp/guess-image.log'

LOG_ERROR = 'ERROR'
LOG_INFO = 'INFO'
LOG_WARNING = 'WARNING'
LOG_DEBUG = 'DEBUG'

LOG_LEVELS = {
    LOG_ERROR: 3,
    LOG_WARNING: 4,
    LOG_INFO: 5,
    LOG_DEBUG: 7
}

class GuessImageLog:
    logCurrentLevel = LOG_INFO
    logFileName = ''
    logHandle = None
    printToo = False

    def logFileRotation(logFile):
        # Check if log file exist
        if (path.isfile(logFile)):
            # Copy existing file and add '.bak' at the end
            shutil.copyfile(logFile, logFile + '.bak')

def initLog(logFile=None, printToo=False):
    load_dotenv()
    if (not logFile):
        # Read logFile from env
        logFile = getenv(ENV_LOGFILE)
        if (not logFile):
            logFile = DEFAULT_LOGFILE
    GuessImageLog.logFileName = logFile
    # Read log level from ENV
    logLevel = getenv(ENV_LOGLEVEL)
    if (logLevel):
        # Check that this level exist
        ret = LOG_LEVELS.get(logLevel)
        if (ret): # ENV log level exists
            GuessImageLog.logCurrentLevel = logLevel
    GuessImageLog.logFileRotation(logFile)
    # Open log file for writing
    try:
        f = open(logFile, 'w')
        GuessImageLog.logHandle = f
    except Exception as error:
        log(f'Cannot open "{logFile}": {error}', LOG_ERROR)
    if (printToo == True):
        GuessImageLog.printToo = printToo
    log(f'Log initialization complete: log file={GuessImageLog.logFileName} | log level={GuessImageLog.logCurrentLevel}')

def log(str, logLevel=LOG_INFO):
    # Check log level first
    if (LOG_LEVELS[logLevel] > LOG_LEVELS[GuessImageLog.logCurrentLevel]):
        return # Do not print
    if (not GuessImageLog.logHandle):
        print(str)
    else:
        # Get date and time
        time = dt.now().strftime("%d-%m-%Y %H:%M:%S")
        logStr = f'[{time}]:{logLevel}:{str}'
        GuessImageLog.logHandle.write(logStr+"\n")
        GuessImageLog.logHandle.flush()
        # Print message if set
        if (GuessImageLog.printToo == True):
            print(logStr)

def closeLog():
    if (GuessImageLog.logHandle):
        GuessImageLog.logHandle.close()