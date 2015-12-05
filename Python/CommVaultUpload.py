import urllib;
import urllib2;
import config;

def login(username, password):

    loginURL = "https://cloud.commvault.com/webconsole/api/login";
    password = config.COMMVAULT_BASE; #password.encode('base64');

    loginXML = "<DM2ContentIndexing_CheckCredentialReq mode=\"webconsole\" flags=\"2\" deviceId=\"68FAB736-80F3-4F39-B1FA-AC35A3C7BAB3\" username=\"{0}\" password=\"{1}\" />";

    loginXML = loginXML.replace("{0}", username);
    loginXML = loginXML.replace("{1}", password);

    print(loginXML);

    contentType = "application/xml; charset=utf-8";
    accept = "application/json";

    request = urllib2.Request(loginURL);
    request.add_header('Content-Type', contentType);
    request.add_header('Accept', accept);

    response = urllib2.urlopen(request, loginXML);

    print(response.read());

login("dsouzarc", "");
