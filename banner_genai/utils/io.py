"""Utility - Folder / File Mgmt. Functions."""

import os
import shutil


def list_files_in_folder(folder_path, folder_name=""):
    file_list = []
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            file_list.append(os.path.join(folder_name, item))
        elif os.path.isdir(item_path):
            file_list.extend(
                list_files_in_folder(item_path, os.path.join(folder_name, item))
            )
    return file_list


# def download_to_computer(folder_path, file_name):
#   file_path = os.path.join(folder_path, file_name)

#   if os.path.exists(file_path):  # Check if the file exists
#       files.download(file_path)  # Download to the local computer
#       print(f"Downloaded '{file_name}'")
#   else:
#       print(f"File not found: '{file_name}'")


def download_to_local_folder(src_folder_path, file_name, local_folder_path):
    src_file_path = os.path.join(src_folder_path, file_name)
    dst_file_path = os.path.join(local_folder_path, file_name)

    if os.path.exists(src_file_path):  # Check if the file exists
        # Copy the file from Google Drive
        shutil.copy(src_file_path, dst_file_path)
        print(f"Copied '{file_name}' to {dst_file_path}")
    else:
        print(f"File not found: '{file_name}'")


def copy_with_subfolders(src, dst):
    if not os.path.exists(dst):
        os.makedirs(dst)  # Create the destination directory if it doesn't exist

    for item in os.listdir(src):
        src_element = os.path.join(src, item)
        dst_element = os.path.join(dst, item)
        if os.path.isdir(src_element):
            shutil.copytree(src_element, dst_element)
        # Recursively copy subdirectories
        else:
            shutil.copy2(src_element, dst_element)  # Copy files


def delete_all_files(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)

                print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")


def get_filenames_in_folder(path):
    filenames = []
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isfile(item_path):
            filenames.append(item)
    return filenames


def get_filepath_in_folder_nested(path):
    filenames = []
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        # FIXME: Better way of filter only for image files.
        if os.path.isfile(item_path) and item_path.endswith(".png"):
            filenames.append(item_path)  # Append the full path
        elif os.path.isdir(item_path):
            filenames.extend(get_filepath_in_folder_nested(item_path))  # Recursive call
    return filenames


def find_files_with_prefix(directory, prefix):
    matching_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith(prefix):
                matching_files.append(os.path.join(root, file))
    return matching_files


def create_file_map(folder_path, extension, prefix):
    file_map = {}
    for filename in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, filename)):
            base_name, file_extension = os.path.splitext(filename)

            if (
                file_extension.lower() == extension.lower()
            ):  # Case-insensitive comparison
                absolute_path = os.path.abspath(os.path.join(folder_path, filename))
                file_map[base_name.removeprefix(prefix)] = absolute_path

    return file_map
