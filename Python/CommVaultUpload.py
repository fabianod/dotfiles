import urllib;
import getpass;
import base64;
import os;
import urllib2;
import sys;
import json;


######################################################################################
# Written by Ryan D'souza
# Quickly uploads files and directories to my cloud storage
# Very light weight, uses standard Python libraries, only requires a password
#
# For run instructions, see
#   https://github.com/dsouzarc/dotfiles/tree/master/Python#commvault-uploader
######################################################################################


####################################
####        BASE URLS           ####
####################################

server = "cloud.commvault.com";
baseURL = "https://" + server + "/webconsole/";
mainAPIURL = baseURL + "api/";

loginURL = mainAPIURL + "login";
uploadFullFile = mainAPIURL + "drive/file/action/upload?uploadType=fullFile";
uploadChunkedFileInitial = mainAPIURL + "drive/file/action/upload?uploadType=chunkedFile";
uploadedChunkedFileForceStart = mainAPIURL + "drive/file/action/upload?uploadType=chunkedFile&forceRestart=true&requestId=";
uploadChunkedFileRequestIdURL = mainAPIURL + "drive/file/action/upload?uploadType=chunkedFile&requestId=";

#4 Megabytes. Is actually 1024, but using 1000 for simplicity reasons
maxSingleSize = 1000 * 1000 * 4;

currentDirectory = "";
userGUID = "";
userToken = "";


####################################
####    HANDLES LOGGING IN      ####
####################################

def login(username, password):

    password = password.encode('base64');

    loginXML = "<DM2ContentIndexing_CheckCredentialReq mode=\"webconsole\" flags=\"2\" deviceId=\"68FAB736-80F3-4F39-B1FA-AC35A3C7BAB3\" username=\"{0}\" password=\"{1}\" />";

    loginXML = loginXML.replace("{0}", username);
    loginXML = loginXML.replace("{1}", password);

    contentType = "application/xml; charset=utf-8";
    accept = "application/json";

    request = urllib2.Request(loginURL);
    request.add_header('Content-Type', contentType);
    request.add_header('Accept', accept);

    print("Logging in");
    response = urllib2.urlopen(request, loginXML);

    if response.code != 200:
        print("Error. Respond code: " + str(response.code));
        sys.exit(0);

    response = json.loads(response.read());

    if 'DM2ContentIndexing_CheckCredentialResp' in response:
        response = response["DM2ContentIndexing_CheckCredentialResp"];

        if '@userGUID' not in response or '@token' not in response:
            print("Incorrect username or password: " + str(response));
            return False;

        global userGUID;
        global userToken;
        global currentDirectory;

        userGUID = response["@userGUID"];
        userToken = response["@token"];
        currentDirectory = str(os.getcwd()) + "/";

        if len(userGUID) != 0 and len(userToken) != 0:
            print("Successful login");
            return True;

    print("Error logging in: " + str(response));
    return False;


####################################
####     GENERATES HEADERS      ####
####################################

def generateHeaders(pathToFile):

    fileSize = os.path.getsize(pathToFile);
    fileName = os.path.basename(pathToFile);
    lastModified = long(os.path.getmtime(pathToFile));

    path = os.path.split(pathToFile)[0];
    cloudPath = "\Drive" + path.replace("/", "\\"); 

    headers = {
        "Host": server,
        "Accept": "application/json",
        "Authtoken": userToken,
        "Content-type": "text/plain",
        "ParentFolderPath": base64.b64encode(cloudPath),
        "FileModifiedtime": str(lastModified),
        "FileModifiedTime": str(lastModified),
        "FileSize": str(fileSize),
        "FileName": base64.b64encode(fileName)
    }

    return headers, fileName, cloudPath;



####################################
####     FOR CHUNK UPLOADING    ####
####################################

