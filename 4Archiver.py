import json
import httpx
import PySimpleGUI as sg
import os
import requests
from pywebcopy import save_webpage
import time

class ControlGUI:
    def __init__(self):
        pass
    def main_gui(self):
        """I am opening threads.csv,  if it exists this will have any threads we were previously archiving.
        If not file exists we will create one for the user."""
        try:
            with open('threads.txt') as f:
            	thread_list = f.read().splitlines()
        except FileNotFoundError:
            with open('threads.txt', mode='a'): 
            	pass
            with open('threads.txt') as f:
            	thread_list = f.read().splitlines()

                    
        layout=[[sg.T("Rip existing threads or add new ones?")],
        [sg.Button("Rip existing")],[sg.Button("Add new")], [sg.Button("Show current threads")]]
        window = sg.Window('Unofficial Mongolian Basket Weaving Thread Archiver', layout, 
                               enable_close_attempted_event=True, default_element_size=(50, 10))
        while True:
            event, values = window.read()
            """If the user wants to add new threads to the list then this will create a new instance of the GUIGetThread
            class and will prompt the user for more threads.  After the user enters more threads it will be
            appended to the text file"""
            if event =="Rip existing":
                rip_threads=GUIRipThread(thread_list)
                rip_threads.save_thread()
            elif event == "Add new":
                new_threads=GUIGetThread()
                append_list=new_threads.get_user_input()
                """The next three lines are to strip out extrenaous characters before writing it to our
                text file"""
                with open('threads.txt', 'a') as f:
                    for thread in append_list:
                        f.write(f"{thread}\n")
                    
                with open('threads.txt') as f:
                    thread_list = f.read().splitlines()
            elif event =="Show current threads":
                with open('threads.txt') as f:
            	    thread_list = f.read().splitlines()
                existing_threads=GUIShowThread(thread_list)
                existing_threads.get_list()
            elif event ==sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Do you really want to exit?') == 'Yes':
                break

        window.close()
        
