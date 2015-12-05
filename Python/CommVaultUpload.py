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

#4 Megabytes. Is actually 1024, but using 1000 for simplicity reasons
maxSingleSize = 1000 * 1000 * 4;

currentDirectory = "";
userGUID = "";
userToken = "";


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

    response = urllib2.urlopen(request, loginXML);

    if response.code == 200:
        print("Response Code 200");
    else:
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
            return True;
        else:
            return False;

    else:
        print("Error logging in: " + str(response));
        return False;



def beginChunkUpload(pathToFile):

    print("beginning");

def uploadFile(pathToFile):

    if not os.path.isfile(pathToFile):
        print("ERROR COULD NOT FIND FILE: " + pathToFile);
        return;

    fileSize = os.path.getsize(pathToFile);

    if fileSize > maxSingleSize:
        beginChunkUpload(pathToFile);

    else:
        request = urllib2.Request(uploadFullFile);

        fileName = os.path.basename(pathToFile);
        lastModified = int(os.path.getmtime(pathToFile));

        path = os.path.split(pathToFile)[0];
        cloudPath = "\Drive" + path.replace("/", "\\"); # "\Drive\Ryan\\";

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
            if int(response['@errorCode']) == 200:
                print("Successfully uploaded " + fileName + "\tpath: " + pathToFile + "\tto cloud location: " + cloudPath);
                return;

        print("ERROR UPLOADING " + pathToFile + " MESSAGE: " + str(response));


#DELETE HERE
currentDirectory = str(os.getcwd()) + "/";

#KEEP

if login("dsouzarc", ""):
    print("Successful login");

    fileName = "";

    if len(sys.argv) == 1:
        fileName = raw_input("Enter file name to upload or '/' to upload all files in this directory and subdirectories:\n");
    elif len(sys.argv) == 2:
        fileName = sys.argv[1];

    uploadFile(fileName);



else:
    print("Unsuccessful login");
    sys.exit(0);

