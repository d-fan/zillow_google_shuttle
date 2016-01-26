# zillow_google_shuttle
Finds Zillow listings within a certain distance of Google shuttle stops (currently 0.5 miles)

Disclaimer: This was written in an afternoon and never touched again. I make no claim that this is readable or easy to use.

## Requirements

    pip install requests geopy
    
## Instructions

1. Browse to an area on Zillow and fill in any desired filters
2. Go to Developer Tools > Network
3. Filter to "getresults"
4. Paste the request URL into the script for the variable "url"
5. Run `python zillow_distance.py`
