import requests
import xml.etree.ElementTree as ET



def get_pubmed_data():
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db" : "pubmed",
        "term" : "cell surface proteins AND mass spectrometry",
        "term" : "cell surface proteomics",
        "term" : "cell surface glycoproteins AND mass spectrometry",
        "term" : "plasma membrane AND mass spectrometry",
        "term" : "cell surface AND mass spectrometry",
        "term" : "plasma membrane proteome",
        "term" : "cell surface proteome",
        "term" : "surfaceome",
        "retmode" : "xml",
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        root = ET.fromstring(response.content)
        pmids = [id_elem.text for id_elem in root.findall(".//Id")]
        return pmids
    else:
        print("Error", response.status_code)
        return None 
    
def get_pubmed_with_ref():
    url_ref = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
    params = {
        "dbfrom" : "pubmed",
        "linkname" : "pubmed_pubmed_citedin",
        "id" : "19349973",
        "retmode" : "xml"
    }

    response_ref = requests.get(url_ref, params=params)
    if response_ref.status_code == 200:
        root_ref = ET.fromstring(response_ref.content)
        pmids = [id_elem.text for id_elem in root_ref.findall(".//Link/Id")]
        return pmids
    else:
        print("Error:", response_ref.status_code)
        return []



articles = get_pubmed_data()
articles_ref = get_pubmed_with_ref()

if articles:
    print("PMIDs Found with Key Words: ")
    for item in articles:
        print(item)
else:
    print("No articles found")

if articles_ref:
    print("PMIDS Found with Reference: ")
    for item_ref in articles:
        print(item_ref)
else:
    print("No articles with reference found")

PMID_List = []
for item in articles:
    PMID_List.append(item)

for item_ref in articles_ref:
    PMID_List.append(item_ref)