def uploadFileInChunks(pathToFile):

    print("Beginning to upload " + os.path.basename(pathToFile));

    #Gets the request id for the upload
    requestID, chunkOffset = handleConflict(pathToFile);

    fileSize = os.path.getsize(pathToFile);
    fileToUpload = open(pathToFile, 'rb');

    #If it's already uploaded - same file size and last modified date
    if chunkOffset == -1:
        print("Successfully finished uploading " + os.path.basename(pathToFile));
        return;

    #Partial upload, start reading from where we left off
    if chunkOffset != 0:
        fileToUpload.seek(chunkOffset);

    #Go through the remaining bytes
    while(chunkOffset + (maxSingleSize) < fileSize):

        #Get the chunk, create our url, and upload it
        chunk = fileToUpload.read(maxSingleSize);
        url = uploadChunkedFileRequestIdURL + str(requestID);
        requestIDOld, chunkResponse = beginChunkUpload(pathToFile, chunk, False, url);

        #Same as above - file has already been uploaded
        if chunkResponse == -1:
            print("Successfully finished uploading " + os.path.basename(pathToFile));
            return;
        chunkOffset += 4 * 1000 * 1000;

    #The last chunk gets a special tag, so it can't be in the while loop
    remainder = fileSize - chunkOffset;
    print("HERE: " + str(fileSize) + "\t" + str(chunkOffset));
    chunk = fileToUpload.read(remainder);

    #Upload that last chunk
    url = uploadChunkedFileRequestIdURL + str(requestID);
    beginChunkUpload(pathToFile, chunk, True, url);
    print("Successfully finished uploading " + os.path.basename(pathToFile));


########################################################################
####     GETS REQUESTID + LAST CHUNK FOR UPLOADING IN CHUNKS        ####     
########################################################################

def handleConflict(pathToFile):

    #Create our request and remove excess parameters
    request = urllib2.Request(uploadChunkedFileInitial);
    headers, fileName, cloudPath = generateHeaders(pathToFile);
    headers["FileEOF"] = "0";
    del headers["Content-type"];
    request.headers = headers;

    #Get the first chunk of data
    request.add_data(open(pathToFile, 'rb').read(maxSingleSize));

    #Try because python throws an exception if the http status isn't 200
    try:
        response = urllib2.urlopen(request);

        #409 = partially completed uploaded. 200 = first upload
        if response.code == 409 or response.code == 200:
            response = json.loads(response.read());
            response = response['DM2ContentIndexing_UploadFileResp'];
            requestID = response['@requestId'];
            chunkOffset = long(response['@chunkOffset']);
            print("Found duplicate for " + fileName + "\tChunk: " + str(chunkOffset) + str(response));
            return requestID, chunkOffset;

        #Some other http status code
        else:
            print("ERROR: " + str(response));
            return 0, 0;

    #Any exceptions
    except urllib2.HTTPError, err:

        #Handle these the same way
        if err.code == 409 or err.code == 200:
            response = json.loads(err.read());
            response = response['DM2ContentIndexing_UploadFileResp'];
            requestID = response['@requestId'];
            chunkOffset = long(response['@chunkOffset']);
            print("Found duplicate for " + fileName + "\tChunk: " + str(chunkOffset) + "\t" + str(response));
            return requestID, chunkOffset;

        else:
            print("ERROR: " + str(err.read()));
            return 0, 0;


##############################################
####     DOES THE BULK OF CHUNK UPLOADS  ####
#############################################

