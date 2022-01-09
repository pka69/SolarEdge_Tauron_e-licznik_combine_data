import os


STORAGE_DIR = 'imported/'
OUTPUT_DIR = 'output/'

global debug
debug = True

def set_debug(new_debug_value):
    global debug
    debug = new_debug_value
    return debug

def switch_debug():
    global debug
    return debug

def get_debug():
    global debug
    return debug

def check_folder_structure(folder_list):
    my_folder_list = [f for f in os.listdir()
            if not os.path.isfile(os.path.join(f))]
    for directory in folder_list:
        if (directory[:-1] if directory[-1] in ['\\', '/'] else directory) not in my_folder_list:
            os.mkdir(directory[:-1] if directory[-1] in ['\\', '/'] else directory)


# check folder structure (and eventually create folders)
check_folder_structure([globals()[i] for i in dir() if i.lower().endswith('_dir')])