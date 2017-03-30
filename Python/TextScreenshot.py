#!/usr/bin/python

import requests
from PIL import Image

import sys
from datetime import datetime

import CredentialManager

#######################################################################
# Written by Ryan D'souza
#
# Takes a link, calls ScreenshotLayer's API to get a screenshot
# Of the text at that link
#
# Sends that screenshot to my phone
#
# Dependency: CredentialManager.py
#   See: tiny.cc/credentialManager.py
#######################################################################

#MailGun information
mailGunURL = "https://api.mailgun.net/v3/sandboxee071b43671c4663b8790099f51085b7.mailgun.org/messages"
mailGunAuth = ('api', CredentialManager.get_value("MailGunAPIKey"))

#Screenshot Layer Image Information
defaultSaveLocation = "/Users/Ryan/Dropbox/Screenshots"

screenshotLayerURL = "http://api.screenshotlayer.com/api/capture"
accessKey = CredentialManager.get_value("ScreenshotLayerAPI")

linkToScreenshot = None

#If we got the link to screenshot as a parameter
if len(sys.argv) == 2:
    linkToScreenshot = sys.argv[1]

#Otherwise, just prompt for it
else:
    linkToScreenshot = raw_input("Enter link to screenshot: ")

parameters = {
    "access_key": accessKey,
    "url": linkToScreenshot,
    "viewport": "2500x2500",
    "width": 2500
}

#Regex magic to get the domain from the link
domainName = linkToScreenshot.split("//")[-1].split("/")[0]
todaysDate = datetime.today().strftime('%d-%b-%Y %H:%M:%S')
fileName = defaultSaveLocation + "/From " + domainName + " on " + todaysDate + ".png"

imageRequest = requests.get(screenshotLayerURL, params=parameters, stream=True)
imageRequest.raw.decode_content = True # handle spurious Content-Encoding
image = Image.open(imageRequest.raw)

image.save(fileName, "PNG")
print("Saved image to: " + fileName)

data = {
    'from': 'dsouzarc+mailgun@gmail.com',
    'to': 'dsouzarc@gmail.com',
    'subject': domainName,
    'text': linkToScreenshot
}
files = [("attachment", open(filePath))]

response = requests.post(mailGunURL, auth=mailGunAuth, data=data, files=files)

if response.status_code == 200:
    print("Successfully sent to self")
else:
    response.raise_for_status()