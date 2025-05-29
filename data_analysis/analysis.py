"""Standalone script for testing XML parsing and article field extraction.

This script is not part of the production ETL pipeline. It was used to explore the 
structure of PubMed XML files and experiment with functions for extracting metadata,
author information, and affiliation data.

Useful for:
- Debugging specific XML entries
- Validating individual parsing logic
- Exploring XML tree navigation
"""

import xml.etree.ElementTree as ET

# pylint: disable=W0612
# only showed up on github workflows


def get_all_articles(root):
    """Returns all pubmed articles"""
    return root.findall('./PubmedArticle')


def get_article_title(article: ET.Element) -> str:
    """Returns article title"""
    title_element = article.find(".//ArticleTitle")
    return title_element.text


def get_article_pmid(article: ET.Element) -> str:
    """Returns article pmid"""
    pmid_element = article.find(".//PMID")
    return pmid_element.text


def get_article_year(article: ET.Element) -> str:
    """Returns article year"""
    date_element = article.find(".//PubDate/Year")
    return date_element.text


def get_article_keywords(article: ET.Element) -> list[str]:
    """Returns article keywords"""
    keywords_element = article.findall(".//KeywordList/Keyword")
    return [keyword.text for keyword in keywords_element]


def get_article_mesh(article: ET.Element) -> list[str]:
    """Returns article mesh descriptors"""
    mesh_elements = article.findall(
        ".//MeshHeadingList/MeshHeading/DescriptorName")
    return [mesh.get("UI") for mesh in mesh_elements]


def get_author_name(author: ET.Element) -> tuple:
    """Returns author's first name, last name and initials"""
    first = author.findtext('ForeName')
    last = author.findtext('LastName')
    initial = author.findtext('Initials')

    return first, last, initial


def get_author_grid(author: ET.Element) -> tuple:
    """Returns author's grid identifiers"""
    grid_identifiers = author.findall(
        './/AffiliationInfo/Identifier')
    return [
        grid.text for grid in grid_identifiers if grid.get("Source") == "GRID"]


def get_author_affiliations(author: ET.Element) -> tuple:
    """Returns author's affiliations/institutions"""
    affiliations_ = []
    for aff in author.findall('.//AffiliationInfo/Affiliation'):
        affiliations_.append(aff.text)
    return affiliations_


if __name__ == "__main__":

    # import data and read from file
    tree = ET.parse('../raw_data/pubmed_result_sjogren.xml')
    root = tree.getroot()

    # Find all PubmedArticle elements under the PubmedArticleSet root
    articles = get_all_articles(root)
    # <Element 'PubmedArticle' at 0x104bc73d0>, <Element 'PubmedArticle' at 0x104bdb6a0>,...
    count = len(articles)  # 3549

    # Task 2
    article_element = articles[23]

    title = get_article_title(article_element)

    pmid = get_article_pmid(article_element)

    date = get_article_year(article_element)

    keywords = get_article_keywords(article_element)

    mesh_descriptors = get_article_mesh(article_element)

    # Task 3

    second_article = articles[208]

    author_element = second_article.find('.//AuthorList/Author')

    firstname, lastname, initials = get_author_name(author_element)

    grid_identifier = get_author_grid(author_element)

    affiliations = get_author_affiliations(author_element)
