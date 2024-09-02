from os import listdir, system
from subprocess import run, STDOUT, PIPE
from guess_image_lib import *
from img_fs_lib import *

S3BUCKET = 's3://guess-image'

# Build cmd to upload image to S3
def buildUploadCmd(imgName):
    filePath = buildImgPathName(imgName)
    return 's3cmd put "' + filePath + '" ' + S3BUCKET

# Upload image to Bucket
def uploadImg(imgName):
    cmd = buildUploadCmd(imgName)
    return system(cmd)

def getImgsInBucket():    
    # указывайте полный путь к запускаемой 
    # программе/команде или она не будет работать
    cmd = 's3cmd ls ' + S3BUCKET
    # перенаправляем `stdout` и `stderr` в переменную `output`
    res = run(cmd.split(), stdout=PIPE, text=True)
    output = res.stdout
    arrOutput = output.split("\n")

    arrFinal = set()
    for s in arrOutput:
        index = s.find(S3BUCKET)
        if (index == -1):
            # No file - just skip
            continue
        index = index + len(S3BUCKET)+1 # get index of image name
        image = s[index:] # get image
        arrFinal.add(image) # save

    return arrFinal

# Check if image is in bucket
def checkImgInBucket(imgName, imgsInBucket):
    ret = False
    if (imgName in imgsInBucket):
        ret = True
    return ret

def bulkUpload(creators, titles, years):
    imgsInBucket = getImgsInBucket()

    for i in range(0, len(creators)):
        # Check is img is in bucket
        imgName = buildImgName(creators[i], titles[i], years[i])
        if (not checkImgInBucket(imgName, imgsInBucket)):
            # upload image to bucket
            print(f"Uploading {imgName}")
            ret = uploadImg(imgName)
            if (ret != 0):
                # Fail
                print(f'ERROR: Cannot upload image {imgName}. Returned: {ret}')
                break
        else:
            #print(f"Skip uploading (already uploaded): {imgName}")
            pass

