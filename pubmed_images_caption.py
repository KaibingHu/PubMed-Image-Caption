import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import json
import argparse
import os
from datetime import datetime

# Register XML namespace
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

# Function to fetch CDN image links for a given PMC ID
def fetch_cdn_links(pmc_id):
    """
    Fetches CDN image links from the PMC article page.
    Args:
        pmc_id (str): PMC ID of the article.

    Returns:
        list: List of CDN image URLs.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
    }
    url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch page for PMC{pmc_id}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    cdn_links = []

    for img_tag in soup.find_all('img'):
        src = img_tag.get('src')
        if src and 'cdn.ncbi.nlm.nih.gov' in src:
            if src.startswith('//'):
                src = 'https:' + src
            cdn_links.append(src)
    return cdn_links

# Function to fetch PMC IDs based on search term
def fetch_pmc_ids(term, db="pmc", retmax=100):
    """
    Fetches PMC IDs for articles matching the search term.
    Args:
        term (str): Search term for query.
        db (str): Database to query.
        retmax (int): Maximum number of results.

    Returns:
        list: List of PMC IDs.
    """
    esearch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db={db}&term={term}&retmax={retmax}"
    try:
        response = requests.get(esearch_url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch PMC IDs: {e}")
        return []

    root = ET.fromstring(response.content)
    pmcids = [id_elem.text for id_elem in root.findall(".//Id")]
    return pmcids

# Function to fetch article details in batches
def fetch_article_details(pmcids, batch_size=5):
    """
    Fetches article details in batches including captions and image URLs.
    Args:
        pmcids (list): List of PMC IDs.
        batch_size (int): Number of articles to fetch in one batch.

    Returns:
        list: List of dictionaries containing article details.
    """
    article_details = []

    for batch_start in range(0, len(pmcids), batch_size):
        batch = pmcids[batch_start:batch_start + batch_size]
        ids = ",".join(batch)
        
        efetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={ids}&retmode=xml"
        try:
            response = requests.get(efetch_url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch details for batch {batch}: {e}")
            continue

        root = ET.fromstring(response.content)
        articles = root.findall(".//article")

        for article in articles:
            pmcid_elem = article.find(".//article-id[@pub-id-type='pmc']")
            pmcid = pmcid_elem.text if pmcid_elem is not None else "No PMCID"

            cdn_links = fetch_cdn_links(pmcid)

            title_elem = article.find(".//article-title")
            title = title_elem.text if title_elem is not None else "No title"

            abstract_elem = article.find(".//abstract")
            abstract = abstract_elem.text if abstract_elem is not None else "No abstract"

            captions = []
            images = []
            for fig in article.findall(".//fig"):
                caption_elem = fig.find(".//caption/p")
                caption = caption_elem.text if caption_elem is not None else "No caption"

                graphic = fig.find(".//graphic")
                image_url = "No image URL"
                if graphic is not None:
                    image_href = graphic.attrib.get("{http://www.w3.org/1999/xlink}href")
                    if image_href:
                        matched_url = next((url for url in cdn_links if image_href in url), "No Match Found")
                        image_url = matched_url

                captions.append(caption)
                images.append(image_url)

            article_details.append({
                "pmcid": pmcid,
                "title": title,
                "abstract": abstract,
                "captions": captions,
                "images": images
            })

    return article_details

# Main Execution
def main():
    """
    Main function to orchestrate the data retrieval process.
    """
    parser = argparse.ArgumentParser(description="Fetch PMC articles with images.")
    parser.add_argument('--term', type=str, required=True, help='Search term')
    parser.add_argument('--retmax', type=int, default=10, help='Number of results to fetch')
    args = parser.parse_args()

    # Fetch PMC IDs
    pmcids = fetch_pmc_ids(term=args.term, retmax=args.retmax)
    print(f"Retrieved {len(pmcids)} PMCIDs: {pmcids}")

    # Fetch article details
    if pmcids:
        details = fetch_article_details(pmcids, batch_size=5)
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{args.term}_{args.retmax}_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(details, f, indent=4)
        print(f"Results saved to {filename}")

if __name__ == "__main__":
    main()
