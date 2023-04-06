# -*- coding: utf-8 -*-
"""
Created on Wed Apr  5 08:39:28 2023

@author: Dan
"""


from pathlib import Path
from shutil import copytree, copy
from time import sleep
from datetime import datetime
from collections import defaultdict
from os.path import getmtime
from itertools import chain

def synchronization():
    'Periodically synchronize the contents of one folder to a newly created one.'
    # Accepting and verifying user inputs
    while True:
        source_path = Path(input('Please input the path for the source folder:\n'))
        if source_path.is_dir() is False:
            print('Please enter a valid path to an existing folder.\n'
                  f'You entered "{str(source_path)}".')
        else:
            source_path = source_path.absolute()
            break
    while True:
        try:
            replica_path = Path(input('Please input the path for the replica folder:\n'))
            replica_path.mkdir(exist_ok=True)
            replica_path = replica_path.absolute()
            break
        except OSError:
            print('Please provide a valid replica path.\n'
                  f'You entered "{str(replica_path)}".')
    while True:
        log_path = Path(input('Please input the path for the log file:\n'))
        try:
            log_path.touch(exist_ok=True)
            log_path.unlink(missing_ok=True)
            log_path = log_path.absolute()
            break
        except OSError:
            print('Please provide a valid path for the log file.'
                  f'You entered "{str(log_path)}".')
    while True:
        synch_interval_input = input('Please input the synchronization interval in seconds:\n')
        try:
            synch_interval = int(synch_interval_input)
            break
        except ValueError:
            print(f'Please provide the synchronization interval in seconds as an integer.\n'
                  f'You entered "{synch_interval_input}".')

    # Doing the actual synchronization and logging 
    # (NOTE: the "else" part could be replaced with a simple copytree command, but 
    # the long solution might be preferable if data transfer is the limiting factor)
    while True:
        source_dict = create_path_dict(source_path)
        replica_dict = create_path_dict(replica_path)
        source_folders, replica_folders = [[x for x in y.rglob('*') if x.is_dir() is True] 
                                           for y in (source_path, replica_path)]
        if len(list(replica_path.rglob('*'))) == 0:
            copytree(source_path, replica_path, dirs_exist_ok=True)
            number_copied = len(source_dict.values())
            num_outdated_folders, num_outdated_val = 0, 0

        else:
            number_copied = 0
            already_copied = []
            for folder, files in source_dict.items():
                # Check if the folder was included in a previous copy 
                if len([x for x in already_copied if x in folder]) > 0:
                    continue
                # If the folder does not exist yet, just copy the whole folder 
                if (new_path := convert_path(folder, source_path, replica_path)).is_dir() is False:
                    copytree(Path(folder), Path(new_path))
                    subfolders = [str(x) for x in Path(folder).rglob('*') if x.is_dir() is True]  
                    already_copied.extend(subfolders)
                    number_copied += len(files)
                # Does the file exist in the replica folder and if so, is the source file newer
                else:
                    for file in files:
                        new_file = convert_path(file, source_path, replica_path)
                        if new_file.exists() is True and getmtime(file) <= getmtime(new_file):
                            continue
                        else:
                            copy(file, new_file)
                            number_copied += 1
                            
            # making sure that there are no outdated files and folders in replica 
            converted_source_folders = [str(convert_path(x, source_path, replica_path)) for 
                                    x in source_folders]
            outdated_folders = [x for x in replica_folders if
                                str(x) not in converted_source_folders]
            try:
                if (num_outdated_folders := len(outdated_folders)) > 0:
                    for folder in outdated_folders:
                        Path(folder).unlink()
                converted_source_val = [str(convert_path(x, source_path, replica_path)) for 
                                        x in list(chain(*source_dict.values()))]
                outdated_val = [x for x in list(chain(*replica_dict.values())) if 
                                str(x) not in converted_source_val]
                if (num_outdated_val := len(outdated_val)) > 0:
                    for val in outdated_val:
                        val.unlink()
            except PermissionError:
                print('A problem has occured: Please make sure that permission' 
                      ' is granted to remove outdated files and folders.')
                break
            
        log_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        num_copied_folders = len(source_folders) + num_outdated_folders - len(replica_folders)
        msg = (f'At {log_time}, {num_copied_folders} folder(s) and {number_copied}'
               f' file(s) were copied from {source_path.absolute()}'
               f' to {replica_path.absolute()}. {num_outdated_folders} folder(s) and'
               f' {num_outdated_val} file(s) were deleted from {replica_path.absolute()}.\n')
        with open(log_path, 'a') as f:
            f.write(msg)
        print(msg)
        sleep(synch_interval)

def create_path_dict(path):
    'Assigns the paths of the content of each folder to the str(path) of that folder'
    all_files = [x for x in path.rglob('*') if x.is_dir() is False]
    path_dict = defaultdict(list)
    for f in all_files:
        path_dict[str(f.parent)].append(f)
    return path_dict

def convert_path(path_to_convert, source_path, replica_path):    
    'Converts the source path to the corresponding replica path.'
    return Path(str(path_to_convert).replace(str(source_path), str(replica_path)))

if __name__ == '__main__':
    synchronization()

