import base64;
import json;
import getpass; 
import os;


####################################################
# Written by Ryan D'souza
# A password manager completely written in Python
####################################################


#Store data in hidden file in hidden folder in home directory
directory_path = str(os.path.expanduser("~")) + "/.my_credential_manager/";
file_path = directory_path + ".credential_files.json";

#Create path if needed
if not os.path.exists(directory_path):
    print("Initialized credential manager: " + file_path);
    os.makedirs(directory_path);

#Load data from file
if os.path.isfile(file_path):
    try:
        with open(file_path) as credential_file:
            credentials = json.load(credential_file);
            print("Credentials loaded");
    except ValueError:
        print("Value error for loading existing credentials from file. Building new file");
        credentials = {};
else:
    print("No existing credentials");
    credentials = {};


#################################
# UTILITY & MANAGERIAL METHODS
#################################


#Save credentials
def save_credentials(usernameKey, username, password, passwordKey):
    
    if usernameKey in credentials:
        print("Username already exists for '" + usernameKey + "'.");
        answer = raw_input("Override? y/n: ");

        if answer == 'y':
            credentials[usernameKey] = base64.b64encode(username);
            credentials[passwordKey] = base64.b64encode(password);

            with open(file_path, 'w') as file:
                json.dump(credentials, file, sort_keys = True, indent = 4, ensure_ascii = False);
                print("Credentials saved");
                return;
        else:
            print("Cancelled");
            return;
    else:
        credentials[usernameKey] = base64.b64encode(username);
        credentials[passwordKey] = base64.b64encode(password);
        
        with open(file_path, 'w') as file:
            json.dump(credentials, file, sort_keys = True, indent = 4, ensure_ascii = False);
            print("Credentials saved");
            return;

#Set key to value
def save_key(key, value):
    credentials[key] = base64.b64encode(value);
    
    with open(file_path, 'w') as file:
        json.dump(credentials, file, sort_keys = True, indent = 4, ensure_ascii = False);
        print("Key and value successfully saved");

#Save key to value (with secure prompt)
def save_key_prompt():
    key = raw_input("Key: ");
    value = raw_input("Value: ");

    save_key(key, value);

#Get value/credential associated with key
def get_key(key):

    if key in credentials:
        return base64.b64decode(credentials[key]);
    else:
        raise KeyError("No value found for: " + key);

#Check to see if a value/credential exists
def does_key_exist(key):
    return key in credentials;

#Delete a credential
def delete_key(key):

    if key in credentials:
        del credentials[key];
        
        with open(file_path, 'w') as file:
            json.dump(credentials, file, sort_keys = True, indent = 4, ensure_ascii = False);
            print("Value for '" + key + "' has been deleted. Credentials saved");
            return;
        print("Error saving credentials");
    else:
        print("Delete failed; '" + key + "' does not exist");

#Prompts for credentials, then saves them
def save_credentials_prompt():
    usernameKey = raw_input("Username key: ")   
    username = raw_input("Username: ");
    passwordKey = raw_input("Password key: ");
    password = getpass.getpass("Password: ");

    save_credentials(usernameKey, username, password, passwordKey);

#Only prompt for credentials and then save them if this file is run from main ( 'python CredentialManager.py' )
if __name__ == "__main__":
    save_credentials_prompt();
