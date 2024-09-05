from random import shuffle
from db_lib import *

# Show image and button if not answered
# Input:
#   userName - user name
#   gameId - game ID
#   data - {'class'/'imgClass' - image css classes, 'url' - src of image, 'iId' - image ID}
#   submitTest - text to show on submit button
#   finished - if game finished or not (False by default)
def showImageGameType1(userName, gameId, data, submitText, finished = False):
    html = f'''
        <div class="outer h310 w310"><div class="inner h310 w310">
            <img class="{data['class']} {data['imgClass']}" src="{data['url']}"/>
        </div></div>
    '''
    if (not finished):
        html = html +  f'''
            <div class="h30 w310 outer"><div class="inner_button">
            <form action="" method="get">
                <input type="hidden" name="user" value="{userName}">
                <input type="hidden" name="game" value="{gameId}">
                <input type="hidden" name="answer" value="{data['iId']}">
                <input type="submit" value="{submitText}" class="h20 w100"/>
            </form></div></div>
        '''
    return html

def showDivStr(text, classStr=None):
    classText = ''
    if (classStr):
        classText = f' class="{classStr}"'
    return f'<div{classText}>{text}</div>'

def showResultFooter(userName, gameInfo, finished):
    ret = ''
    if (finished):
        gameType = gameInfo.get('type')
        gameResult = gameInfo['result']
        gameComplexity = gameInfo.get('complexity')
        playAgainUrl = getBaseUrl() + f'?user={userName}&type={gameType}&complexity={gameComplexity}'
        playAgainLink = showDivStr(f'<a href="{playAgainUrl}">Play agin</a>')
        startNewGameUrl = getBaseUrl() + f'?user={userName}'
        startNewGameLink = showDivStr(f'<a href="{startNewGameUrl}">Choose another game type</a>')
        userAnswerId = gameInfo.get('user_answer')
        correctAnswerId = gameInfo.get('correct_answer')
        userAnswerStr = ''
        correctAnswer = ''
        corrIncorr = 'correctAnswer'
        corrIncorrStr = 'CORRECT'
        if gameType == 1:
            correctAnswer = Connection.getImageInfoById(correctAnswerId).get('imageName')
            if (not gameResult):
                corrIncorrStr = 'INCORRECT'
                corrIncorr = 'incorrectAnswer'
                userAnswer = Connection.getImageInfoById(userAnswerId).get('imageName')
                userAnswerStr = showDivStr(f'Your answer was "<span class="{corrIncorr}">{userAnswer}</span>"')
        else:
            correctAnswer = Connection.getCreatorNameById(correctAnswerId)
            if (not gameResult):
                corrIncorrStr = 'INCORRECT'
                corrIncorr = 'incorrectAnswer'
                userAnswer = Connection.getCreatorNameById(userAnswerId)
                userAnswerStr = showDivStr(f'Your answer was "<span class="{corrIncorr}">{userAnswer}</span>"')

        # show result
        correctAnswerStr = showDivStr(f'Correct answer is "<span class="correctAnswer">{correctAnswer}</span>"')
        answerResult = showDivStr(f'Your answer is <span class="{corrIncorr}">{corrIncorrStr}</span>')
        ret = ret + showDivStr(f'''
            {correctAnswerStr}
            {userAnswerStr}
            {answerResult}
            {playAgainLink}
            {startNewGameLink}
        ''')

    return ret

# Show game type 1 or error page
def showQuestionGameType1(queryParams, gameInfo, textQuestion):
    userName = queryParams.get('user')
    gameId = gameInfo['id']
    imageIds = []
    question = gameInfo['question']
    for item in question.split(' '):
        imageIds.append(int(item))
    data = []
    hor = 'hauto w300'
    ver = 'h300 wauto'
    shuffle(imageIds)
    correct_answer = ''
    answer = ''
    finished = (gameInfo['result'] != None)
    if (finished):
        correct_answer = int(gameInfo['correct_answer'])
        answer = int(gameInfo['user_answer'])
    for id in imageIds:
        url = Connection.getImageUrlById(id)
        orientation = int(Connection.getImageInfoById(id)['orientation'])
        img_class = ''
        if (finished):
            if (id == correct_answer):
                img_class = "correct_image"
            elif (id == answer):
                img_class = "user_answer"
        if (orientation == 1):
            data.append({'url':url,'class':ver,'iId':id,'imgClass':img_class})
        else:
            data.append({'url':url,'class':hor,'iId':id,'imgClass':img_class})
    pageTitle = "Question type 1 page:"
    if (gameInfo['result'] != None):
        pageTitle = "Result page"
    ret = f'''
        <div>{pageTitle}</div>
        <div class="textQuestion">{textQuestion}</div>
        <table class="gametype1">
            <tr><td>
    '''
    ret0 = showImageGameType1(userName, gameId, data[0], 1, finished)
    ret1 = showImageGameType1(userName, gameId, data[1], 2, finished)
    ret2 = showImageGameType1(userName, gameId, data[2], 3, finished)
    ret3 = showImageGameType1(userName, gameId, data[3], 4, finished)

    ret = ret + ret0 + '</td><td>' + ret1 + '</td></tr><tr><td>' + ret2 + '</td><td>' + ret3

    ret = ret + '''
                </td></tr>
        </table>
    '''

    ret = ret + showResultFooter(userName, gameInfo, finished)

    return ret

