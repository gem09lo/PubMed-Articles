# pylint: disable=R1705
# Fixed but still showed up on github workflows
# # pylint: disable=W0612
"""Process PubMed XML file to extract article metadata, author information, and create a structured DataFrame for analysis."""
import re
import pandas as pd
import spacy
import pycountry
import xml.etree.ElementTree as ET
from rapidfuzz import process
from rapidfuzz.distance import Levenshtein
from pandarallel import pandarallel


pandarallel.initialize(progress_bar=True)
cache = {}
nlp = spacy.load("en_core_web_sm")

grid_df = pd.read_csv("institutes.csv")
grid_map = grid_df.set_index('name').to_dict()['grid_id']

# Functions for parsing article metadata and extracting information


def parse_article_metadata(article: ET.Element) -> tuple[str, str, str]:
    """Returns article pmid, title and year."""
    pmid_value = article.find(".//PMID").text
    title_value = article.find(".//ArticleTitle").text
    year_element = article.find(".//PubDate/Year")
    year_value = year_element.text if year_element is not None else ""

    return pmid_value, title_value, year_value


def parse_author_info(author: ET.Element) -> str:
    """Returns author's full name."""
    last_name = author.find("LastName")
    first_name = author.find("ForeName")

    if last_name is not None and first_name is not None:
        return f"{last_name.text} {first_name.text}"
    if last_name is not None:
        return last_name.text
    if first_name is not None:
        return first_name.text
    return ""


def get_email(affiliation_text: str) -> str:
    """Extracts the email from affiliation name using regex"""
    email_address = re.search(r"[\w.]+@[\w.]+\w+", affiliation_text)
    return email_address.group() if email_address else ""


def get_zipcode(affiliation_text: str) -> str:
    """Extracts zipcode from affiliation name using regex"""
    zip_code = re.search(
        r"[A-Za-z]{1,2}\d[A-Za-z\d]? ?\d[A-Za-z]{2}|\d{5}(-\d{4})?|[A-Z]\d[A-Z] \d[A-Z]\d", affiliation_text)
    return zip_code.group() if zip_code else ""


def get_keywords(article: ET.Element) -> list[str]:
    """Returns keywords for each article"""
    keywords_element = article.findall(".//KeywordList/Keyword")
    return [keyword.text for keyword in keywords_element] if keywords_element else [""]


def get_mesh_identifiers(article: ET.Element) -> list[str]:
    """Returns mesh identifiers UI for each article"""
    mesh_elements = article.findall(
        ".//MeshHeadingList/MeshHeading/DescriptorName")
    return [mesh.get("UI") for mesh in mesh_elements] if mesh_elements else [""]

# NER-related functions


def extract_entities(affiliation_text: str):
    """Extracts entities from affiliation text."""
    doc = nlp(affiliation_text)
    entities = doc.ents

    return entities


def extract_gpe_entities(entities) -> set[str]:
    """Extracts GPE (country/location) entities from entities."""
    gpe_entities = {
        entity.text for entity in reversed(entities) if entity.label_ == "GPE"}
    return gpe_entities


def extract_org_entities(entities) -> set[str]:
    """Extracts ORG (organization) entities from entities."""
    org_entities = {
        entity.text for entity in entities if entity.label_ == "ORG"}
    return org_entities


valid_countries = {country.name for country in pycountry.countries}


def extract_country(gpe_entities: set[str]) -> str:
    """Returns valid country name from GPE entities for each affiliation"""
    return next((gpe for gpe in gpe_entities if gpe in valid_countries), None)

# Function to match institutions to GRID dataset


def match_org_to_grid(org_entities: str) -> tuple[str, str]:
    """Matches the org_entities to GRID dataset institutions with RapidFuzz"""
    best_match = None
    best_match_id = None

    for org in org_entities:
        match = process.extractOne(org, grid_map.keys(
        ), scorer=Levenshtein.normalized_similarity, score_cutoff=0.9)
        if match and match[1] >= 0.9:
            best_match = match[0]
            best_match_id = grid_map[best_match]
            break

    return (best_match, best_match_id)


def match_org_to_grid_caching(org_entities: set[str]) -> tuple[str, str]:
    """Matches the org_entities to GRID dataset institutions with RapidFuzz, using caching."""
    best_match = None
    best_match_id = None

    for org in org_entities:
        if org in cache:
            return cache[org]

        match = process.extractOne(org, grid_map.keys(
        ), scorer=Levenshtein.normalized_similarity, score_cutoff=0.9)
        if match and match[1] >= 0.9:
            best_match = match[0]
            best_match_id = grid_map[best_match]
            cache[org] = (best_match, best_match_id)
            return (best_match, best_match_id)

        cache[org] = (None, None)
    return (None, None)

# Above and beyond - top keywords


