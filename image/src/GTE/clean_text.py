
import re
import roman

def extract(input_text):
    """
    Extracts range-based references (e.g., '25-32, 39-43') from the input text,
    adding dots as needed and returning the modified references as new entries.
    
    Args:
        input_text (str): The input text containing the range references
        
    Returns:
        list: List of expanded range references with appropriate dots added
    """
    pattern = r"\.\d+(?:-\d+)?,*(?:\s*\d+(?:-\d+)?)*"
    
    match = re.search(pattern, input_text)
    if not match:
        return []

    matched_range_text = match.group()  # Extracted range reference, e.g., "25-32, 39-43"
    new_entries = []
    need_dot = False
    
    for r in matched_range_text.split(","):
        # If needed, add a dot to the beginning of the reference
        re_text = "." + r.strip() if need_dot else r.strip()
        new_entries.append(re.sub(pattern, re_text, input_text))
        need_dot = True  # After the first entry, the next ones should have a dot

    return new_entries

def substitute_expanded(text, previous_collection='', previous_volume='', previous_identifier=''):
    """
    Substitutes all papyri references in the input text with their expanded form,
    using the provided expand() function. Updates the text in-place.

    Args:
        text (str): The original text with papyri references
        previous_collection (str): Context for expansion (default is '')
        previous_volume (str): Context for expansion (default is '')
        previous_identifier (str): Context for expansion (default is '')

    Returns:
        str: The updated text with all papyri references substituted by their expanded forms
    """
    # Save original text for substitution
    original_text = text
    text = re.sub(r'\n\s*', ' ', text)
    text = text.replace("?", "")
    
    # Get list of references to replace
    references = extract_papyri_references(original_text)

    for ref in references:
        expanded_refs, previous_collection, previous_volume, previous_identifier = expand(
            ref, previous_collection, previous_volume, previous_identifier
        )
        
        # Handle list of expanded references or single expanded reference
        if isinstance(expanded_refs, list):
            expanded_str = "; ".join(expanded_refs) + ";"
        else:
            expanded_str = expanded_refs + ";"
        
        # Replace reference in the original text
        original_text = original_text.replace(ref, expanded_str)
    
    return original_text

def is_roman_numeral(s):
    """
    Check if the given string is a valid Roman numeral.

    Args:
        s (str): The string to check

    Returns:
        bool: True if the string is a valid Roman numeral, otherwise False
    """
    try:
        roman.fromRoman(s)
        return True
    except roman.InvalidRomanNumeralError:
        return False

def smart_split(text, delimiter):
    """
    Splits the input text by the specified delimiter, ensuring that parentheses
    and brackets are respected (i.e., they are not split inside them).

    Args:
        text (str): The text to split
        delimiter (str): The delimiter to split by (e.g., space, comma, etc.)

    Returns:
        list: List of parts obtained by splitting the text
    """
    parts = []
    current = []
    depth = 0

    for char in text:
        # Track parentheses and brackets depth
        if char == '(' or char == '[':
            depth += 1
            current.append(char)
        elif char == ')' or char == ']' and depth > 0:
            depth -= 1
            current.append(char)
        elif char == delimiter and depth == 0:
            if current:
                parts.append(''.join(current))
                current = []
        else:
            current.append(char)

    # Add the last part
    if current:
        parts.append(''.join(current))
    
    return parts

def expand(text, previous_collection='', previous_volume='', previous_identifier=''):
    """
    Expands a papyri reference text into its full form, updating the provided context
    (collection, volume, identifier).

    Args:
        text (str): The papyri reference text
        previous_collection (str): Previous collection context
        previous_volume (str): Previous volume context
        previous_identifier (str): Previous identifier context

    Returns:
        tuple: The expanded reference text, updated collection, volume, and identifier
    """
    parts = smart_split(text, ' ')
    
    # Handle case where the last part is in square brackets
    if parts[-1].startswith('['):
        bracket = parts.pop()
    
    offset = 1 if "?" in parts else 0

    if len(parts) == 4 + offset:
        # If the reference has 4 parts, update the collection, volume, and identifier
        previous_collection = parts[0]
        previous_volume = parts[1]
        previous_identifier = parts[2].split('.')[0]
        new_clause = text
    elif len(parts) == 3 + offset and is_roman_numeral(parts[0]):
        # If it's a Roman numeral volume, create a new reference with the collection
        previous_volume = parts[0]
        new_clause = previous_collection + ' ' + text
    elif len(parts) == 3 + offset:
        # If the reference has 3 parts, update the collection
        previous_collection = parts[0]
        new_clause = text
    elif len(parts) == 2 + offset:
        # Handle the case where the identifier is missing
        missing_identifier = len(parts[0].split('.')) == 1
        if missing_identifier:
            new_clause = previous_collection + ' ' + previous_volume + ' ' + previous_identifier + '.' + text
        else:
            previous_identifier = parts[0].split('.')[0]
            new_clause = previous_collection + ' ' + previous_volume + ' ' + text
    else:
        # Default case, append 'Failed' if the format doesn't match
        new_clause = text + " Failed"

    return (' '.join(new_clause.split()), previous_collection, previous_volume, previous_identifier)