def showGameComplexityCombobox():
    # suffle creator
    complexities = ['Easy','Medium','Hard']
    ret = "<div><select name=\"complexity\">"
    i = 1
    for c in complexities:
        html = f"<option value=\"{i}\">{complexities[i]}</option>"
        ret = ret + html
        i = i + 1

    ret = ret + "</select></div>"
    return ret


def showCreatorsCombobox(creators):
    # suffle creator
    ret = "<div><select name=\"answer\">"
    for creator in creators:
        html = f"<option value=\"{creator['creatorId']}\">{creator['creatorName']}</option>"
        ret = ret + html

    ret = ret + "</select></div>"
    return ret

def showComplexityRadiobutton():
    complexity = [{'Txt':'Easy','Value':1,'checked':''},
                  {'Txt':'Medium','Value':2,'checked':' checked'}
                  ,{'Txt':'Hard',"Value":3,'checked':''}]
    html = '''
        <div class="complexity">
        <div>Choose game complexity:</div>
    '''
    for item in complexity:
        html = html + f'''
            <div>
                <input type="radio" id="complexity" name="complexity" value="{item['Value']}"{item['checked']}/>
                <label for="complexity">{item['Txt']}</label>
            </div>
        '''
    html = html + "</div>"
    return html

# Show game type 2 or error page
def showQuestionGameType2(queryParams, gameInfo, textQuestion):
    userName = queryParams.get('user')
    gameId = gameInfo['id']
    imageId = int(gameInfo['question'])
    complexity = gameInfo['complexity']
    hor = 'hauto w300'
    ver = 'h300 wauto'
    orientation = int(Connection.getImageInfoById(imageId)['orientation'])
    url = Connection.getImageUrlById(imageId)
    data = ''
    if (orientation == 1):
        data = {'url':url,'class':ver,'iId':imageId}
    else:
        data = {'url':url,'class':hor,'iId':imageId}
    pageTitle = "Question type 2 page:"
    if (gameInfo['result'] != None):
        pageTitle = "Result page"
    imageInfo = Connection.getImageInfoById(imageId)        
    combobox = ''
    correct_answer = ''
    answer = ''
    finished = (gameInfo['result'] != None)
    img_class = ''
    if (finished):
        correct_answer = int(gameInfo['correct_answer'])
        answer = int(gameInfo['user_answer'])
        if (answer == correct_answer):
            img_class = "correct_image"
        else:
            img_class = "user_answer"
    else:
        creatorId = imageInfo['creatorId']
        creatorName = imageInfo['creatorName']
        creators = Connection.getNCreators(CREATORS_IN_TYPE2_ANSWER, creatorId, complexity)
        creators.append({'creatorId':creatorId,'creatorName':creatorName})
        shuffle(creators)
        combobox = showCreatorsCombobox(creators)
    ret = f'''
        <div>{pageTitle}</div>
        <div class="textQuestion">{textQuestion}</div>
        <div class="outer w310">
            <img class="w300 {img_class}" src="{data['url']}"/>
        </div>
    '''
    if (not finished):
        ret = ret + f'''
            <div>
            <form action="" method="get">
                <input type="hidden" name="user" value="{userName}"/>
                <input type="hidden" name="game" value="{gameId}"/>
                {combobox}
                <div><input type="submit" class="h20 w100" value"Answer/></div>
            </form>
            </div>
        '''
    ret = ret + showResultFooter(userName, gameInfo, finished)
    return ret

# CSS for question page
def showGameStyles():
    css = '''<style type="text/css">
        div.complexity {border:1px solid black; width:200px;}
        table.gametype1 td {cellspacing: 10px;}
        .hauto {height: auto}
        .h300 {height:300px}
        .h310 {height:310px}
        .h30 {height:30px}
        .h20 {height:20px}
        .wauto {width:auto}
        .w300 {width:300px}
        .w310 {width:310px}
        .w100 {width:100px}
        .outer {align-items: center; justify-content: center; position: relative;}
        .inner {align-items: center; justify-content: center; display: grid; vertical-align: middle;}
        .inner_button {position: absolute; left:100px; top:5px}
        .error {border:1px solid red}
        table.list, table.list td, table.list th
        {
            border: 1px solid black;
            border-collapse:collapse
        }
        table.list td, table.list th {padding: 10px;}
        .textQuestion {color: blue;}
        .correct_image {border: 3px solid green}
        .user_answer {border: 3px solid red}
        .correctAnswer {color: green;}
        .incorrectAnswer {color: red;}
        </style>
    '''
    return css

