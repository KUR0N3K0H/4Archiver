4Archiver is a python script that will let you save 4chan threads.  This will save the posts in the thread as well as any uploaded images.
This script was written in Python 3.8 on Ubuntu 20.04,  I tried to make the script as system agnostic but I cannot guarantee it will work on other operating systems.

4Archiver relies on a few non-standard libraries you can install with pip3.  To run this script you will need to install:
 
PySimpleGUI

pywebcopy

httpx

The other libraries I use should come with the standard Python library.

To run this script simply run it like any other python program:

Python3 4Archiver.py

Your list of threads is saved to a text file called “threads.txt”.  If the script does not detect this file in the present working directory at startup it will create an empty file.  The script will remove any threads that have been archived or 404ed. 

The script will create a folder for each board in your present working directory, from there each thread will also have its on sub-folder.   

Every 60 seconds the script will iterate through the list of threads in threads.txt.

If you want to disable the progress bar that pops up comment out line 93.   
