"""FBS conference membership by season, 2004 onward (2004 values stand in for earlier seasons).

Each school maps to a list of (first_season, conference); a conference
applies from that season until the next entry. Schools not listed are
treated as "FCS & lower" (FCS, Division II/III, junior college, Canada).

Players are credited to the conference their school was in during their
final college season there (NFL entry year minus one). Corrections are
welcome: edit an entry and the next build picks it up.

Conventions: the Pac-10 and Pac-12 are one line ("Pac-12"); Big East
football runs through 2012 and the American starts in 2013; Notre Dame's
2020 season in the ACC is recorded.
"""

SEC, B1G, B12, ACC, P12 = "SEC", "Big Ten", "Big 12", "ACC", "Pac-12"
BE, AAC, MWC, CUSA = "Big East", "American", "Mountain West", "Conference USA"
MAC, SBC, WAC, IND = "MAC", "Sun Belt", "WAC", "Independent"
FCS = "FCS & lower"

HISTORY = {
    # ---- SEC ----
    "Alabama": [(2004, SEC)], "Arkansas": [(2004, SEC)], "Auburn": [(2004, SEC)],
    "Florida": [(2004, SEC)], "Georgia": [(2004, SEC)], "Kentucky": [(2004, SEC)],
    "LSU": [(2004, SEC)], "Ole Miss": [(2004, SEC)], "Mississippi State": [(2004, SEC)],
    "South Carolina": [(2004, SEC)], "Tennessee": [(2004, SEC)], "Vanderbilt": [(2004, SEC)],
    "Missouri": [(2004, B12), (2012, SEC)],
    "Texas A&M": [(2004, B12), (2012, SEC)],
    "Texas": [(2004, B12), (2024, SEC)],
    "Oklahoma": [(2004, B12), (2024, SEC)],
    # ---- Big Ten ----
    "Illinois": [(2004, B1G)], "Indiana": [(2004, B1G)], "Iowa": [(2004, B1G)],
    "Michigan": [(2004, B1G)], "Michigan State": [(2004, B1G)], "Minnesota": [(2004, B1G)],
    "Northwestern": [(2004, B1G)], "Ohio State": [(2004, B1G)], "Penn State": [(2004, B1G)],
    "Purdue": [(2004, B1G)], "Wisconsin": [(2004, B1G)],
    "Nebraska": [(2004, B12), (2011, B1G)],
    "Maryland": [(2004, ACC), (2014, B1G)],
    "Rutgers": [(2004, BE), (2013, AAC), (2014, B1G)],
    "USC": [(2004, P12), (2024, B1G)], "UCLA": [(2004, P12), (2024, B1G)],
    "Oregon": [(2004, P12), (2024, B1G)], "Washington": [(2004, P12), (2024, B1G)],
    # ---- Big 12 ----
    "Baylor": [(2004, B12)], "Iowa State": [(2004, B12)], "Kansas": [(2004, B12)],
    "Kansas State": [(2004, B12)], "Oklahoma State": [(2004, B12)], "Texas Tech": [(2004, B12)],
    "Colorado": [(2004, B12), (2011, P12), (2024, B12)],
    "TCU": [(2004, CUSA), (2005, MWC), (2012, B12)],
    "West Virginia": [(2004, BE), (2012, B12)],
    "BYU": [(2004, MWC), (2011, IND), (2023, B12)],
    "UCF": [(2004, MAC), (2005, CUSA), (2013, AAC), (2023, B12)],
    "Cincinnati": [(2004, CUSA), (2005, BE), (2013, AAC), (2023, B12)],
    "Houston": [(2004, CUSA), (2013, AAC), (2023, B12)],
    "Arizona": [(2004, P12), (2024, B12)], "Arizona State": [(2004, P12), (2024, B12)],
    "Utah": [(2004, MWC), (2011, P12), (2024, B12)],
    # ---- ACC ----
    "Clemson": [(2004, ACC)], "Duke": [(2004, ACC)], "Florida State": [(2004, ACC)],
    "Georgia Tech": [(2004, ACC)], "Miami": [(1991, BE), (2004, ACC)], "North Carolina": [(2004, ACC)],
    "NC State": [(2004, ACC)], "Virginia": [(2004, ACC)], "Virginia Tech": [(1991, BE), (2004, ACC)],
    "Wake Forest": [(2004, ACC)],
    "Boston College": [(2004, BE), (2005, ACC)],
    "Pitt": [(2004, BE), (2013, ACC)], "Syracuse": [(2004, BE), (2013, ACC)],
    "Louisville": [(2004, CUSA), (2005, BE), (2013, AAC), (2014, ACC)],
    "Cal": [(2004, P12), (2024, ACC)], "Stanford": [(2004, P12), (2024, ACC)],
    "SMU": [(2004, WAC), (2005, CUSA), (2013, AAC), (2024, ACC)],
    # ---- Pac-12 holdovers ----
    "Oregon State": [(2004, P12)], "Washington State": [(2004, P12)],
    # ---- Independents ----
    "Notre Dame": [(2004, IND), (2020, ACC), (2021, IND)],
    "UConn": [(2004, BE), (2013, AAC), (2020, IND)],
    "UMass": [(2012, MAC), (2016, IND), (2025, MAC)],
    "Army": [(2004, CUSA), (2005, IND), (2024, AAC)],
    "Navy": [(2004, IND), (2015, AAC)],
    # ---- American ----
    "Memphis": [(2004, CUSA), (2013, AAC)],
    "Temple": [(2004, BE), (2005, IND), (2007, MAC), (2012, BE), (2013, AAC)],
    "South Florida": [(2004, CUSA), (2005, BE), (2013, AAC)],
    "Tulane": [(2004, CUSA), (2014, AAC)],
    "Tulsa": [(2004, WAC), (2005, CUSA), (2014, AAC)],
    "East Carolina": [(2004, CUSA), (2014, AAC)],
    "Charlotte": [(2015, CUSA), (2023, AAC)],
    "FAU": [(2004, IND), (2005, SBC), (2013, CUSA), (2023, AAC)],
    "North Texas": [(2004, SBC), (2013, CUSA), (2023, AAC)],
    "Rice": [(2004, WAC), (2005, CUSA), (2023, AAC)],
    "UAB": [(2004, CUSA), (2023, AAC)],
    "UTSA": [(2012, WAC), (2013, CUSA), (2023, AAC)],
    # ---- Mountain West ----
    "Air Force": [(2004, MWC)], "Colorado State": [(2004, MWC)], "New Mexico": [(2004, MWC)],
    "San Diego State": [(2004, MWC)], "UNLV": [(2004, MWC)], "Wyoming": [(2004, MWC)],
    "Boise State": [(2004, WAC), (2011, MWC)],
    "Fresno State": [(2004, WAC), (2012, MWC)],
    "Nevada": [(2004, WAC), (2012, MWC)],
    "Hawaii": [(2004, WAC), (2012, MWC)],
    "San Jose State": [(2004, WAC), (2013, MWC)],
    "Utah State": [(2004, SBC), (2005, WAC), (2013, MWC)],
    # ---- Conference USA ----
    "UTEP": [(2004, WAC), (2005, CUSA)],
    "Louisiana Tech": [(2004, WAC), (2013, CUSA)],
    "FIU": [(2004, IND), (2005, SBC), (2013, CUSA)],
    "Middle Tennessee": [(2004, SBC), (2013, CUSA)],
    "Western Kentucky": [(2008, IND), (2009, SBC), (2014, CUSA)],
    "Liberty": [(2018, IND), (2023, CUSA)],
    "Jacksonville State": [(2023, CUSA)],
    "Sam Houston State": [(2023, CUSA)],
    "New Mexico State": [(2004, SBC), (2005, WAC), (2013, IND), (2014, SBC), (2018, IND), (2023, CUSA)],
    "Delaware": [(2025, CUSA)],
    "Missouri State": [(2025, CUSA)],
    # ---- MAC ----
    "Akron": [(2004, MAC)], "Ball State": [(2004, MAC)], "Bowling Green": [(2004, MAC)],
    "Buffalo": [(2004, MAC)], "Central Michigan": [(2004, MAC)], "Eastern Michigan": [(2004, MAC)],
    "Kent State": [(2004, MAC)], "Miami (OH)": [(2004, MAC)], "Northern Illinois": [(2004, MAC)],
    "Ohio": [(2004, MAC)], "Toledo": [(2004, MAC)], "Western Michigan": [(2004, MAC)],
    # ---- Sun Belt ----
    "Arkansas State": [(2004, SBC)], "Louisiana": [(2004, SBC)], "Louisiana-Monroe": [(2004, SBC)],
    "Troy": [(2004, SBC)],
    "South Alabama": [(2012, SBC)],
    "Georgia State": [(2013, SBC)],
    "Texas State": [(2012, WAC), (2013, SBC)],
    "App State": [(2014, SBC)],
    "Georgia Southern": [(2014, SBC)],
    "Coastal Carolina": [(2017, SBC)],
    "James Madison": [(2023, SBC)],
    "Old Dominion": [(2014, CUSA), (2022, SBC)],
    "Marshall": [(2004, MAC), (2005, CUSA), (2022, SBC)],
    "Southern Miss": [(2004, CUSA), (2022, SBC)],
    "Idaho": [(2004, SBC), (2005, WAC), (2013, IND), (2014, SBC), (2018, FCS)],
    "Sacramento State": [(2025, IND)],
}

POWER = {SEC, B1G, B12, ACC, P12}


def conference(school, season):
    """Conference for a school in a given season; FCS & lower if unknown."""
    hist = HISTORY.get(school)
    if not hist:
        return FCS
    # the table starts in 2004; earlier seasons use a school's 2004 conference
    # (older veterans in archived seasons), apart from the moves listed above
    conf = hist[0][1] if hist[0][0] <= 2004 else FCS
    for start, name in hist:
        if season >= start:
            conf = name
    return conf
