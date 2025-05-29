"""Uploads the processed data (csv file) to an s3 bucket."""
from os import environ
from boto3 import client
from dotenv import load_dotenv


def connect_to_s3():
    """Connects to S3 using credentials from .env file"""

    s3 = client("s3", aws_access_key_id=environ["ACCESS_KEY_ID"],
                aws_secret_access_key=environ["SECRET_ACCESS_KEY"])
    return s3


def upload_csv_file(s3, bucket_name, file_name):
    """Upload the processed csv file to s3 output bucket."""
    output_file = "c14-gem-lo-processed-pubmed.csv"
    s3.upload_file(file_name, bucket_name, output_file)

    print(f"{file_name} uploaded successfully as {output_file}")


def download_csv_file(s3, bucket_name, file_prefix, file_extension):
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


def main_load():
    """Connects to bucket and download relevant files"""

    bucket = "sigma-pharmazer-output"

    client = connect_to_s3()

    # Full dataset use "../cleaned_data/pubmed_output2.csv"
    upload_csv_file(client, bucket, "../cleaned_data/pubmed_output.csv")

    # download_csv_file(client, bucket, "c14-gem", ".csv")


if __name__ == "__main__":

    load_dotenv()

    main_load()
