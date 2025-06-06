"""ETL Extract Stage:
Connects to an AWS S3 bucket, downloads relevant PubMed XML files based on a prefix and file extension,
and saves them locally to the raw_data/ directory for further processing.
"""
import os
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
    """Downloads relevant files from S3 to raw_data folder."""

    bucket = s3.list_objects(Bucket=bucket_name)
    contents = bucket.get("Contents", [])
    files_needed = []

    for file in contents:
        data = file["Key"]
        if data.startswith(file_prefix) and data.endswith(file_extension):
            files_needed.append(data)

    if files_needed:
        for file in files_needed:
            local_path = os.path.join("../raw_data", os.path.basename(file))
            s3.download_file(bucket_name, file, local_path)
            print(f"{file} downloaded successfully to {local_path}")
    else:
        print("No data was uploaded")


def main_extract():
    """Connects to bucket and download relevant files"""

    bucket = "sigma-pharmazer-input"

    client = connect_to_s3()

    # upload_initial_xml(client, bucket, "../raw_data/c14-gem-lo-pubmed.xml")

    download_pubmed_data_files(
        client, bucket, "c14-gem-lo", ".xml")


if __name__ == "__main__":

    load_dotenv()

    main_extract()
