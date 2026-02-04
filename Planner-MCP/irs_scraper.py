"""
990_scraper.py
Charter & Stone - IRS Form 990 Scraper Module

Retrieves nonprofit financial data from ProPublica's Nonprofit Explorer API.
Part of the "Deep Dive Analyst" toolkit.

Usage:
    python 990_scraper.py "Austin College"
    python 990_scraper.py "University of Dallas"

API Documentation: https://projects.propublica.org/nonprofits/api
"""

import sys
import json
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from urllib.parse import quote


# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_URL = "https://projects.propublica.org/nonprofits/api/v2"
SEARCH_ENDPOINT = f"{BASE_URL}/search.json"
ORG_ENDPOINT = f"{BASE_URL}/organizations"

# Request timeout in seconds
TIMEOUT = 15

# User agent for polite API access
HEADERS = {
    "User-Agent": "Charter-Stone-990-Scraper/1.0 (Higher Education Research)"
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Filing990Summary:
    """Structured summary of a Form 990 filing."""
    organization_name: str
    ein: str
    tax_year: int
    total_revenue: Optional[int]
    total_expenses: Optional[int]
    net_assets: Optional[int]
    pdf_url: Optional[str]
    form_type: str
    city: Optional[str]
    state: Optional[str]
    ntee_code: Optional[str]  # National Taxonomy of Exempt Entities
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "organization_name": self.organization_name,
            "ein": self.ein,
            "ein_formatted": f"{self.ein[:2]}-{self.ein[2:]}" if len(self.ein) >= 3 else self.ein,
            "tax_year": self.tax_year,
            "total_revenue": self.total_revenue,
            "total_expenses": self.total_expenses,
            "net_assets": self.net_assets,
            "net_income": (self.total_revenue - self.total_expenses) if self.total_revenue and self.total_expenses else None,
            "pdf_url": self.pdf_url,
            "form_type": self.form_type,
            "city": self.city,
            "state": self.state,
            "ntee_code": self.ntee_code
        }
    
    def __str__(self) -> str:
        """Human-readable summary."""
        def fmt_currency(val: Optional[int]) -> str:
            if val is None:
                return "N/A"
            return f"${val:,.0f}"
        
        net_income = None
        if self.total_revenue and self.total_expenses:
            net_income = self.total_revenue - self.total_expenses
        
        return f"""
================================================================================
IRS FORM 990 SUMMARY
================================================================================
Organization:   {self.organization_name}
EIN:            {self.ein[:2]}-{self.ein[2:] if len(self.ein) >= 3 else self.ein}
Location:       {self.city or 'Unknown'}, {self.state or 'Unknown'}
Tax Year:       {self.tax_year}
Form Type:      {self.form_type}
NTEE Code:      {self.ntee_code or 'Not classified'}

FINANCIALS
--------------------------------------------------------------------------------
Total Revenue:  {fmt_currency(self.total_revenue)}
Total Expenses: {fmt_currency(self.total_expenses)}
Net Income:     {fmt_currency(net_income)}
Net Assets:     {fmt_currency(self.net_assets)}

DOCUMENTATION
--------------------------------------------------------------------------------
PDF Filing:     {self.pdf_url or 'Not available'}
================================================================================
"""


# =============================================================================
# API FUNCTIONS
# =============================================================================