def top_keywords_by_country(pubmed_df: pd.DataFrame) -> None:
    """Prints the top 5 most frequent keywords for each country."""

    process_df = pubmed_df[(pubmed_df["Country"].notna()) &
                           (pubmed_df["Article keywords"].notna()) &
                           (pubmed_df["Article keywords"] != "['']")]

    def parse_keywords(keywords):
        if isinstance(keywords, str):
            return keywords.strip('[]').replace("'", "").split(', ')
        elif isinstance(keywords, list):
            return keywords
        else:
            return []
    process_df["Article keywords"] = process_df["Article keywords"].apply(
        parse_keywords)

    exploded_df = process_df.explode("Article keywords")

    keyword_counts = exploded_df.groupby(
        ["Country", "Article keywords"]).size().reset_index(name='count')

    top_keywords = keyword_counts.groupby("Country").apply(
        lambda x: x.nlargest(5, 'count')).reset_index(drop=True)

    for country, group in top_keywords.groupby("Country"):
        print(f"\nTop 5 keywords for {country}:")
        for _, row in group.iterrows():
            print(f"{row['Article keywords']}: {row['count']}")


def calculate_match_percentage(pubmed_df: pd.DataFrame) -> float:
    """Calculate and print the percentage of matched records."""
    pubmed_df["Match status"] = pubmed_df["Institution GRID id"].notna()
    total_records = len(pubmed_df)
    matched_records = pubmed_df["Match status"].sum()
    match_percentage = (matched_records / total_records) * 100
    print(f"Percentage of matched records: {match_percentage:.2f}%")
    return match_percentage


def extract_samples(pubmed_df: pd.DataFrame):
    """Extract and save samples of matched and unmatched records."""
    matched_records = pubmed_df["Match status"].sum()
    total_records = len(pubmed_df)

    matched_sample = pubmed_df[pubmed_df["Match status"]].sample(
        min(20, matched_records), random_state=42
    )
    unmatched_sample = pubmed_df[~pubmed_df["Match status"]].sample(
        min(20, total_records - matched_records), random_state=42
    )

    matched_sample.to_csv("matched_sample.csv", index=False)
    unmatched_sample.to_csv("unmatched_sample.csv", index=False)

# main processing


def process_pubmed_xml(file_path: str) -> pd.DataFrame:
    """Process pubmed xml and create base dataframe"""
    tree = ET.parse(file_path)
    root = tree.getroot()
    print(f"Processing {file_path}")

    data = {
        "Article PMID": [], "Article title": [], "Article keywords": [],
        "Article MESH identifiers": [], "Article Year": [], "Author full name": [],
        "Author email": [], "Affiliation name": [], "Affiliation zipcode": []
    }

    for article in root.findall("PubmedArticle"):
        pmid_value, title_value, year_value = parse_article_metadata(article)

        for author in article.findall(".//AuthorList/Author"):
            for affiliation in author.findall("AffiliationInfo/Affiliation"):
                data["Article PMID"].append(pmid_value)
                data["Article title"].append(title_value)
                data["Article Year"].append(year_value)
                data["Author full name"].append(parse_author_info(author))

                affiliation_text = affiliation.text
                data["Affiliation name"].append(affiliation_text)
                data["Author email"].append(get_email(affiliation_text))
                data["Affiliation zipcode"].append(
                    get_zipcode(affiliation_text))
                data["Article keywords"].append(get_keywords(article))
                data["Article MESH identifiers"].append(
                    get_mesh_identifiers(article))

    return pd.DataFrame(data)


def insert_affiliation_data(pubmed_df: pd.DataFrame, output_file: str) -> pd.DataFrame:
    """Add NLP and matching results to DataFrame"""

    pubmed_df["Affiliation name"] = pubmed_df["Affiliation name"].astype(str)
    pubmed_df["nlp"] = pubmed_df["Affiliation name"].apply(
        extract_entities)

    pubmed_df["Country"] = pubmed_df["nlp"].apply(extract_gpe_entities)
    pubmed_df["Institution name"] = pubmed_df["nlp"].apply(
        extract_org_entities)

    pubmed_df["Country"] = pubmed_df["Country"].apply(extract_country)

    grid = pubmed_df["Institution name"].parallel_apply(
        match_org_to_grid)

    # grid = pubmed_df["Institution name"].parallel_apply(
    #     match_org_to_grid_caching)

    pubmed_df[["Institution GRID name", "Institution GRID id"]
              ] = pd.DataFrame(grid.to_list())

    calculate_match_percentage(pubmed_df)

    extract_samples(pubmed_df)

    pubmed_df.drop(columns=["Institution name", "nlp"], inplace=True)

    # FULL DATA
    # pubmed_df.to_csv("pubmed_output2.csv", index=False)
    pubmed_df.to_csv(output_file, index=False)
    print(f"{output_file} saved successfully")

    return pubmed_df


def main_transform():
    """Processes the pubmed xml data and creates a pubmed dataframe with cleaned data"""
    pubmed_raw_file = "c14-gem-lo-pubmed.xml"
    pubmed_df = process_pubmed_xml(pubmed_raw_file)
    processed_csv_file = "pubmed_output.csv"
    pubmed_df = insert_affiliation_data(pubmed_df, processed_csv_file)

    # ABOVE AND BEYOND
    # top_keywords_by_country(pubmed_df)


if __name__ == "__main__":
    main_transform()


# 3 mins~
# 5mins 25s for match/unmatch data

# Percentage of matched records: 40.86%

# pandas multiprocessing
# to use full file change:
# pubmed_raw_file = ./challenge-1/pubmed_result_sjogren.xml"
# processed_csv_file = "pubmed_output2.csv"
