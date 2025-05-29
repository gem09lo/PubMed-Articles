"""Trigger script to manually upload a sample PubMed XML file to the input S3 bucket.

This was used during early testing to populate the bucket with an initial file. 
It is not used in the final automated ETL pipeline, but can be kept for manual data upload tasks.
"""
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

    print(f"{output_file} uploaded to {bucket_name} successfully")


def main_extract():
    """Connects to bucket and download relevant files"""

    bucket = "sigma-pharmazer-input"

    client = connect_to_s3()

    upload_initial_xml(client, bucket, "../raw_data/pubmed_result_start.xml")


if __name__ == "__main__":

    load_dotenv()

    main_extract()
