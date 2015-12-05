import urllib;
import urllib2;
import sys;
import json;

import config;

userGUID = "";
userToken = "";

def login(username, password):

    loginURL = "https://cloud.commvault.com/webconsole/api/login";
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

        global userGUID;
        global userToken;
        userGUID = response["@userGUID"];
        userToken = response["@token"];

    else:
        print("Error logging in: " + str(response));


login("dsouzarc", "");

