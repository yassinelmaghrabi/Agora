

from src.GTE.clean_text import collect_expanded
from typing import List, Dict, Optional
import time
import datetime
import re
import roman
import requests
import logging
from lxml import etree
# Setup logging for errors
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

logs = []  # List to store logs
output_text = ""  # Placeholder for output text
cit_text = ""  # Placeholder for citation text
processing = False  # Flag to track processing state
prev_collection = ''  # Variable to store previous collection for continuity


def extract(input_text: str) -> tuple[List[Dict[str, str]], List[str]]:
    """
    Extracts references with ranges from the input text. The references must contain a collection name,
    a number, and a line range. This function processes these references and returns them in a structured
    format along with the raw matches.

    Args:
        input_text (str): The text from which to extract papyri references. The text should contain references
                          with collection names, numbers, and line ranges (e.g., "P. OXY. 123. 10-12").
    
    Returns:
        Tuple[List[Dict[str, str]], List[str]]:
            - List[Dict[str, str]]: A list of processed references in a structured format (e.g., {"collection": "P. OXY.", "number": 123, "identifier": "10", "lines": "12"}).
            - List[str]: A list of raw references in string form (e.g., "P. OXY. 123. 10-12 (AD 100-120);").
    """
    range_pattern = r"""
    (?P<base>                                     # Named group 'base'
        (?:[A-Z][A-Za-z.]*\s){1,2}                # 1 or 2 space-separated parts (before final)
        \d+\.                                     # Final part: digits followed by dot
    )
    (?P<ranges>                                   # Named group 'ranges'
        \d+-\d+(?:,\s*\d+-\d+)*                   # One or more ranges, comma-separated
    )
    \s*
    (?P<paren>\([^)]+\))                          # Named group 'paren': parentheses content
    """
    
    matches = re.finditer(range_pattern, input_text, re.VERBOSE)
    processed_matches = []  # Store the final processed matches
    raw_matches = []  # Store raw extracted citations
    prev_collection = ''  # Variable to store previous collection

    for match in matches:
        base = match.group("base")  # Extract base (collection, number)
        split_base = base.split(' ')  # Split base into collection and number
        
        if len(split_base) == 2:
            parts = [prev_collection, split_base[0], split_base[1]]
            base = " ".join(parts)
        else:
            prev_collection = split_base[0]  # Store collection for next iteration

        ranges = match.group("ranges")  # Extract range
        paren = match.group("paren")  # Extract parentheses content

        for r in [s.strip() for s in ranges.split(",")]:
            citation = f"{base}{r} {paren};"  # Build citation string
            raw_matches.append(citation)  # Add raw match
            processed = process_extracted_text(citation)  # Process citation

            if processed:
                processed_matches.append(processed)  # Add processed match to result

    return processed_matches, raw_matches



def extract_greek_lines_from_file(filepath):

    with open(filepath, 'rb') as f:
        xml_bytes = f.read()

    # Parse with namespace support
    tree = etree.fromstring(xml_bytes)
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

    ab_elements = tree.xpath("//tei:div[@type='edition']//tei:ab", namespaces=ns)

    greek_lines = []
    for ab in ab_elements:
        for lb in ab.xpath(".//tei:lb[@n]", namespaces=ns):
            try:
                line_num = int(lb.attrib["n"])
            except ValueError:
                continue  # skip non-integer line numbers
            if line_num:
                parts = [lb.tail or '']
                for sib in lb.itersiblings():
                    if sib.tag.endswith("lb"):
                        break
                    parts.append(sib.text or '')
                    parts.append(sib.tail or '')
                greek_lines.append("".join(parts).strip())
    output = "\n".join(greek_lines)
    print(output)
    return output

def smart_split(text: str) -> List[str]:
    """
    Splits a text into parts, respecting parentheses. This ensures that text inside parentheses is not split.

    Args:
        text (str): The text to split.
    
    Returns:
        List[str]: A list of text parts split by spaces, but respecting parentheses.
    """
    parts = []
    current = []
    depth = 0  # Parentheses depth counter

    for char in text:
        if char == '(':
            depth += 1
            current.append(char)
        elif char == ')':
            depth -= 1
            current.append(char)
        elif char == ' ' and depth == 0:
            if current:
                parts.append(''.join(current))  # Add part to the list
                current = []  # Reset current part
        else:
            current.append(char)

    if current:
        parts.append(''.join(current))

    return parts


