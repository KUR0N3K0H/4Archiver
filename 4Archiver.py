"""
This program will download all pictures and webms from specified 4chan 
threads along with any user comments.  The script leverages the 4chan API 
to to accomplish this.  The script will continue to scrape new replies and 
images from a thread until the thread 404s.
"""
import os
import time

import json
import httpx
import PySimpleGUI as sg
import requests
from pywebcopy import save_webpage


class ControlGUI:
    """
    This is the GUI the user will see when they start the application.  
    The user will be presented with three options:

    1) Rip existing – The script will begin to download any existing threads 
    listed in threads.txt
    2) Add new – This will allow the user to add new threads to threads.txt.  
    3) Show current threads – This will allow the user to look at the contents 
    of threads.txt

    Threads.txt is a text file that contains a list of 4chan threads the 
    user is trying to download. Additionally if threads.txt does not 
    exist the script will create it for the user
    """
    def __init__(self):
        """
        Creating attributes for the class.
        """
        self.thread=None
        self.image_url_list=None
        self.complete_folder_path=None

    def read_threads(self):
        """
        This function is going to open the threads.txt file where any previous 
        threads the user was downloading are saved.  If threads.txt does 
        not exist the function will create a blank threads.txt file in the 
        present working directory.
        """
        try:
            with open('threads.txt', encoding="us-ascii") as f:
                thread_list = f.read().splitlines()
        except FileNotFoundError:
            with open('threads.txt', encoding="us-ascii", mode='a'):
                pass
            with open('threads.txt', encoding="us-ascii") as f:
                thread_list = f.read().splitlines()
        return thread_list

    def create_gui(self,thread_list):
        """
        This function will present the user with three options they can pick:

        1) Rip existing- The script will begin to download any existing threads
        listed in threads.txt
        2) Add new – This will allow the user to add new threads to threads.txt  
        3) Show current threads – This will allow the user to look at the 
        contents of threads.txt
        """
        layout=[[sg.T("Rip existing threads or add new ones?")],
        [sg.Button("Rip existing")],[sg.Button("Add new")],
        [sg.Button("Show current threads")]]
        window = sg.Window('Mongolian Basket Weaving Thread Archiver', layout,
        enable_close_attempted_event=True,
        default_element_size=(50, 10))

        while True:
            event, unused_value = window.read()
            if event =="Rip existing":
                rip_threads=GUIRipThread(thread_list)
                rip_threads.save_thread()
            elif event == "Add new":
                new_threads=GUIGetThread()
                append_list=new_threads.get_user_input()
                with open('threads.txt', 'a' , encoding="us-ascii") as f:
                    f.write(f"{append_list}\n")
                with open('threads.txt' , encoding="us-ascii") as f:
                    thread_list = f.read().splitlines()
            elif event =="Show current threads":
                with open('threads.txt', encoding="us-ascii") as f:
                    thread_list = f.read().splitlines()
                existing_threads=GUIShowThread(thread_list)
                existing_threads.get_list()
            elif event ==sg.WINDOW_CLOSE_ATTEMPTED_EVENT and \
                sg.popup_yes_no('Do you really want to exit?') == 'Yes':
                break
        window.close()

