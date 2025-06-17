"""Utility - Assorted General GCS Related."""

import os

from google.api_core.exceptions import NotFound
from google.cloud import storage


def list_files_in_gcs_bucket(bucket_name, project_id):
    """Lists all the blobs in the bucket."""
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs()  # Get all blobs
    return [blob.name for blob in blobs]  # Extract filenames


def list_files_in_gcs_bucket_folder(bucket_name, folder, project_id):
    """Lists all the files within a specified folder in the bucket."""
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)

    # Use the prefix parameter to filter blobs within the folder
    blobs = bucket.list_blobs(prefix=folder)

    return [blob.name for blob in blobs]


def download_to_local_folder_from_gcs_bucket(
    bucket_name, file_name, local_folder_path, project_id
):
    """Downloads a blob from GCS and saves it locally"""
    storage_client = storage.Client(project=project_id)

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    try:
        # Check if blob exists before downloading
        if blob.exists():
            # Create destination directory if it doesn't exist
            # Extract the GCS folder structure from the file name
            gcs_folder_path = os.path.dirname(file_name)

            # Combine the local folder path with the GCS folder structure
            full_local_path = os.path.join(local_folder_path, gcs_folder_path)

            # Create the full local directory structure if it doesn't exist
            os.makedirs(full_local_path, exist_ok=True)

            dst_file_path = os.path.join(full_local_path, os.path.basename(file_name))

            blob.download_to_filename(dst_file_path)
            print(f"Downloaded {file_name} to {full_local_path}")
        else:
            print(f"Blob {file_name} does not exist in bucket {bucket_name}")
    except Exception as e:
        print(f"An error occurred: {e}")


def download_to_local_folder_from_gcs_folder(
    bucket_name, file_name, local_folder_path, project_id
):
    """Downloads a blob from GCS and saves it locally"""
    storage_client = storage.Client(project=project_id)

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    try:
        # Check if blob exists before downloading
        if blob.exists():
            # Create destination directory if it doesn't exist
            destination_directory = os.path.dirname(local_folder_path)
            os.makedirs(destination_directory, exist_ok=True)

            dst_file_path = os.path.join(local_folder_path, os.path.basename(file_name))
            blob.download_to_filename(dst_file_path)
            print(f"Downloaded {file_name} to {local_folder_path}")
        else:
            print(f"Blob {file_name} does not exist in bucket {bucket_name}")
    except Exception as e:
        print(f"An error occurred: {e}")


def copy_file_to_gcs(
    localfilepath, gcs_bucket_name, gcs_folder, gcs_filename, project_id
):
    """Copies a local file to Google Cloud Storage."""

    try:
        # Check if the file exists
        if not os.path.exists(localfilepath):
            raise FileNotFoundError(f"File not found: {localfilepath}")

        # Upload to Google Cloud Storage
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(gcs_bucket_name)

        # Create the bucket if it doesn't exist
        if not bucket.exists():
            bucket = storage_client.create_bucket(gcs_bucket_name)

        blob_name = os.path.join(gcs_folder, gcs_filename)
        blob = bucket.blob(blob_name)

        # Upload the local file, overwriting if it exists
        blob.upload_from_filename(localfilepath)

        print(f"File {localfilepath} uploaded to gs://{gcs_bucket_name}/{blob_name}")

    except (
        FileNotFoundError,
        ValueError,
        Exception,
    ) as e:  # Use PyPDF2.utils.PdfReadError
        print(f"Error: {e}")


def delete_bucket_and_contents(bucket_name, project_id):
    """Deletes a GCS bucket and all its contents."""

    storage_client = storage.Client(project=project_id)

    try:
        # Get the bucket object
        bucket = storage_client.get_bucket(bucket_name)

        # Delete all blobs (objects) in the bucket
        blobs = bucket.list_blobs()
        for blob in blobs:
            blob.delete()
        print(f"Deleted all objects in bucket {bucket_name}")

        # Delete the bucket itself
        bucket.delete()
        print(f"Deleted bucket {bucket_name}")

    except NotFound:
        print(f"Bucket {bucket_name} not found, ignoring.")


def delete_bucket_contents(bucket_name, project_id):
    """Deletes all contents in GCS bucket."""

    storage_client = storage.Client(project=project_id)

    try:
        # Get the bucket object
        bucket = storage_client.get_bucket(bucket_name)

        # Delete all blobs (objects) in the bucket
        blobs = bucket.list_blobs()
        for blob in blobs:
            blob.delete()
        print(f"Deleted all objects in bucket {bucket_name}")

    except NotFound:
        print(f"Bucket {bucket_name} not found, ignoring.")


def create_bucket_if_not_exists(bucket_name, project_id, location):
    """Creates a GCS bucket if it doesn't already exist."""

    storage_client = storage.Client(project=project_id)

    try:
        bucket = storage_client.get_bucket(bucket_name)
        print(f"Bucket {bucket_name} already exists.")  # Bucket found
    except:  # Bucket not found, so create it
        bucket = storage_client.bucket(bucket_name)
        bucket.storage_class = "STANDARD"
        new_bucket = storage_client.create_bucket(bucket, location=location)
        print(f"Created bucket {new_bucket.name} in {new_bucket.location}.")
