# Archetype narrative generation logic
import pymysql
from typing import Dict, List, Tuple

# DB connection helper (adjust as needed)
def get_db():
    return pymysql.connect(
        host='localhost', user='root', password='', database='prism_db', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor
    )

TIER_MAP = {
    'Low': range(1, 4),
    'Medium': range(4, 8),
    'High': range(8, 11)
}

def get_tier(value: int) -> str:
    if value >= 8:
        return 'High'
    elif value >= 4:
        return 'Medium'
    else:
        return 'Low'

def get_descriptor_phrase(key: str, tier: str) -> str:
    db = get_db()
    try:
        with db.cursor() as cursor:
            sql = "SELECT descriptor_phrase FROM competency_descriptors WHERE competency_key=%s AND tier=%s"
            cursor.execute(sql, (key, tier))
            row = cursor.fetchone()
            return row['descriptor_phrase'] if row else f'{key} ({tier})'
    finally:
        db.close()

def flatten_skive(skive: Dict[str, Dict[str, int]]) -> List[Tuple[str, int]]:
    flat = []
    for cat in skive.values():
        for k, v in cat.items():
            flat.append((k, v))
    return flat

def generate_archetype_narrative(skive: Dict[str, Dict[str, int]]):
    all_ratings = flatten_skive(skive)
    sorted_ratings = sorted(all_ratings, key=lambda x: x[1], reverse=True)
    signature = sorted_ratings[:3]
    supporting = [x for x in sorted_ratings[3:] if x[1] >= 8]
    foundational = [x for x in sorted_ratings if 4 <= x[1] <= 7]

    sig_phrases = [get_descriptor_phrase(k, 'High') for k, _ in signature]
    sup_phrases = [get_descriptor_phrase(k, 'High') for k, _ in supporting]
    found_phrases = [get_descriptor_phrase(k, 'Medium') for k, _ in foundational]

    narrative = (
        f"This role operates at a strategic level, where success is defined by {', '.join(sig_phrases)}. "
        f"Critical supporting skills include {', '.join(sup_phrases)}. "
        f"A professional standard of competence in {', '.join(found_phrases)} is the expected foundation for this role."
    )
    archetype_name = ' '.join([k.replace('_', ' ').title() for k, _ in signature])
    return {
        "archetype_name": archetype_name,
        "narrative": narrative,
        "signature_competencies": [k for k, _ in signature],
        "supporting_competencies": [k for k, _ in supporting],
        "foundational_expectations": [k for k, _ in foundational]
    }
