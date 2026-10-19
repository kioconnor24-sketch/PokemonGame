"""Read-only planning scenarios for the remaining byte met-origin codebook.

Counts *names*, not maps. Nothing here approves a name, allocates a code,
retires an old origin, or certifies that the area register covers all children.
"""
import csv
from pathlib import Path
import unicodedata

FIRST_NEW = 216
LAST_ORDINARY = 252
NONE = 215
SINNOH = "REGION_SINNOH"


def name_key(name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("origin name must be a nonempty string")
    return " ".join(unicodedata.normalize("NFC", name).casefold().split())


def read_area_register(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"TrackerKey", "LocationOrZone"} <= set(reader.fieldnames or ()):
            raise ValueError("area register requires TrackerKey and LocationOrZone columns")
        rows = list(reader)
    _areas(rows)
    return rows


def _areas(rows):
    result = {}
    for row in rows:
        key = row.get("TrackerKey")
        if not isinstance(key, str) or not key.strip():
            raise ValueError("area requires a nonempty TrackerKey")
        if key in result:
            raise ValueError(f"duplicate area key: {key}")
        name_key(row.get("LocationOrZone"))
        result[key] = row["LocationOrZone"].strip()
    if not result:
        raise ValueError("area inventory is empty")
    return result


def origin_demand(rows, sections, aliases=None, additional=(), reserve=0):
    """Compare an explicit name scenario with the immutable 216..252 pool.

    Aliases are unapproved planning input, not automatic geographic grouping.
    An existing Sinnoh name cannot be regrouped or expanded to a different
    registered area; that would change the meaning of its saved origin.
    """
    areas = _areas(rows)
    if aliases is None:
        aliases = {}
    if not isinstance(aliases, dict) or set(aliases) - set(areas):
        raise ValueError("aliases must be an object keyed only by registered areas")
    if not isinstance(additional, (list, tuple)):
        raise ValueError("additional origins must be a list of explicit names")
    if type(reserve) is not int or reserve < 0:
        raise ValueError("reserve must be a nonnegative integer")
    if not isinstance(sections, (list, tuple)):
        raise ValueError("sections must be a list")
    used, identifiers, frozen, legacy_names = set(), set(), {}, {}
    for section in sections:
        if not isinstance(section, dict):
            raise ValueError("section must be an object")
        value, ident = section.get("value"), section.get("id")
        if type(value) is not int or not 0 <= value <= LAST_ORDINARY or value == NONE:
            raise ValueError("named section uses NONE, a special code, or an invalid byte value")
        if (not isinstance(ident, str) or not ident or ident in {"MAPSEC_NONE", "MAPSEC_COUNT"}
                or ident in identifiers or value in used):
            raise ValueError("duplicate or missing section identity/value")
        identifiers.add(ident)
        used.add(value)
        # MAPSEC_DYNAMIC has no static JSON label. Its legacy value remains
        # occupied; an absent label is never permission to recycle its code.
        if value < NONE and section.get("name") is None and section.get("region") != SINNOH:
            continue
        key = name_key(section.get("name"))
        if section.get("region") == SINNOH:
            if key in frozen:
                raise ValueError("ambiguous existing Sinnoh origin name; explicit identity policy needed")
            frozen[key] = dict(section)
        else:
            legacy_names.setdefault(key, []).append(ident)
    proposed = {}
    members = {}
    for area, original in areas.items():
        original_key = name_key(original)
        target = aliases.get(area, original)
        key = name_key(target)
        if original_key in frozen and key != original_key:
            raise ValueError(f"{area}: cannot regroup an existing saved Sinnoh origin")
        if key in frozen and key != original_key:
            raise ValueError(f"{area}: cannot expand another existing saved Sinnoh origin")
        proposed.setdefault(key, target.strip())
        members.setdefault(key, []).append(area)
    for name in additional:
        proposed.setdefault(name_key(name), name.strip())
    existing = sorted(set(proposed) & set(frozen))
    new = sorted(set(proposed) - set(frozen))
    free = sorted(set(range(FIRST_NEW, LAST_ORDINARY + 1)) - used)
    required = len(new) + reserve
    collisions = [dict(name=proposed[key], legacy_ids=sorted(legacy_names[key]))
                  for key in sorted(set(proposed) & set(legacy_names))]
    return {
        "scope": "Planning scenario only; not approval or a complete child/Averon inventory",
        "registered_areas": len(areas),
        "distinct_proposed_names": len(proposed),
        "already_allocated_sinnoh_names": [dict(id=frozen[key]["id"], value=frozen[key]["value"],
                                               name=frozen[key]["name"]) for key in existing],
        "new_names_required": len(new),
        "new_names": [proposed[key] for key in new],
        "remaining_ordinary_codes": len(free),
        "available_values": free,
        "other_future_reserve": reserve,
        "codes_required_with_reserve": required,
        "shortfall": max(0, required - len(free)),
        "fits_current_byte_pool": required <= len(free),
        "name_groups": [dict(name=proposed[key], area_keys=sorted(members.get(key, [])))
                        for key in sorted(proposed)],
        "legacy_same_name_not_reused": collisions,
        "inventory_complete": False,
        "production_allocations": [],
    }