class GUIRipThread:
    def __init__(self,thread_list):
        self.thread_list=thread_list
        self.iteration_counter=0
    def save_thread(self):
        layout=[
        [sg.Button("Start rip")], [sg.Button("Main Menu")],
            [sg.T(key="-OUTPUT_TEXT-")],
            [sg.T("Any archived or 404ed threads will be deleted from your saved file")]]
        window = sg.Window('Unofficial Mongolian Basket Weaving Thread Archiver', layout, 
                               enable_close_attempted_event=True, default_element_size=())
        while True:
            event, values = window.read(timeout=60000)
            """The iteration counter is just here to prevent my list of threads from re-initializing
            every 60 seconds,  this if statement should only run the first time the user opens this window"""
            if self.iteration_counter==0:
                self.iteration_counter+=1
                new_loop_thread_list=[]
                for item in self.thread_list:                     
                    """I am also creating a second list,  if we have any threads that are archived or 404ed
                    we will remove them from this second list so it does not interrupt the operation of the script"""
                    if item not in new_loop_thread_list:
                        new_loop_thread_list.append(item)
                    """The following block of code will check to see if our two lists are the same,  if not it will
update the list that is read by the script"""

            if new_loop_thread_list!=self.thread_list:
                self.thread_list.clear()
                for item in new_loop_thread_list:
                    self.thread_list.append(item)

            if event =="Start rip" or event == sg.TIMEOUT_KEY:
                self.progress_counter=0
                for thread in self.thread_list:
                    try:
                        sg.OneLineProgressMeter("Progress", self.progress_counter+1, len(self.thread_list),  "", "Downloading, please wait")
                        time.sleep(2)
                        thread=thread.strip()
                        json_threads=self.convert_to_json(thread)                    
                        is_archived,complete_folder_path=self.api_call(json_threads)
                        """index_value will be one of three values, 0 means the thread is active, 1 means the thread
                        is archived, and 2 means the thread is 404ed"""
                        if is_archived==2:
                            try:
                                new_loop_thread_list.remove(thread)
                            except ValueError:
                                pass
                        elif is_archived==1:
                            window.perform_long_operation(lambda: self.post_ripper(thread,complete_folder_path),'-FUNCTION COMPLETED-')
                            try:
                                new_loop_thread_list.remove(thread)
                            except ValueError:
                                pass
                        elif is_archived==0:
                            window.perform_long_operation(lambda: self.post_ripper(thread,complete_folder_path),'-FUNCTION COMPLETED-')
                        elif is_archived==3:
                            pass
                        self.progress_counter+=1
                    except AttributeError:
                       new_loop_thread_list.remove(thread)
                window["-OUTPUT_TEXT-"].update("Rip complete! The script will re-start in 60 seconds.")
            elif event =="Main Menu" or event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
                with open('threads.txt', 'w') as f:
                    for thread in new_loop_thread_list:
                        f.write(f"{thread}\n")
                break
        window.close(); del window
    def convert_to_json(self,thread):
        self.thread=thread
        """The purpose of this function is to convert the URLs the user enters into a .json parameters that can 
        be requested with the API"""
        self.json_thread=[]
        self.thread=self.thread.replace("boards.4channel.org","a.4cdn.org")
        self.thread=self.thread.replace("boards.4chan.org","a.4cdn.org")
        self.thread=self.thread.replace("[","")
        self.thread=self.thread.replace("]","")
        self.thread=self.thread.replace("'","")
        self.thread=self.thread+".json"
        return self.thread
    
    def api_call(self,json_threads):
        """This function will download all images from a thread, it will also see if the thread is archived
        or 404ed"""
        is_archived=0
        self.json_threads=json_threads
        self.image_url_list=[]
        board_name=self.json_threads.split("/")
        complete_folder_path=""
        try:
            api_response=httpx.get(self.json_threads)
        except httpx.UnsupportedProtocol:
            is_archived=2
            return is_archived,complete_folder_path
        except httpx.ReadTimeout:
             is_archived=3
             time.sleep(10)
             return is_archived,complete_folder_path
        except httpx.ConnectError:
             is_archived=3
             time.sleep(10)
             return is_archived,complete_folder_path
        except httpx.ConnectTimeout:
             is_archived=3
             time.sleep(10)
             return is_archived,complete_folder_path
        
        """"These lines of code will check to see if the thread is 404ed,  if it is then it will immediately
        exit the function"""
        
        if api_response.status_code == 404:
            is_archived=2
            return is_archived, complete_folder_path
            
        api_json=json.loads(api_response.text)
        """The next two lines of code will check to see if the thread was archived"""
        if "archived" in api_json["posts"][0]:
            is_archived=1
            
        dirpath=os.makedirs(os.path.join(board_name[3], board_name[5].replace(".json", "")),exist_ok=True)
        index_value=0
        for item in api_json['posts']:
            """In this nested loop we are going to go through each thread and scrape a list of images that 
             are in the thread.  We will add each image to a list and we will download it later"""
            if "tim" in item:
                filename=str(api_json['posts'][index_value]['tim'])
                extension=api_json['posts'][index_value]['ext']
                completed_image_url="https://i.4cdn.org/"+board_name[3]+"/"+filename+extension
                self.image_url_list.append(completed_image_url)
                index_value+=1
            else:
                index_value+=1
        for picture in self.image_url_list:
            complete_folder_path=(os.path.join(board_name[3], board_name[5].replace(".json", "")))
            image_name=picture.split("/")[-1]
            complete_image_name=os.path.join(complete_folder_path,image_name)
            """This will check to see if the file already exists, if it does the file will be skipped"""
            if os.path.isfile(complete_image_name) == True:
                pass
            else:
                write_image = open(complete_image_name, 'wb')
                write_image.write(requests.get(picture).content)
                write_image.close()
        return is_archived, complete_folder_path
    
    def post_ripper(self,thread,complete_folder_path):
        self.thread=thread
        self.complete_folder_path=complete_folder_path
        thread_name=self.thread.split("/")[-1]
        save_webpage(
            url=self.thread,
            project_folder=self.complete_folder_path,
            project_name=thread_name,
            bypass_robots=True,
            debug=False,
            open_in_browser=False,
            delay=None,
            threaded=False,
            )
    
class GUIGetThread:
    def __init__(self):
        pass
     
    def get_user_input(self):
        """The first part of this function is to create a GUI that asks the user to enter all of their threads. """
        layout =[[sg.T('Please enter your list of threads, each thread should be seperated by a new line')],
                [sg.Multiline((''), key='-THREAD-LIST-')],
                [sg.Button('Read')]
                ]
        window = sg.Window('Unofficial Mongolian Basket Weaving Thread Archiver', layout, 
                           enable_close_attempted_event=True, default_element_size=(50, 10))
        event, values = window.read()

        """After I get the list of threads from the user they will be in a dictionary,  I cannot really
         do anything with the dictioanry so I have to convert it into a list by stripping off extreanous 
        characters.  One I have the list I return it"""

        list_of_threads=values.values()
        window.close()
        return list_of_threads


class GUIShowThread:
    def __init__(self,thread_list):
        self.thread_list=thread_list
    
    def get_list(self):
        for item in self.thread_list:
            sg.Print(item)
            
    
a=ControlGUI()        
a.main_gui()
