import os;


#Written by Ryan Dsouza
#Quickly renames all the photos in a directory with the format
#'Screenshot_X.png', where X is that file's place in the directory

#Also prints out the markdown code to display these many images

#Run instructions: 'python ImageRenamer.py'
#Make sure to update prefix with the correct repo name


files = os.listdir('.');
index = 0;

prefix = "https://github.com/dsouzarc/bmfiOS/blob/master/Screenshots/";

for fileName in files:

    if fileName != "ImageRenamer.py":
        newFileName = "Screenshot_" + str(index) + ".png";
        os.rename(fileName, newFileName);
        print("![Screenshot " + str(index) + "](" + prefix + newFileName + ")");
        index += 1;
