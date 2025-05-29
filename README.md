# PubMed Articles ETL Project (Machine Learning)

## 🧠 Overview

This project processes scientific publication data from PubMed in XML format, aiming to extract author metadata, match affiliation names to institutional GRID identifiers using NLP and fuzzy matching, and store the final structured data for analysis.

The goal was to automate and streamline the process of extracting, cleaning, and enriching article metadata, as well as to build deployable infrastructure that allows for scalable and maintainable data ingestion using AWS services.

This project was completed over one week and includes both local development capabilities and production deployment via AWS ECS and Terraform.

---


### 📌 Stakeholder

**Eve Chen (Director of Immunology)**

This project was developed for Eve, a health data scientist working in the research team at Pharmacer. Eve is responsible for analyzing research articles to extract information on authors, their institutions, and associated metadata to support research collaboration and pharmaceutical development. 

The goal of this pipeline is to automate what was previously a time-consuming manual task: matching institution names and extracting structured metadata from PubMed XML files, enabling more efficient and accurate data analysis for downstream work.

---


## 🎯 Project Aims

- Parse large-scale PubMed XML data and extract key metadata (e.g. article titles, authors, affiliations).
- Use NLP and fuzzy matching to identify author institutions and link them to GRID IDs.
- Generate clean CSV outputs suitable for further analysis and dashboarding.
- Automatically notify stakeholders of ETL pipeline status via AWS SES email.
- Deploy the pipeline as a scheduled or event-driven ECS task using Terraform.

---

### ⚙️ Technologies Used
**Tool / Service**
- `Python`	:ETL pipeline implementation
- `spaCy`	:Named Entity Recognition (NER)
- `RapidFuzz`	:String similarity matching
- `pandarallel`	:Multiprocessing support for large DataFrames
- `AWS S3`	:Input/output data storage
- `AWS ECS Fargate`	:Serverless task execution
- `AWS SES`	:Email notifications
- `Terraform`	:Infrastructure provisioning
- `Jupyter Notebooks`	:Development and data validation

---

## 📁 Project Structure

[pipeline]
- extract.py: Extracts data from raw XML and institutional files.
- transform.py: Cleans and processes extracted data.
- load.py: Loads cleaned data into target storage (e.g., CSV).
- etl.py: Orchestrates the full ETL process.
- trigger.py: Entry point for triggering ETL pipeline.
- dockerfile: Docker configuration for running the pipeline.

[raw_data]
- c14-gem-lo-pubmed.xml: Sampled XML dataset for testing.
- pubmed_result_sjogren.xml: Full XML dataset from PubMed.

Standardised Global Research Identifier database (GRID) datasets ('Source of Truth'):
- institutes.csv: Reference list of institutions from GRID.
- aliases.csv: (Optional) aliases from GRID data.
- addresses.csv: (Optional) institutional address data.

[cleaned_data]
- pubmed_output.csv: Cleaned sample output.
- pubmed_output2.csv: Cleaned full dataset.
- matched_sample.csv: Rows successfully matched to institutions.
- unmatched_sample.csv: Unmatched records for manual review.

[data_analysis]
- pubmed_result.ipynb: Jupyter notebook processing the full dataset.
- pubmed_test.ipynb: Debugging and test notebook for small dataset.

[terraform]
- main.tf: AWS infrastructure configuration.
- variables.tf: Input variables for Terraform.
- terraform.tfvars: Private configuration (gitignored).
- README.md: Instructions for deploying infrastructure.

Root Files
- README.md: Project overview, setup, and usage instructions.
- requirements.txt: Python dependencies.
- .gitignore: Specifies files/folders to exclude from Git.

---

## 🔧 Setup Instructions

### 1. Clone the Repository

- `git clone https://github.com/<your-username>/pubmed-articles.git`
- `cd pubmed-articles`


### 2. Create a Virtual Environment and Install Requirements

- `python -m venv .venv`
- `source .venv/bin/activate`
- `pip install -r requirements.txt`

### 3. Download spaCy Language Model

- `python -m spacy download en_core_web_sm`


### 🚀 Run ETL Pipeline Locally (No AWS)

To run the ETL pipeline locally on a smaller dataset (c14-gem-lo-pubmed.xml) for testing and development:
- `cd pipeline`
- `python etl_dev.py`

This will:
- Load raw_data/c14-gem-lo-pubmed.xml
- Process and match institutions
- Save output to cleaned_data/pubmed_output.csv
- Create matched_sample.csv and unmatched_sample.csv

### ☁️ Deploying to AWS (Terraform)

This project supports automatic deployment to AWS ECS via Terraform. You can:

- Upload raw XML to S3
- Trigger the ECS task via an EventBridge rule
- Receive email notifications on pipeline success/failure

For full setup instructions, see:
➡️ [terraform/README.md]


### 📓 Notebooks
Notebooks are located in the data_analysis/ folder:

Notebook:
`pubmed_result.ipynb`: Full dataset, structured analysis
`pubmed_test.ipynb`: Sample data, faster iteration/dev

Both perform similar NLP + fuzzy matching, but test runs are quicker and better for debugging.
