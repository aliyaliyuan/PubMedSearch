import requests
import xml.etree.ElementTree as ET
import time
import csv
import os
import json
from datetime import datetime, timedelta
import pandas as pd
import re

# Paths - Update these for your system
CSV_PATH = "/path/to/pubmed.csv"
DATE_FILE_PATH = "/path/to/last_date.txt"
LOG_PATH = "/path/to/pubmed_log.txt"

# Airtable Configuration
API_KEY = "INSERT_API_KEY"
BASE_ID = "appXXX"
TABLE_ID = "tblXXX"
URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def log_message(message):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    
    # Also write to log file
    with open(LOG_PATH, "a", encoding='utf-8') as f:
        f.write(log_msg + "\n")

def get_min_date():
    """Get the last update date, or default to starting date"""
    if os.path.exists(DATE_FILE_PATH):
        with open(DATE_FILE_PATH, "r") as f:
            date_str = f.read().strip()
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                log_message(f"Invalid date format in {DATE_FILE_PATH}, using default")
                return datetime(2022, 5, 1)
    else:
        log_message("No previous date file found, starting from 2022-05-01")
        return datetime(2022, 5, 1)

def save_min_date(date_obj):
    """Save the current date as the last update date"""
    try:
        with open(DATE_FILE_PATH, "w") as f:
            f.write(date_obj.strftime("%Y-%m-%d"))
        log_message(f"Updated last_date.txt to: {date_obj.strftime('%Y-%m-%d')}")
    except Exception as e:
        log_message(f"Error saving date: {str(e)}")

def get_existing_pmids_from_airtable():
    """Fetch existing PMIDs from Airtable to avoid duplicates"""
    existing_pmids = set()
    offset = None
    
    log_message("Fetching existing PMIDs from Airtable...")
    
    while True:
        try:
            params = {"fields": "PMID"}
            if offset:
                params["offset"] = offset
            
            response = requests.get(URL, headers={"Authorization": f"Bearer {API_KEY}"}, params=params)
            
            if response.status_code != 200:
                log_message(f"Error fetching existing PMIDs: {response.text}")
                break
            
            data = response.json()
            records = data.get('records', [])
            
            for record in records:
                pmid = record.get('fields', {}).get('PMID')
                if pmid:
                    existing_pmids.add(str(pmid))
            
            offset = data.get('offset')
            if not offset:
                break
                
            time.sleep(0.2)  # Rate limiting
            
        except Exception as e:
            log_message(f"Exception fetching existing PMIDs: {str(e)}")
            break
    
    log_message(f"Found {len(existing_pmids)} existing PMIDs in Airtable")
    return existing_pmids

def get_existing_pmids_from_csv():
    """Get existing PMIDs from local CSV file"""
    existing_pmids = set()
    if os.path.exists(CSV_PATH):
        try:
            df = pd.read_csv(CSV_PATH)
            if 'PMID' in df.columns:
                existing_pmids = set(df['PMID'].astype(str).tolist())
                log_message(f"Found {len(existing_pmids)} existing PMIDs in CSV")
        except Exception as e:
            log_message(f"Error reading existing CSV: {str(e)}")
    return existing_pmids

# Creates a master set that all functions add to 
PMIDs = set()

def get_all_PMIDS(query, db="pubmed", retmax=10000, email=None, tool=None, min_date=None, max_date=None):
    """Get PMIDs based on keyword search with date filtering"""
    PMID_List = set()
    retstart = 0
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    
    # Format dates for PubMed API
    min_date_str = min_date.strftime("%Y/%m/%d") if min_date else "2022/05/01"
    max_date_str = max_date.strftime("%Y/%m/%d") if max_date else "3000"
    
    log_message(f"Searching for: {query[:50]}... from {min_date_str} to {max_date_str}")
    
    while True:
        params = {
            "db": db,
            "term": query,
            "retstart": retstart,
            "retmax": retmax,
            "retmode": "xml",
            "mindate": min_date_str,
            "maxdate": max_date_str,
            "datetype": "pdat"
        }

        if email:
            params["email"] = email
        if tool:
            params["tool"] = tool

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            root = ET.fromstring(response.content)

            pmids = [ID.text for ID in root.findall(".//IdList/Id")]
            if not pmids:
                break
            
            PMID_List.update(pmids)
            retstart += retmax
            
            time.sleep(0.34)  # NCBI Rate Limit

            counter = root.find("Count")
            if counter is not None:
                total_count = int(counter.text)
                if retstart >= total_count:
                    break 
        except Exception as e:
            log_message(f"Error in get_all_PMIDS: {str(e)}")
            break

    # Add to master list
    for element in PMID_List:
        PMIDs.add(element)

    log_message(f"Found {len(PMID_List)} PMIDs for this query")
    return PMID_List

