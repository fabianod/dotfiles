#!/usr/bin/python

from PIL import Image;
import os;
import sys;
import shutil;

#Original image
global originalImage;

#Path to save to: path program run from + directory 'AppIcon'
global saveToPath;

#Resizes the image and saves it
#width/height are ints, imageDescription is string describing new image
def resizeImage(newWidth, newHeight, imageDescription):
    newImage = originalImage.resize((newWidth, newHeight), Image.ANTIALIAS);
    
    newFileName = saveToPath + "/Icon-" + imageDescription + ".png";
    newImage.save(newFileName, quality=100);

#If the image name/directory is not inputted, prompt user for it
if len(sys.argv) == 1:
    fileName = raw_input("Enter file name and directory:\n");

#If image name/directory is inputted as command parameter
else:
    fileName = sys.argv[1];

#Open the original image
originalImage = Image.open(fileName);

#Path to save files to (see 'saveToPath' declaration
pathWhenExecuting = os.getcwd();
saveToPath = pathWhenExecuting + "/AppIcon";

#If the 'AppIcon' directory exists, delete it
if os.path.exists(saveToPath):
    shutil.rmtree(saveToPath);

#And remake it
os.makedirs(saveToPath);

#Creates a copy of the original image, resizes to those dimensions, saves it to disk
resizeImage(1024, 1024, "1024");
resizeImage(512, 512, "512");
resizeImage(256, 256, "256");
resizeImage(128, 128, "128");
resizeImage(64, 64, "64");
resizeImage(32, 32, "32");
resizeImage(16, 16, "16");
