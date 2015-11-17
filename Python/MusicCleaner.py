import os
import sys

######################################################################################
# Written by Ryan D'souza
# #
# # A simple script I wrote to clear out duplicate songs in my roommate's iTunes
# # library --> Goes right to where the music is stored and deletes it
# #
# ######################################################################################


#Determines whether a file is a duplicate --> Follows iTunes renaming style
def fileIsDuplicate(fileName):
    lastChar = fileName[-1];

    return lastChar == '1' or lastChar == '2' or lastChar == '3' or lastChar == '4';

path = os.getcwd()
totalDeletions = 0;

for subdir, dirs, files in os.walk(path):

    #Holds the file names in each directory
    songs = {}

    #Add all the files in the directory to the set
    for file in files:

        pathToFile = os.path.join(subdir, file);
        fileNameWOExtension = os.path.splitext(os.path.basename(pathToFile))[0]

        #Add the file to the set
        songs[fileNameWOExtension] = pathToFile;

    #Go through all the files
    for file in files:

        pathToFile = os.path.join(subdir, file);
        fileNameWOExtension = os.path.splitext(os.path.basename(pathToFile))[0]

        #If the file could be a duplicate
        if fileIsDuplicate(fileNameWOExtension):

            #Original file name, ignores space in "fileName 1"
            originalFileName = fileNameWOExtension[-2]; 

            #If we have the original file, delete it
            if originalFileName in songs:
                try:
                    os.remove(pathToFile)
                    totalDeletions += 1
                    print("DELETED: " + fileNameWOExtension + "\t\tFROM: " + pathToFile)
                except:
                    print("ERROR DELETING: " + fileNameWOExtension + "\t\tFROM : " + pathToFile)

print("Finished. Total deletions: " + str(totalDeletions))
