# Terraform Setup

## ☁️ Overview – Infrastructure for Automating the PubMed ETL Pipeline

This folder contains Terraform scripts to deploy and automate the ETL pipeline on AWS.

Once deployed, this infrastructure enables:

- ✅ Running the ETL pipeline in an AWS Fargate container (ECS)
- ✅ Automatically triggering the pipeline when a new XML file is uploaded to an S3 input bucket
- ✅ Sending email notifications (via AWS SES) when the pipeline starts, completes, or fails

---

## 🛠️ Getting Setup

### 1. Ensure AWS credentials are available

Create a `.env` file in your project root with the following:
- ACCESS_KEY_ID=<your_access_key>
- SECRET_ACCESS_KEY=<your_secret_key>
- SENDER_EMAIL=<verified_ses_sender_email>
- RECIPIENT_EMAIL=<notification_recipient_email>
- VPC_ID=<your_existing_vpc_id>

Note: `SENDER_EMAIL` must be verified in the AWS SES console.

### 2. Initialize and apply Terraform
- `cd terraform`
- `terraform init`
- `terraform apply`


### 🗂️ Files Explained

- `main.tf`: Main infrastructure: ECS task, ECR repo, EventBridge rule, IAM roles, security group
- `variables.tf`: Declares input variables (e.g. AWS credentials, VPC ID)
`terraform.tfvars`:	Stores your actual AWS credentials and other inputs (ignored by Git)
`README.md`: You're reading it! Contains setup instructions and architecture overview


### 🏗️ Infrastructure Architecture

- `ECS Fargate Task`: Runs the ETL Docker container on demand
- `ECR Repository`: Stores your container image
- `CloudWatch Event Rule`: Automatically triggers ECS task when a new file is uploaded to S3
- `IAM Roles & Policies`: Grants ECS and EventBridge the correct permissions
- `Security Group`: Allows outbound and necessary inbound access for ECS task
- `SES`: Sends email alerts when the pipeline runs or fails

### 📦 Expected S3 Buckets

- `sigma-pharmazer-input`: Receives raw XML files (triggers pipeline)
- `sigma-pharmazer-output`: Stores processed CSV files


### ✅ Notes
- This setup assumes the ECS cluster (c14-ecs-cluster) already exists.
- Email alerts will only work if both sender and recipient addresses are verified in SES (in sandbox mode).
- Be sure your VPC and subnet IDs are correct for ECS Fargate execution.

### 💡 Example Workflow

1. Push your ETL Docker image to the ECR repository.
2. Upload c14-gem-lo-pubmed.xml to the sigma-pharmazer-input bucket.
3. EventBridge rule triggers ECS task to run your ETL.
4. Output CSV is saved to sigma-pharmazer-output.
5. Email notifications are sent to the specified recipients.