def beginChunkUpload(pathToFile, chunk, isLastChunk, url):

    #Get our headers, remove extraneous headers
    request = urllib2.Request(url);
    headers, fileName, cloudPath = generateHeaders(pathToFile);

    del headers["Content-type"];
    del headers["ParentFolderPath"];
    del headers["FileModifiedtime"];
    del headers["FileModifiedTime"];
    del headers["FileSize"];
    del headers["FileName"];

    #The last chunk has a different tag
    if isLastChunk:
        headers["FileEOF"] = "1";
    else:
        headers["FileEOF"] = "0";

    request.headers = headers;
    request.add_data(chunk);

    try:
        response = urllib2.urlopen(request);
    except urllib2.HTTPError, err:

        #Problematic error codes
        if err.code == 400 or err.code == 403:
            print("IN CHUNK BAD REQUEST FOR " + fileName + "\t" + err.read());
            return 0, 0;

        #Duplicate - already partially uploaded
        elif err.code == 409:
            print("DUPLICATE FOUND: " + requestID + "\t" + str(chunkOffSet) + " RETURNED");
            return requestID, chunkOffSet;

        #Yay for more problems
        else:
            print("ERROR: " + str(err.code) + " OUTPUT: " + err.read());
            raise;

    #Same as above -- more problems
    if response.code != 200:
        print("ERROR CHUNK UPLOADING " + pathToFile + " Response code: " + str(response.code));
        return;

    #No error codes, begin parsing the data
    response = json.loads(response.read());
    response = response['DM2ContentIndexing_UploadFileResp'];

    if "@errorCode" in response:

        #Chunk was successfully uploaded
        if long(response['@errorCode']) == 200:
            chunkOffSet = long(response['@chunkOffset']);
            requestID = ""; #response['@requestId'];
            print("Successfully uploaded chunk of " + fileName + "\tpath: " + pathToFile + "\tto cloud location: " + cloudPath + str(response));
            return requestID, chunkOffSet;

    #More error codes
    print("ERROR CHUNK UPLOADING " + pathToFile + " MESSAGE: " + str(response));
    return 0, 0


##############################################
####     UPLOADS SMALL FILES (< 4MB)     ####
#############################################

def uploadFile(pathToFile):

    if not os.path.isfile(pathToFile):
        print("ERROR COULD NOT FIND FILE: " + pathToFile);
        return;

    fileSize = os.path.getsize(pathToFile);

    #File too big, we got to chunk it
    if fileSize > maxSingleSize and 1 == 2:
        uploadFileInChunks(pathToFile);

    #We can handle it here
    else:
        request = urllib2.Request(uploadFullFile);

        headers, fileName, cloudPath = generateHeaders(pathToFile);

        print("Beginning to upload " + fileName + " to " + cloudPath);

        request.add_data(open(pathToFile, 'rb').read());
        request.headers = headers;

        try:
            response = urllib2.urlopen(request);
        except urllib2.HTTPError, err:
            print("ERROR UPLOADING " + fileName + " CODE: " + str(err.code) + " LOG: " + str(request.read()));
            return;

        #Unsuccessful upload for whatever reason
        if response.code != 200:
            print("ERROR UPLOADING " + pathToFile + " Response code: " + str(response.code));
            return;

        response = json.loads(response.read());

        if 'DM2ContentIndexing_UploadFileResp' in response:
            response = response['DM2ContentIndexing_UploadFileResp'];

        if "@errorCode" in response:
            if long(response['@errorCode']) == 200:
                print("Successfully uploaded " + fileName + "\tpath: " + pathToFile ); #+ "\tto cloud location: " + cloudPath);
                return;

        print("ERROR UPLOADING " + pathToFile + " MESSAGE: " + str(response));



##############################################
####     MAIN METHOD - THE GOOD STUFF    ####
#############################################

password = getpass.getpass("Enter your password:\n");

#Login
if login("dsouzarc", password):

    currentDirectory = str(os.getcwd()) + "/";
    fileName = None;

    #No input - prompt the user for file names or directories to upload
    if len(sys.argv) == 1:
        fileName = raw_input("Enter file name to upload or '/' to upload all files in this directory and subdirectories:\n");

    #Given a file as a parameter at run time
    elif len(sys.argv) == 2:
        fileName = sys.argv[1];

    #Given a list of files at run time
    else:
        for fileName in sys.argv[1:]:
            fileLocation = currentDirectory = fileName;
            uploadFile(fileLocation);

    #Upload all files in this directory and its subdirectories --> user entered '/' or '.'
    if fileName == "/" or fileName == ".":
        print("GOOD TO GO");
        for root, subFolders, files in os.walk(os.getcwd() + "/"):
            for name in files:
                if name != "CommVaultUpload.py" and name != ".DS_Store":
                    filePath = os.path.join(root, name);
                    uploadFile(filePath);

    #Just one file entered
    elif fileName != None:
        uploadFile(fileName);

else:
    print("Unsuccessful login");
    sys.exit(0);
