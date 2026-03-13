"""Ward zoning data computation for Chicago RS-zoned land percentages.

Computes the percentage of RS-zoned (residential single-family) land
relative to total ADU-eligible land area per ward, using zone data
from the Chicago Cityscape Zoning Explorer API.
"""

# Prefixes for ADU-eligible zone classes
ADU_ELIGIBLE_PREFIXES = ("B", "C", "RM", "RS", "RT")

# Prefixes for zones excluded from the denominator
EXCLUDED_PREFIXES = ("PD", "PMD", "M", "T", "POS")


def compute_rs_percentage(zone_data: list[dict]) -> float:
    """Compute RS-zoned land as a percentage of ADU-eligible area.

    Args:
        zone_data: List of zone dicts with 'zone_class' and 'area_sqft' keys.

    Returns:
        RS percentage rounded to one decimal place, or 0.0 if no eligible area.
    """
    eligible_area = 0.0
    rs_area = 0.0
    for zone in zone_data:
        zone_class = zone.get("zone_class", "")
        area = float(zone.get("area_sqft", 0))
        if any(zone_class.startswith(prefix) for prefix in ADU_ELIGIBLE_PREFIXES):
            eligible_area += area
            if zone_class.startswith("RS-"):
                rs_area += area
    if eligible_area == 0:
        return 0.0
    return round(rs_area / eligible_area * 100, 1)
