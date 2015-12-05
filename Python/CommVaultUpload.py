import urllib;
import base64;
import os;
import urllib2;
import sys;
import json;

import config;

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

    password = config.COMMVAULT_BASE; #password.encode('base64');

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

def handleConflict(pathToFile):

    request = urllib2.Request(uploadChunkedFileInitial);
    headers, fileName, cloudPath = generateHeaders(pathToFile);
    headers["FileEOF"] = "0";
    del headers["Content-type"];
    request.headers = headers;
    request.add_data(open(pathToFile, 'rb').read(4 * 1000 * 1000));
    try:
        response = urllib2.urlopen(request);
        if response.code == 409 or response.code == 200:
            response = json.loads(response.read());
            response = response['DM2ContentIndexing_UploadFileResp'];
            requestID = response['@requestId'];
            chunkOffset = long(response['@chunkOffset']);
            print("Found duplicate for " + fileName + "\tChunk: " + str(chunkOffset) + str(response));
            return requestID, chunkOffset;
        else:
            print("ERROR: " + str(response));
            return 0, 0;
    except urllib2.HTTPError, err:
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

def uploadFileInChunks(pathToFile):

    print("Beginning to upload " + os.path.basename(pathToFile));

    requestID, chunkOffset = handleConflict(pathToFile);

    fileSize = os.path.getsize(pathToFile);
    fileToUpload = open(pathToFile, 'rb');

    if chunkOffset == -1:
        print("Successfully finished uploading " + os.path.basename(pathToFile));
        return;

    if chunkOffset != 0:
        fileToUpload.seek(chunkOffset);

    while(chunkOffset + (4 * 1000 * 1000) < fileSize):
        print("Uploading new chunk");
        chunk = fileToUpload.read(4 * 1000 * 1000);
        url = uploadChunkedFileRequestIdURL + str(requestID);
        requestIDOld, chunkResponse = beginChunkUpload(pathToFile, chunk, False, url);

        if chunkResponse == -1:
            print("Successfully finished uploading " + os.path.basename(pathToFile));
            return;
        #chunkOffset += 4 * 1000 * 1000;

    remainder = fileSize - chunkOffset;
    print("HERE: " + str(fileSize) + "\t" + str(chunkOffset));
    chunk = fileToUpload.read(remainder);

    if chunk:
        print("CHUNK IS GOOD");
    else:
        print("CHUNK IS BAD");

    url = uploadChunkedFileRequestIdURL + str(requestID);
    beginChunkUpload(pathToFile, chunk, True, url);
    print("Successfully finished uploading " + os.path.basename(pathToFile));

def beginChunkUpload(pathToFile, chunk, isLastChunk, url):

    request = urllib2.Request(url);
    headers, fileName, cloudPath = generateHeaders(pathToFile);

    del headers["Content-type"];
    del headers["ParentFolderPath"];
    del headers["FileModifiedtime"];
    del headers["FileModifiedTime"];
    del headers["FileSize"];
    del headers["FileName"];

    if isLastChunk:
        print("GOT TO LAST CHUNK");
        #headers["FileEOF"] = "1";
    else:
        headers["FileEOF"] = "0";

    request.headers = headers;
    request.add_data(chunk);

    try:
        response = urllib2.urlopen(request);
    except urllib2.HTTPError, err:

        if err.code == 400 or err.code == 403:
            print("IN CHUNK BAD REQUEST FOR " + fileName + "\t" + err.read());
            return 0, 0;

        elif err.code == 409:
            print("DUPLICATE FOUND: " + requestID + "\t" + str(chunkOffSet) + " RETURNED");
            return requestID, chunkOffSet;
        else:
            print("ERROR: " + str(err.code) + " OUTPUT: " + err.read());
            raise;

    if response.code != 200:
        print("ERROR CHUNK UPLOADING " + pathToFile + " Response code: " + str(response.code));
        return;

    response = json.loads(response.read());
    print(response);

    response = response['DM2ContentIndexing_UploadFileResp'];

    if "@errorCode" in response:
        if long(response['@errorCode']) == 200:
            chunkOffSet = long(response['@chunkOffset']);
            requestID = ""; #response['@requestId'];
            print("Successfully uploaded chunk of " + fileName + "\tpath: " + pathToFile + "\tto cloud location: " + cloudPath + str(response));
            return requestID, chunkOffSet;

    print("ERROR CHUNK UPLOADING " + pathToFile + " MESSAGE: " + str(response));
    return 0, 0


'''
uploadChunkedFileInitial = mainAPIURL + "drive/file/action/upload?uploadType=chunkedFile";
uploadedChunkedFileForceStart = mainAPIURL + "drive/file/action/upload?uploadType=chunkedFile&forceRestart=true&requestId=";
uploadChunkedFileRequestIdURL = @"drive/file/action/upload?uploadType=chunkedFile&requestId=";
'''

def uploadFile(pathToFile):

    if not os.path.isfile(pathToFile):
        print("ERROR COULD NOT FIND FILE: " + pathToFile);
        return;

    fileSize = os.path.getsize(pathToFile);

    if fileSize > maxSingleSize and 1 == 2:
        uploadFileInChunks(pathToFile);

    else:
        request = urllib2.Request(uploadFullFile);

        headers, fileName, cloudPath = generateHeaders(pathToFile);

        print("Beginning to upload " + fileName + " to " + cloudPath);

        request.add_data(open(pathToFile, 'rb').read());
        request.headers = headers;

        response = urllib2.urlopen(request);

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


#DELETE HERE
currentDirectory = str(os.getcwd()) + "/";

#KEEP

if login("dsouzarc", ""):

    fileName = "";

    if len(sys.argv) == 1:
        fileName = raw_input("Enter file name to upload or '/' to upload all files in this directory and subdirectories:\n");
    elif len(sys.argv) == 2:
        fileName = sys.argv[1];

    uploadFile(fileName);



else:
    print("Unsuccessful login");
    sys.exit(0);

