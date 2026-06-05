import re

def extract_university_domain(email: str) -> str | None:
    """
    Returns the domain portion of a valid .ac.uk email address.
    Returns None if the email does not match the expected pattern.
    Always lowercases and strips whitespace before checking.
    """
    if not email:
        return None
    
    # Strip leading/trailing whitespace and lowercase the entire email
    cleaned_email = email.strip().lower()
    
    # Match non-empty local part before @, and a domain ending in .ac.uk
    match = re.match(r"^([^@]+)@([a-zA-Z0-9.-]+\.ac\.uk)$", cleaned_email)
    if match:
        return match.group(2)
    
    return None

def is_domain_allowed(domain: str, allowed_domains: set) -> bool:
    """
    Returns True if the domain is permitted to register.
    If allowed_domains is empty, any valid .ac.uk domain is accepted.
    If allowed_domains is non-empty, the domain must be in the set.
    """
    if not domain:
        return False
    
    # Clean the domain just in case
    cleaned_domain = domain.strip().lower()
    
    if not allowed_domains:
        return True
        
    return cleaned_domain in allowed_domains
