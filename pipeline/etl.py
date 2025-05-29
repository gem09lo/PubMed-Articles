"""Complete ETL pipeline"""
import boto3
from dotenv import load_dotenv
from extract import main_extract
from transform import main_transform
from load import main_load
from os import environ as ENV


def verify_email_identity(email):
    """Verify an email identity with SES"""
    ses_client = boto3.client(
        "ses", region_name="eu-west-2")  # Adjust region if needed
    response = ses_client.verify_email_identity(EmailAddress=email)
    print(f"Verification response: {response}")


def send_plain_email(subject, body, sender, recipient):
    """Send a plain-text email using SES"""
    ses_client = boto3.client(
        "ses", region_name="eu-west-2")  # Adjust region if needed
    CHARSET = "UTF-8"

    try:
        response = ses_client.send_email(
            Source=sender,
            Destination={
                "ToAddresses": [recipient],
            },
            Message={
                "Subject": {
                    "Charset": CHARSET,
                    "Data": subject,
                },
                "Body": {
                    "Text": {
                        "Charset": CHARSET,
                        "Data": body,
                    }
                },
            },
        )
        print(f"Email sent! Response: {response}")
    except Exception as e:
        print(f"Error sending email: {e}")


def run_etl_pipeline():
    """Downloads, cleans, processes the data, and uploads it to the S3 output bucket"""
    load_dotenv()

    sender_email = ENV["SENDER_EMAIL"]
    recipient_email = ENV["RECIPIENT_EMAIL"]

    # Initial step: Verify the email identity by uncommenting line below:
    # verify_email_identity(sender_email)

    try:
        # Notify that the task has started
        send_plain_email(
            subject="ETL Pipeline Started",
            body="The ETL pipeline has started running.",
            sender=sender_email,
            recipient=recipient_email,
        )

        # Run the ETL steps
        main_extract()
        main_transform()
        main_load()

        # Notify that the task has completed
        send_plain_email(
            subject="ETL Pipeline Completed",
            body="The ETL pipeline has successfully completed.",
            sender=sender_email,
            recipient=recipient_email,
        )
    except Exception as e:
        send_plain_email(
            subject="ETL Pipeline Failed",
            body=f"The ETL pipeline failed with the following error:\n\n{e}",
            sender=sender_email,
            recipient=recipient_email,
        )
        print(f"Pipeline failed: {e}")


if __name__ == "__main__":
    run_etl_pipeline()
