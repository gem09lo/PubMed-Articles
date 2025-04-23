"""Extracts and downloads Pubmed XML files from S3 bucket"""
from os import environ
from boto3 import client
from dotenv import load_dotenv


def connect_to_s3():
    """Connects to S3 using credentials from .env file"""

    s3 = client("s3", aws_access_key_id=environ["ACCESS_KEY_ID"],
                aws_secret_access_key=environ["SECRET_ACCESS_KEY"])
    return s3


def upload_initial_xml(s3, bucket_name, file_name):
    """Upload initial Pubmed XML file to s3 input bucket."""
    output_file = "c14-gem-lo-pubmed.xml"
    s3.upload_file(file_name, bucket_name, output_file)

    print(f"{output_file} uploaded successfully")


def download_pubmed_data_files(s3, bucket_name, file_prefix, file_extension):
    """Downloads relevant files from S3 to a data/folder."""

    bucket = s3.list_objects(Bucket=bucket_name)

    contents = bucket.get("Contents", [])
    files_needed = []

    for file in contents:
        data = file["Key"]
        if data.startswith(file_prefix) and data.endswith(file_extension):
            files_needed.append(data)

    if files_needed:
        for file in files_needed:
            s3.download_file(bucket_name,
                             file, file)
            print(f"{file} downloaded successfully")
    else:
        print("No data was uploaded")


def main_extract():
    """Connects to bucket and download relevant files"""

    bucket = "sigma-pharmazer-input"

    client = connect_to_s3()

    # upload_initial_xml(client, bucket, "challenge-1/pubmed_result_start.xml")

    download_pubmed_data_files(
        client, bucket, "c14-gem-lo", ".xml")


if __name__ == "__main__":

    load_dotenv()

    main_extract()