def get_all_PMIDS_ref(query_ref, email=None, tool=None, min_date=None, max_date=None):
    """Get PMIDs that reference a specific PMID"""
    PMIDS_ref = set()
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
    
    min_date_str = min_date.strftime("%Y/%m/%d") if min_date else "2022/06/01"
    max_date_str = max_date.strftime("%Y/%m/%d") if max_date else "3000"
    
    params = {
        "dbfrom": "pubmed",
        "linkname": "pubmed_pubmed_citedin",
        "id": query_ref,
        "retmode": "xml",
        "mindate": min_date_str,
        "maxdate": max_date_str
    }
    
    if email:
        params["email"] = email
    if tool:
        params["tool"] = tool

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        PMIDS_ref = [id_tag.text for id_tag in root.findall(".//Link/Id")]
        
        for element in PMIDS_ref:
            PMIDs.add(element)
            
        log_message(f"Found {len(PMIDS_ref)} citing PMIDs for {query_ref}")
    except Exception as e:
        log_message(f"Error getting citing PMIDs: {str(e)}")
    
    return PMIDS_ref

def clean_text(text):
    """Clean text for Airtable compatibility"""
    if not text:
        return ""
    text = re.sub(r'<[^<]+?>', '', str(text))
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:50000] if len(text) > 50000 else text

def clean_authors(authors_list):
    """Clean and format authors list"""
    if not authors_list:
        return ""
    author_names = []
    for au in authors_list:
        if isinstance(au, dict) and 'name' in au:
            author_names.append(au['name'])
    result = ", ".join(author_names)
    return result[:1000] if len(result) > 1000 else result

def get_metadata(pmids, db="pubmed", batch_size=200):
    """Get metadata for PMIDs"""
    log_message(f"Getting metadata for {len(pmids)} PMIDs")
    time.sleep(0.4)
    url_meta = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    all_meta = []

    for i in range(0, len(pmids), batch_size):
        batch = pmids[i:i+batch_size]
        params_meta = {
            "db": db,
            "retmode": "json",
            "id": ",".join(batch)
        }
    
        try:
            response = requests.get(url_meta, params=params_meta)
            response.raise_for_status()
            
            data = response.json()
            summaries = data["result"]
            
            for item in batch:
                if item in summaries:
                    id_data = summaries[item]
                    
                    title = clean_text(id_data.get("title", ""))
                    authors = clean_authors(id_data.get("authors", []))
                    pub_date = id_data.get("pubdate", "").split(" ")[0] if id_data.get("pubdate") else ""
                    journal = clean_text(id_data.get("fulljournalname", ""))
                    
                    metadata = {
                        "PMID": str(item),
                        "Title": title,
                        "Authors": authors,
                        "PubDate": pub_date,
                        "Journal": journal,
                        "Link": f"https://pubmed.ncbi.nlm.nih.gov/{item}/"
                    }
                    all_meta.append(metadata)

            time.sleep(0.34)
        except Exception as e:
            log_message(f"Error getting metadata for batch: {str(e)}")
            continue

    return all_meta