class GUIRipThread:
    """"
    This class will look through the threads listed in threads.txt and it will
    obtain a list of images from each thread.  It will download every image
    found inside a thread and it will also check to see if each thread
    in the threads.txt file is archived or not.
    If the thread is archived then it is removed from threads.txt
    """
    def __init__(self,thread_list):
        """
        The class expects the a list of threads to iterate
        through.  The tread list is provided in the ControlGUI class.
        In addition the object will have a counter associated with it.
        The counter is only used for the creation of a list that will be 
        modified by the script
        """
        self.thread_list=thread_list
        self.iteration_counter=0
        self.thread=None
        self.json_formatted=None
        self.image_url_list=None
        self.complete_folder_path=None
    def save_thread(self):
        """"
        This function creates the GUI window that will allow the user to
        iterate through the list of threads we want to save.
        Most of the code in this function is in a while loop.  This ensures
        the script will re-run constantly until it is interupted by the user.
        This allows the script to constantly save new posts and images from
        the threads we are scraping. 
        """
        layout=[
        [sg.Button("Start rip")], [sg.Button("Main Menu")],
            [sg.T(key="-OUTPUT_TEXT-")],
            [sg.T("Any archived or 404ed threads will be deleted from your" +
            " saved file")]]
        window = sg.Window("Unofficial Mongolian Basket Weaving Thread" +
        ' Archiver', layout, enable_close_attempted_event=True,
        default_element_size=())
        while True:
            event, values = window.read(timeout=60000)
            if self.iteration_counter==0:
                self.iteration_counter+=1
                new_loop_thread_list=[]

                for item in self.thread_list:
                    if item not in new_loop_thread_list:
                        new_loop_thread_list.append(item)

            if new_loop_thread_list!=self.thread_list:
                self.thread_list.clear()
                for item in new_loop_thread_list:
                    self.thread_list.append(item)

            if event in ("Start rip", sg.TIMEOUT_KEY):
                for thread in self.thread_list:
                    try:
                        time.sleep(2)
                        self.thread=thread.strip()
                        self.convert_to_json()
                        is_archived,complete_folder_path=self.api_call()
                        """
                        Index_value will be one of three values, 0 means the 
                        thread is active, 1 means the thread
                        is archived, and 2 means the thread is 404ed.  The
                        index value is obtained from the api_call function.
                        Index value 3 is custom and it is used to force a 
                        re-try.
                        """
                        if is_archived==2:
                            try:
                                new_loop_thread_list.remove(thread)
                            except ValueError:
                                pass
                        elif is_archived==1:
                            window.perform_long_operation (lambda: self.post_ripper(thread,complete_folder_path), '-FUNCTION COMPLETED-')
                            try:
                                new_loop_thread_list.remove(thread)
                            except ValueError:
                                pass
                        elif is_archived==0:
                            window.perform_long_operation (lambda: self.post_ripper(thread,complete_folder_path),'-FUNCTION COMPLETED-')
                        elif is_archived==3:
                            pass
                    except AttributeError:
                        new_loop_thread_list.remove(thread)
                window["-OUTPUT_TEXT-"].update("Rip complete!"+
                "The script will re-start in 60 seconds.")
            elif event =="Main Menu" or event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
                with open('threads.txt', 'w', encoding="us-ascii") as f:
                    for thread in new_loop_thread_list:
                        f.write(f"{thread}\n")
                break
        window.close(); del window

    def convert_to_json(self):
        """
        The purpose of this function is to convert the URLs from the threads
        list into a json format that can be interperted by 4chan's API
        """
        self.json_formatted=self.thread.replace("boards.4channel.org",
        "a.4cdn.org")
        self.json_formatted=self.json_formatted.replace("boards.4chan.org",
        "a.4cdn.org")
        self.json_formatted=self.json_formatted.replace("[","")
        self.json_formatted=self.json_formatted.replace("]","")
        self.json_formatted=self.json_formatted.replace("'","")
        self.json_formatted=self.json_formatted+".json"


    def api_call(self):
        """
        This function will download all images from a thread through the API. 
        It will also see if the thread is archived or 404ed.
        """
        is_archived=0
        self.image_url_list=[]
        board_name=self.json_formatted.split("/")
        complete_folder_path=""
        try:
            api_response=httpx.get(self.json_formatted)
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

        """"
        These lines of code will check to see if the thread is 404ed,
        if it is then it will immediately
        exit the function
        """

        if api_response.status_code == 404:
            is_archived=2
            return is_archived, complete_folder_path
        api_json=json.loads(api_response.text)
        if "archived" in api_json["posts"][0]:
            is_archived=1
        index_value=0

        for item in api_json['posts']:
            """
            In this loop we are going to go through each thread and scrape a 
            list of images that are in the thread.  We will add each image to 
            a list and we will download it later
            """
            if "tim" in item:
                filename=str(api_json['posts'][index_value]['tim'])
                extension=api_json['posts'][index_value]['ext']
                completed_image_url="https://i.4cdn.org/"+board_name[3]+"/"+filename+extension
                self.image_url_list.append(completed_image_url)
                index_value+=1
            else:
                index_value+=1
        for picture in self.image_url_list:
            complete_folder_path=(os.path.join(board_name[3],
            board_name[5].replace(".json", "")))
            image_name=picture.split("/")[-1]
            complete_image_name=os.path.join(complete_folder_path,image_name)
            if not os.path.exists(complete_folder_path):
                os.makedirs(complete_folder_path)
            if os.path.isfile(complete_image_name) == True:
                pass
            else:
                write_image = open(complete_image_name, 'wb')
                write_image.write(requests.get(picture).content)
                write_image.close()
        return is_archived, complete_folder_path

    def post_ripper(self,thread,complete_folder_path):
        """
        This function will use the save_webpage library to download the
        posts in the thread.  The posts will be saved as a single html file.
        """
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
    """"
    The purpose of this class is to prompt the user for a list of threads they
    would like to download.  
    """
    def __init__(self):
        """
        This is a blank initialization function
        """


    def get_user_input(self):
        """
        The first part of this function is to create a GUI that asks the user 
        to enter all of their threads. After I get the list of threads from the 
        user they will be in a dictionary,  I cannot really
        do anything with the dictioanry so I have to convert it into a list 
        by stripping off extreanous characters.  One I have the list I 
        return it.
        """
        layout =[[sg.T('Please enter your list of threads,'+
                ' each thread should be seperated by a new line')],
                [sg.Multiline((''), key='-THREAD-LIST-')],
                [sg.Button('Read')]
                ]
        window = sg.Window('Unofficial Mongolian Basket Weaving' +
        ' Thread Archiver', layout, 
                           enable_close_attempted_event=True,
                           default_element_size=(50, 10))

        event, list_of_threads = window.read()
        window.close()
        return list_of_threads.get('-THREAD-LIST-')


class GUIShowThread:

    """
    This class will display a list of threads that are in the threads.txt
    file.
    """
    def __init__(self,thread_list):

        self.thread_list=thread_list

    def get_list(self):
        for item in self.thread_list:
            sg.Print(item)

def main():
    main_program=ControlGUI()
    thread_list = main_program.read_threads()
    create_gui = main_program.create_gui(thread_list)

if __name__ == "__main__":
    main()
