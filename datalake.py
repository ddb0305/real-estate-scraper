import os
import azure_key

from azure.storage.filedatalake import DataLakeServiceClient


def initialize_storage_account(storage_account_name, storage_account_key):
    service_client = DataLakeServiceClient(account_url="{}://{}.dfs.core.windows.net".format(
        "https", storage_account_name), credential=storage_account_key)
    return service_client

def create_file_system_client_service_if_not_exist(service_client, fs_name):
    fs_names = {fs.name for fs in service_client.list_file_systems()}
    if fs_name in fs_names:
        file_system_client = service_client.get_file_system_client(fs_name)
    else:
        file_system_client = service_client.create_file_system(fs_name)
    return file_system_client

def upload_file_to_directory(directory_client, file_path):
    file_name = file_path.split("/")[-1]
    file_client = directory_client.create_file(file_name)
    
    local_file = open(file_path, "r")
    file_contents = local_file.read()
    file_client.append_data(data=file_contents, offset=0, length=len(file_contents))
    file_client.flush_data(len(file_contents))

def upload_directory_to_file_system(file_system_client, dir_path):
    dir_type = dir_path.split("/")[-2]
    dir_name = dir_path.split("/")[-1]

    directory_client = file_system_client.create_directory(dir_type + "/" + dir_name)
    
    file_names = os.listdir(dir_path)
    for file_name in file_names:
        upload_file_to_directory(directory_client, dir_path + "/" + file_name)

if __name__ == "__main__":
    fs_name = "bds-raw-datas"
    
    service_client = initialize_storage_account(azure_key.storage_account_name, azure_key.storage_account_key)
    file_system_client = create_file_system_client_service_if_not_exist(service_client, fs_name)

    dir_types = os.listdir(os.getcwd() + "/" + fs_name)


    for dir_type in dir_types:
        chunks = os.listdir(os.getcwd() + "/" + fs_name + "/" + dir_type)
        for chunk in chunks:
            if not file_system_client.get_directory_client(dir_type + "/" + chunk).exists():
                print("Uploading", dir_type + "/" + chunk)
                upload_directory_to_file_system(file_system_client, os.getcwd() + "/" + fs_name + "/" + dir_type + "/" + chunk)

    