def append_to_csv(new_records):
    """Append new records to CSV file"""
    if not new_records:
        log_message("No new records to append to CSV")
        return
    
    # Check if file exists to determine if we need headers
    file_exists = os.path.exists(CSV_PATH)
    
    try:
        with open(CSV_PATH, mode="a", newline='', encoding='utf-8') as f:
            fieldnames = ["PMID", "Title", "Authors", "PubDate", "Journal", "Link"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # Write header only if file is new
            if not file_exists:
                writer.writeheader()
            
            writer.writerows(new_records)
        
        log_message(f"Appended {len(new_records)} new records to CSV")
    except Exception as e:
        log_message(f"Error writing to CSV: {str(e)}")

def upload_to_airtable(records):
    """Upload records to Airtable in batches"""
    if not records:
        log_message("No records to upload to Airtable")
        return
    
    log_message(f"Uploading {len(records)} records to Airtable")
    BATCH_SIZE = 10
    successful_uploads = 0
    
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i+BATCH_SIZE]
        payload = {"records": batch}
        
        try:
            response = requests.post(URL, headers=HEADERS, json=payload)
            
            if response.status_code == 200:
                successful_uploads += len(batch)
                log_message(f"Successfully uploaded batch {i//BATCH_SIZE + 1}")
            else:
                log_message(f"Failed to upload batch {i//BATCH_SIZE + 1}: {response.text}")
                
        except Exception as e:
            log_message(f"Exception uploading batch: {str(e)}")
        
        time.sleep(0.5)  # Rate limiting
    
    log_message(f"Successfully uploaded {successful_uploads} out of {len(records)} records")

def main():
    """Main execution function"""
    log_message("="*60)
    log_message("Starting PubMed Search Update")
    log_message("="*60)
    
    # Get the date range for this update
    last_update = get_min_date()
    current_date = datetime.now()
    
    log_message(f"Searching for articles from {last_update.strftime('%Y-%m-%d')} to {current_date.strftime('%Y-%m-%d')}")
    
    # Get existing PMIDs to avoid duplicates
    existing_airtable_pmids = get_existing_pmids_from_airtable()
    existing_csv_pmids = get_existing_pmids_from_csv()
    all_existing_pmids = existing_airtable_pmids.union(existing_csv_pmids)
    
    log_message(f"Total existing PMIDs to skip: {len(all_existing_pmids)}")
    
    # Keywords to search
    key_words = [
        '"cell surface proteins"[Title/Abstract] AND "mass spectrometry"[Title/Abstract]',
        '"cell surface proteomics"[Title/Abstract]',
        '"cell surface glycoproteins"[Title/Abstract] AND "mass spectrometry"[Title/Abstract]',
        '"plasma membrane"[Title/Abstract] AND "mass spectrometry"[Title/Abstract]',
        '"cell surface"[Title/Abstract] AND "mass spectrometry"[Title/Abstract]',
        '"plasma membrane proteome"[Title/Abstract]',
        '"cell surface proteome"[Title/Abstract]',
        'surfaceome[Title/Abstract]',
        '"plasma membrane protein"[Title/Abstract]',
        '"cell surface proteome"[Title/Abstract]'
    ]
    
    # Search by keywords
    for word in key_words:
        get_all_PMIDS(word, min_date=last_update, max_date=current_date)
    
    # Get citing papers
    get_all_PMIDS_ref("19349973", min_date=last_update, max_date=current_date)
    
    log_message(f"Total unique PMIDs found: {len(PMIDs)}")
    
    # Filter out existing PMIDs
    new_pmids = PMIDs - all_existing_pmids
    log_message(f"New PMIDs (not in existing records): {len(new_pmids)}")
    
    if not new_pmids:
        log_message("No new PMIDs found. Update complete.")
        save_min_date(current_date)
        return
    
    # Get metadata for new PMIDs
    unique_new_pmids = list(new_pmids)
    metadata_records = get_metadata(unique_new_pmids)
    
    if not metadata_records:
        log_message("No metadata retrieved. Update complete.")
        save_min_date(current_date)
        return
    
    # Append to CSV
    append_to_csv(metadata_records)
    
    # Prepare records for Airtable
    airtable_records = []
    for record in metadata_records:
        # Extract just the year from PubDate
        pub_year = record["PubDate"]
        if pub_year and len(pub_year) >= 4:
            # Extract first 4 characters (year) if available
            pub_year = pub_year[:4]
        else:
            pub_year = ""
        
        airtable_record = {
            "fields": {
                "PMID": record["PMID"],
                "Title": record["Title"],
                "Authors": record["Authors"],
                "PubDate": pub_year,
                "Journal": record["Journal"],
                "Link": record["Link"]
            }
        }
        airtable_records.append(airtable_record)
    # Upload to Airtable
    upload_to_airtable(airtable_records)

    
    # Update the last run date
    save_min_date(current_date)
    
    log_message("="*60)
    log_message("PubMed Search Update Complete")
    log_message(f"New records added: {len(metadata_records)}")
    log_message("="*60)

if __name__ == "__main__":
    main()
