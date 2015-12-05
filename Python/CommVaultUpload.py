import urllib;
import itertools
import mimetools
import mimetypes
import base64;
from cStringIO import StringIO
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


class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        return
    
    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, fileHandle, mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        self.files.append(mimetype, body)
        #self.files.append((fieldname, filename, mimetype, body))
        return
    
    def __str__(self):
        """Return a string representing the form data, including attached files."""
        # Build a list of lists, each containing "lines" of the
        # request.  Each part is separated by a boundary string.
        # Once the list is built, return a string where each
        # line is separated by '\r\n'.  
        parts = []
        part_boundary = '--' + self.boundary
       
        # Add the form fields
        parts.extend(
            [ part_boundary,
              'Content-Disposition: form-data; name="%s"' % name,
              '',
              value,
            ]
            for name, value in self.form_fields
            )
        # Add the files to upload
        parts.extend(
            [ part_boundary,
              'Content-Disposition: file; name="%s"; filename="%s"' % \
                 (field_name, filename),
              'Content-Type: %s' % content_type,
              '',
              body,
            ]
            for field_name, filename, content_type, body in self.files
            )
        
        # Flatten the list and add closing boundary marker,
        # then return CR+LF separated data
        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)









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
        path = os.path.split(pathToFile)[0];
        lastModified = int(os.path.getmtime(pathToFile));

        cloudPath = "\Drive\Ryan\\";

        headers = {
            "Host": server,
            "Accept": "application/xml",
            "Authtoken": userToken,
            "Content-type": "text/plain",
            "ParentFolderPath": base64.b64encode(':'.join(cloudPath)),
            "FileModifiedtime": str(lastModified),
            "FileModifiedTime": str(lastModified),
            "FileSize": str(fileSize),
            "FileName": base64.b64encode(':'.join(fileName)),
        }

        print(headers);
        print("\n\n");

        request.add_data(open(pathToFile).read())
        request.headers = headers;
        #print
        print 'OUTGOING DATA:'
        print request.get_data()

        print
        print 'SERVER RESPONSE:'
        print urllib2.urlopen(request).read()


    
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