def search_organization(name: str, state: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search for organizations by name.
    
    Args:
        name: Organization name to search for
        state: Optional 2-letter state code to filter results
    
    Returns:
        List of matching organization records
    """
    params = {"q": name}
    if state:
        params["state[id]"] = state.upper()
    
    try:
        response = requests.get(
            SEARCH_ENDPOINT,
            params=params,
            headers=HEADERS,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        
        return data.get("organizations", [])
    
    except requests.exceptions.RequestException as e:
        print(f"Search API error: {e}")
        return []


def get_organization_details(ein: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve full organization data by EIN.
    
    Args:
        ein: Employer Identification Number (digits only)
    
    Returns:
        Full organization record including filings, or None on error
    """
    # Strip any formatting from EIN
    ein_clean = ein.replace("-", "").replace(" ", "")
    
    url = f"{ORG_ENDPOINT}/{ein_clean}.json"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            print(f"Organization with EIN {ein} not found")
        else:
            print(f"API error: {e}")
        return None
    
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def get_most_recent_filing(org_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract the most recent filing with financial data.
    
    Args:
        org_data: Full organization record from API
    
    Returns:
        Most recent filing record, or None if no filings exist
    """
    filings = org_data.get("filings_with_data", [])
    
    if not filings:
        # Fall back to filings without extracted data (PDF only)
        filings = org_data.get("filings_without_data", [])
        if filings:
            # Sort by tax period year descending
            filings_sorted = sorted(filings, key=lambda x: x.get("tax_prd_yr", 0), reverse=True)
            return filings_sorted[0] if filings_sorted else None
        return None
    
    # Sort by tax period year descending to get most recent
    filings_sorted = sorted(filings, key=lambda x: x.get("tax_prd_yr", 0), reverse=True)
    return filings_sorted[0] if filings_sorted else None


def build_summary(org_data: Dict[str, Any], filing: Dict[str, Any]) -> Filing990Summary:
    """
    Build a structured summary from raw API data.
    
    Args:
        org_data: Organization profile data
        filing: Filing record (either with or without extracted data)
    
    Returns:
        Filing990Summary dataclass
    """
    org = org_data.get("organization", {})
    
    # Determine form type
    form_type_map = {0: "990", 1: "990-EZ", 2: "990-PF"}
    form_type_num = filing.get("formtype", 0)
    form_type = filing.get("formtype_str") or form_type_map.get(form_type_num, "990")
    
    return Filing990Summary(
        organization_name=org.get("name", "Unknown"),
        ein=str(org.get("ein", filing.get("ein", ""))),
        tax_year=filing.get("tax_prd_yr", 0),
        total_revenue=filing.get("totrevenue"),
        total_expenses=filing.get("totfuncexpns"),
        net_assets=filing.get("totassetsend") or filing.get("totnetassetend"),
        pdf_url=filing.get("pdf_url"),
        form_type=form_type,
        city=org.get("city"),
        state=org.get("state"),
        ntee_code=org.get("ntee_code")
    )


# =============================================================================
# MAIN SCRAPER FUNCTION
# =============================================================================

def scrape_990(
    university_name: str,
    state: Optional[str] = None,
    return_all_matches: bool = False
) -> Optional[Filing990Summary]:
    """
    Main entry point: Search for a university and retrieve its 990 data.
    
    Args:
        university_name: Name of the university/nonprofit to search
        state: Optional 2-letter state code to filter results
        return_all_matches: If True, print all search matches for disambiguation
    
    Returns:
        Filing990Summary for the best match, or None if not found
    """
    print(f"Searching for: {university_name}")
    
    # Step 1: Search for the organization
    matches = search_organization(university_name, state)
    
    if not matches:
        print("No organizations found matching that name.")
        return None
    
    # Filter for likely educational institutions (NTEE codes starting with B)
    # B = Education category in NTEE taxonomy
    edu_matches = [m for m in matches if (m.get("ntee_code") or "").startswith("B")]
    
    # Prefer educational matches, fall back to all matches
    candidates = edu_matches if edu_matches else matches
    
    if return_all_matches or len(candidates) > 1:
        print(f"\nFound {len(matches)} total matches ({len(edu_matches)} educational):\n")
        for i, org in enumerate(candidates[:10], 1):  # Show top 10
            print(f"  {i}. {org.get('name', 'Unknown')}")
            print(f"     EIN: {org.get('strein', 'N/A')} | {org.get('city', '')}, {org.get('state', '')}")
            print(f"     NTEE: {org.get('ntee_code', 'N/A')}")
            print()
    
    # Take the first (best) match
    best_match = candidates[0]
    ein = str(best_match.get("ein", ""))
    
    print(f"Best match: {best_match.get('name')} (EIN: {best_match.get('strein')})")
    
    # Step 2: Get full organization details
    print(f"Fetching 990 filings...")
    org_data = get_organization_details(ein)
    
    if not org_data:
        return None
    
    # Step 3: Get most recent filing
    filing = get_most_recent_filing(org_data)
    
    if not filing:
        print("No Form 990 filings found for this organization.")
        return None
    
    # Step 4: Build and return summary
    summary = build_summary(org_data, filing)
    
    return summary


def scrape_990_by_ein(ein: str) -> Optional[Filing990Summary]:
    """
    Direct lookup by EIN (bypasses search).
    
    Args:
        ein: Employer Identification Number
    
    Returns:
        Filing990Summary or None
    """
    print(f"Fetching organization by EIN: {ein}")
    
    org_data = get_organization_details(ein)
    
    if not org_data:
        return None
    
    filing = get_most_recent_filing(org_data)
    
    if not filing:
        print("No Form 990 filings found.")
        return None
    
    return build_summary(org_data, filing)


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """Command-line interface."""
    if len(sys.argv) < 2:
        print("Usage: python 990_scraper.py <university_name> [state_code]")
        print("       python 990_scraper.py --ein <ein_number>")
        print()
        print("Examples:")
        print('  python 990_scraper.py "Austin College"')
        print('  python 990_scraper.py "University of Dallas" TX')
        print('  python 990_scraper.py --ein 75-1154650')
        sys.exit(1)
    
    # Check for EIN mode
    if sys.argv[1] == "--ein" and len(sys.argv) >= 3:
        ein = sys.argv[2]
        result = scrape_990_by_ein(ein)
    else:
        university_name = sys.argv[1]
        state = sys.argv[2] if len(sys.argv) >= 3 else None
        result = scrape_990(university_name, state)
    
    if result:
        print(result)
        
        # Also output JSON for programmatic use
        print("\nJSON Output:")
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print("\nCould not retrieve 990 data.")
        sys.exit(1)


if __name__ == "__main__":
    main()
