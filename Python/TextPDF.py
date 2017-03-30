#!/usr/bin/python

import requests
from PIL import Image

import sys
from datetime import datetime

import CredentialManager

#######################################################################
# Written by Ryan D'souza
#
# Takes a link, calls PDFLayer's API to get a PDF representation
# Of the text at that link
#
# Sends that PDF to my phone
#
# Dependency: CredentialManager.py
#   See: tiny.cc/credentialManager.py
#######################################################################

#MailGun information
mailGunURL = "https://api.mailgun.net/v3/sandboxee071b43671c4663b8790099f51085b7.mailgun.org/messages"
mailGunAuth = ('api', CredentialManager.get_value("MailGunAPIKey"))

#PDF Location
defaultSaveLocation = "/Users/Ryan/Dropbox/Screenshots/"
pdfLayerURL = "http://api.pdflayer.com/api/convert"
accessKey = CredentialManager.get_value("PDFLayerAPIKey")

linkToPDF = None

#If we got the link to the PDF as a parameter
if len(sys.argv) == 2:
    linkToPDF = sys.argv[1]

#Otherwise, just prompt for it
else:
    linkToPDF = raw_input("Enter link to screenshot: ")

parameters = {
    "access_key": accessKey,
    "document_url": linkToPDF,
    "page_size": "A1" #Big paper size - fewer pages
}

#Regex magic to get the domain from the link
domainName = linkToPDF.split("//")[-1].split("/")[0]
todaysDate = datetime.today().strftime('%d-%b-%Y %H:%M:%S')
fileName = "From " + domainName + " on " + todaysDate + ".pdf"
filePath = defaultSaveLocation + fileName

pdfRequest = requests.get(pdfLayerURL, params=parameters, stream=True)

with open(filePath, 'wb') as pdfFile:
    for chunk in pdfRequest.iter_content(2000):
        pdfFile.write(chunk)

print("Saved PDF to: " + filePath)

data = {
    'from': 'dsouzarc+mailgun@gmail.com',
    'to': 'dsouzarc@gmail.com',
    'subject': domainName,
    'text': linkToPDF
}
files = [("attachment", open(filePath))]

response = requests.post(mailGunURL, auth=mailGunAuth, data=data, files=files)

if response.status_code == 200:
    print("Successfully sent to self")
else:
    response.raise_for_status()