def process_extracted_text(input_text: str) -> Optional[Dict[str, str]]:
    """
    Processes an extracted citation and returns its components in a structured dictionary.

    Args:
        input_text (str): The citation text to process (e.g., "P. OXY. 123. 10-12 (AD 100-120);").
    
    Returns:
        Optional[Dict[str, str]]: A dictionary containing the processed components:
            - "collection" (str): The collection name (e.g., "P. OXY.")
            - "number" (int): The document number (converted from Roman to Arabic numerals)
            - "identifier" (str): The identifier (e.g., "10")
            - "lines" (str): The line range (e.g., "12")
        None: If the citation is not in the expected format.
    """
    parts = smart_split(input_text)
    output = {
        "collection": "",
        "number": 0,
        "identifier": "",
        "lines": "",
    }
    
    if len(parts) % 2 == 0:
        if parts[0].endswith('.'):
            output['collection'] = parts[0][:-1].lower()
        else:
            output['collection'] = parts[0].lower()
        try:
            output['number'] = roman.fromRoman(parts[1])  # Convert Roman numeral to Arabic number
            output['identifier'] = parts[2].split('.')[0]
            return output
        except:
            return None
    return None

def get_Dir(input_dict: Dict[str, str]) -> str:
    """
    Generates the URL for a papyri reference based on the provided dictionary.

    Args:
        input_dict (Dict[str, str]): A dictionary containing the 'collection', 'number', and 'identifier' of the papyrus.
    
    Returns:
        str: The generated URL.
    """
    return f"./src/data/greek/idp.data/DDB_EpiDoc_XML/{input_dict.get('collection')}/{input_dict.get('collection')}.{input_dict.get('number')}/{input_dict.get('collection')}.{input_dict.get('number')}.{input_dict.get('identifier')}.xml"


def get_URL(input_dict: Dict[str, str]) -> str:
    """
    Generates the URL for a papyri reference based on the provided dictionary.

    Args:
        input_dict (Dict[str, str]): A dictionary containing the 'collection', 'number', and 'identifier' of the papyrus.
    
    Returns:
        str: The generated URL.
    """
    return f"https://papyri.info/ddbdp/{input_dict['collection']};{input_dict['number']};{input_dict['identifier']}"


def scrape_list(dict_list: List[Dict[str, str]], delay: float) -> List[Optional[str]]:
    """
    Scrapes the Greek text for a list of papyri references.

    Args:
        dict_list (List[Dict[str, str]]): A list of dictionaries, each containing a papyri reference with 'collection', 'number', and 'identifier'.
        delay (float): The time to wait (in seconds) between each web scraping request.
    
    Returns:
        List[Optional[str]]: A list of Greek text for each reference. Each element is the text extracted from a papyrus, or None if an error occurred.
    """
    output = []
    for dict in dict_list:
        try:
            output.append(extract_greek_lines_from_file(get_Dir(dict)))
        except:
            output.append(None)
        time.sleep(delay)  # Delay between requests
    return output


def greek_text_from_text(input_text: str, delay: float = 0) -> List[Dict[str, str]]:
    """
    Extracts Greek text from the input text by collecting references and scraping the corresponding texts.

    Args:
        input_text (str): The input text containing papyri references.
        delay (float): The time delay (in seconds) between web scraping requests to avoid overloading the server.
    
    Returns:
        List[Dict[str, str]]: A list of dictionaries containing:
            - "clause" (str): The raw reference citation.
            - "text" (str): The Greek text extracted from the reference.
    """
    input_text = " ".join(collect_expanded(input_text))  # Expand all references
    extracted_Dicts, extracted_text = extract(str(input_text))  # Extract references and text
    unique_dicts = [dict(t) for t in {tuple(d.items()) for d in extracted_Dicts}]
    output_list = []

    for a, b in zip(extracted_text, scrape_list(unique_dicts, delay)):
        if b == '' or b == None:
            continue
        output_list.append({"clause": a, "text": b})  # Pair citation and text

    return output_list

