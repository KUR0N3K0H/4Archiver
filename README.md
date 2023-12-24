4Archiver is a python script that will let you save 4chan threads.  
This will save the posts in the thread as well as any uploaded images.
To install run

pip3 install -r requirements.txt

To run this script simply run it like any other python program:

Python3 4Archiver.py

Your list of threads is saved to a text file called “threads.txt”.  
If the script does not detect this file in the present working directory at 
startup it will create an empty file.  
The script will remove any threads that have been archived or 404ed. 

The script will create a folder for each board in your present working 
directory, from there each thread will also have its on sub-folder.   

Every 60 seconds the script will iterate through the list of threads in 
threads.txt.  The script will continue to run until it is interrupted by
the user
  
