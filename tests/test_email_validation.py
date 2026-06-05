from app.utils.email_validation import extract_university_domain, is_domain_allowed

def test_extract_university_domain_valid():
    """Valid student email returns correct domain."""
    assert extract_university_domain("student@brookes.ac.uk") == "brookes.ac.uk"
    assert extract_university_domain("user@student.brookes.ac.uk") == "student.brookes.ac.uk"

def test_extract_university_domain_normalises_case():
    """Uppercase email is normalised and returns correct domain."""
    assert extract_university_domain("STUDENT@Brookes.AC.UK") == "brookes.ac.uk"
    assert extract_university_domain("Student@Subdomain.Brookes.Ac.Uk") == "subdomain.brookes.ac.uk"

def test_extract_university_domain_strips_spaces():
    """Email with leading/trailing spaces is stripped correctly."""
    assert extract_university_domain("  student@brookes.ac.uk  ") == "brookes.ac.uk"

def test_extract_university_domain_invalid_tld():
    """Non .ac.uk email returns None."""
    assert extract_university_domain("student@brookes.ac.uk.fake.com") is None
    assert extract_university_domain("student@brookes.com") is None
    assert extract_university_domain("student@brookes.co.uk") is None

def test_extract_university_domain_no_at():
    """Email with no @ returns None."""
    assert extract_university_domain("no-at-sign.ac.uk") is None
    assert extract_university_domain("student.brookes.ac.uk") is None

def test_is_domain_allowed_in_set():
    """is_domain_allowed returns True when domain in non-empty set."""
    allowed = {"brookes.ac.uk", "oxford.ac.uk"}
    assert is_domain_allowed("brookes.ac.uk", allowed) is True
    assert is_domain_allowed("oxford.ac.uk", allowed) is True

def test_is_domain_allowed_empty_set():
    """is_domain_allowed returns True for any .ac.uk domain when set is empty."""
    allowed = set()
    assert is_domain_allowed("brookes.ac.uk", allowed) is True
    assert is_domain_allowed("oxford.ac.uk", allowed) is True
    assert is_domain_allowed("anydomain.ac.uk", allowed) is True

def test_is_domain_not_allowed():
    """is_domain_allowed returns False when domain not in non-empty set."""
    allowed = {"brookes.ac.uk"}
    assert is_domain_allowed("oxford.ac.uk", allowed) is False
    assert is_domain_allowed("university.ac.uk", allowed) is False