def collect_expanded(text, previous_collection='', previous_volume='', previous_identifier=''):
    """
    Collects all expanded papyri references from the input text,
    using the provided expand() function and preserving expansion context.

    Args:
        text (str): The original text with papyri references
        expand (function): A function that returns (expanded_refs, prev_coll, prev_vol, prev_id)
        previous_collection (str): Optional context for expansion
        previous_volume (str): Optional context for expansion
        previous_identifier (str): Optional context for expansion

    Returns:
        list: All expanded references in a flat list
    """
    text = re.sub(r'\n\s*', ' ', text)
    text = text.replace("?", "")
    
    references = extract_papyri_references(text)
    all_expanded = []

    for ref in references:
        expanded_refs, previous_collection, previous_volume, previous_identifier = expand(
            ref.strip(';'), previous_collection, previous_volume, previous_identifier
        )
        if isinstance(expanded_refs, list):
            all_expanded.extend(expanded_refs)
        else:
            all_expanded.append(expanded_refs)
    
    return all_expanded

def extract_papyri_references(text):
    """
    Extracts papyri references from the input text. These references are typically
    in the form of document identifiers, volume, and line ranges.

    Args:
        text (str): The input text with papyri references

    Returns:
        list: List of extracted papyri references in their original order
    """
    # Clean up text by replacing newlines and removing question marks
    text = re.sub(r'\n\s*', ' ', text)
    text = text.replace("?", "")
    
    # Split the text by semicolons to process each part
    parts = [p.strip() for p in text.split(';')]
    all_references = []
    
    for i, part in enumerate(parts):
        if not part:  # Skip empty parts
            continue
            
        # Detect and extract papyri references based on pattern
        if i == 0 or re.match(r'[A-Z]+\.?', part):
            pattern = r"""
            ([A-Z]+(?:\.[A-Z]+)*\.?\s+              # Document identifier (P.CAIR.ZEN, BGU, CPR, etc)
            (?:[IVX]+|[0-9]+)?\s*                   # Volume number (Roman or Arabic)
            (?:[0-9]+(?:\.[0-9]+)*)                 # Document number
            (?:\.[0-9]+(?:-[0-9]+)?                 # Line reference range
            (?:,\s*[0-9]+(?:-[0-9]+)?)*)?           # Additional line references
            (?:\?)?                                 # Optional question mark
            \s*(?:\([^()]*\))                       # Date and location in parentheses
            (?:\s*\[[^]]*\])?)                      # Optional notes in square brackets
            """
            matches = re.findall(pattern, part, re.VERBOSE)
            all_references.extend(matches)
        else:
            # Handle continuation references (e.g., just volume or document number)
            pattern = r"""
            ((?:[IVX]+\s+)?                         # Optional volume number (Roman numerals)
            [0-9]+(?:\.[0-9]+)*                     # Document number
            (?:\.[0-9]+(?:-[0-9]+)?                 # Line reference range
            (?:,\s*[0-9]+(?:-[0-9]+)?)*)?           # Additional line references
            (?:\?)?                                 # Optional question mark
            \s*(?:\([^()]*\))                       # Date and location in parentheses
            (?:\s*\[[^]]*\])?)                      # Optional notes in square brackets
            """
            matches = re.findall(pattern, part, re.VERBOSE)
            all_references.extend(matches)
    
    new_references = []
    for reference in all_references:
        ref_with_semicolon = reference + ";"
        
        if not is_balanced(ref_with_semicolon):
            continue  # Skip unbalanced references

        extracted = extract(ref_with_semicolon)
        
        if extracted:
            for nref in extracted:
                if is_balanced(nref):
                    new_references.append(nref)
        else:
            new_references.append(ref_with_semicolon)
    
    return new_references

def is_balanced(s):
    """
    Checks if the parentheses and brackets in a string are balanced.

    Args:
        s (str): The string to check

    Returns:
        bool: True if the string has balanced parentheses and brackets, otherwise False
    """
    return s.count('(') == s.count(')') and s.count('[') == s.count(']')