# Show start of the page
def showHeader():
    css = showGameStyles()
    start1 = '''<!DOCTYPE html>
        <html>
        <head>
        <title>Игра “Угадай картину"</title>
    '''
    start2 = '''
        </head>
        <body>
    '''
    return start1 + css + start2

# Show footer of the page
def showFooter():
    footer = '''
        </body></html>
    '''
    return footer

# Show login page
def showLoginPage(baseUrl):
    html = f'''
        Login:
        <form action="" method="get">
            <input type="text" name="user" required/>
            <input type="submit" value="Login"/>
        </form>
        <div><a href="{baseUrl}?newuser">Register new user</a></div>
    '''
    return html

# Show new user page
def showNewUserPage():
    html = '''
        <div>Create new user</div>
        <form action="" method="get">
            <input type="text" name="user" required/>
            <input type="hidden" name="registeruser"/>
            <input type="Submit" value="Register"/>
        </form>
    '''
    return html

# Show game type page
# Input: 
#   params - query parameters
#   game_types - array with game types [id, name, question]
def showGameTypePage(params, game_types):
    html = '''
        <div>Game Type page:</div>
    '''
    baseUrl = getBaseUrl()
    userName = params.get('user')
    urlAll = baseUrl + f'?user={userName}&list_all'
    urlUnfinished = baseUrl + f'?user={userName}&list_unfinished'
    urlFinished = baseUrl + f'?user={userName}&list_finished'
    links = [['Show all games',urlAll],['Show UnFinished games',urlUnfinished],['Show Finished games',urlFinished]]
    htmlForm = ''

    comlexityRadiobutton = showComplexityRadiobutton()

    htmlForm = htmlForm + f'''
        <div>
        <form action="" method="get">
            <input type="hidden" name="user" value="{params['user']}"/>
            {comlexityRadiobutton}
    '''

    for arr in game_types:
        htmlForm = htmlForm + showDivStr(f'''
                <button type="submit" name="type" value="{arr[0]}">{arr[1]}</button>
        ''')
    htmlForm = htmlForm + f'''
                </form>
            </div>
        '''
    htmlLinks = ''
    for link in links:
        htmlLinks = htmlLinks + f'<div><a href="{link[1]}">{link[0]}</a></div>'

    return html + htmlForm + htmlLinks

def showQuestionPage(params, gameInfo, textQuestion):
    gameType = gameInfo['type']
    content = "Default question game page:"
    if (gameType == 1):
        content = showQuestionGameType1(params, gameInfo, textQuestion)
    elif (gameType == 2):
        content = showQuestionGameType2(params, gameInfo, textQuestion)
    else:
        content = "Not implemented yet"

    return content

def showListPage(params, games, list_type):
    userName = params.get('user')
    htmlStart = f'''
        <div>List games page ({list_type}):</div>
    '''
    content = ''
    if (len(games) == 0): # No games found
        url = getBaseUrl() + f'?user="{userName}"'
        content = f'''
        <div>No games found</div>
        <div><a href="{url}">Start new game</a></div>
        '''
    else:
        content = '<table class="list">'
        # Show header
        content = content + "<tr>"
        content = content + f"<th>id</th>"
        content = content + f"<th>userId</th>"
        content = content + f"<th>gameType</th>"
        content = content + f"<th>created</th>"
        content = content + f"<th>question</th>"
        content = content + f"<th>correct_answer</th>"
        content = content + f"<th>user_answer</th>"
        content = content + f"<th>result</th>"
        content = content + f"<th>finished</th>"
        content = content + f"<th>show</th>"
        content = content + "</tr>"
        # Show rows
        for gi in games:
            showHTML = f'''
                <form method="get">
                    <input type="hidden" name="user" value="{userName}"/>
                    <input type="hidden" name="game" value="{gi['id']}"/>
                    <input type="submit" value="Show"/>
                </form>
                '''
            created = gi['created'].strftime("%d-%m-%Y %H:%M:%S")
            finished = ''
            if (gi['finished'] != None):
                finished = gi['finished'].strftime("%d-%m-%Y %H:%M:%S")
            result = gi['result']
            if (result == None):
                result = ''
            user_answer = gi['user_answer']
            if (user_answer == None):
                user_answer = ''

            content = content + "<tr>"
            content = content + f"<th>{gi['id']}</th>"
            content = content + f"<th>{gi['user']}</th>"
            content = content + f"<th>{gi['type']}</th>"
            content = content + f"<th>{created}</th>"
            content = content + f"<th>{gi['question']}</th>"
            content = content + f"<th>{gi['correct_answer']}</th>"
            content = content + f"<th>{user_answer}</th>"
            content = content + f"<th>{result}</th>"
            content = content + f"<th>{finished}</th>"
            content = content + f"<th>{showHTML}</th>"

        content = content + "</table>"
    return htmlStart+content

def showErrorPage(error):
    err = showError(error)
    baseUrl = getBaseUrl()
    html = f'''
        <div>Please <a href="{baseUrl}">try again</a></div>
    '''
    return err + html    

# Return error message
def showError(error):
    html = f'''
        <div><span class="error">Error: {error}</span></div>
    '''
    return html