#ifndef JSONPROC_MAP_SECTIONS_H
#define JSONPROC_MAP_SECTIONS_H

#include <fstream>
#include <regex>
#include <set>
#include <stdexcept>
#include "nlohmann/json.hpp"

// Validate before rendering either section template; never edit source JSON.
inline void prepare_map_sections(nlohmann::json &data, const std::string &input)
{
    using json = nlohmann::json;
    if (!data.is_object() || !data.contains("map_sections"))
        return;
    auto fail = [](const std::string &why) { throw std::runtime_error("map sections: " + why); };
    const unsigned none = 215, first_special = 253, max_section = 8191;
    const unsigned max_entries = max_section + 1 - 4; // NONE and three met specials stay holes.
    const auto slash = input.find_last_of("/\\");
    const auto baseline_path = input.substr(0, slash == std::string::npos ? 0 : slash + 1)
        + "region_map_sections.legacy.json";
    std::ifstream baseline_file(baseline_path);
    if (!baseline_file)
        fail("missing frozen legacy manifest: " + baseline_path);
    json baseline;
    baseline_file >> baseline;
    auto &entries = data.at("map_sections");
    if (!baseline.is_array() || baseline.size() != none)
        fail("legacy manifest must contain exactly 215 entries");
    if (!entries.is_array() || entries.size() < none || entries.size() > max_entries)
        fail("expected 215 legacy entries and at most 8188 total named sections");
    const std::set<std::string> regions = {"REGION_NONE", "REGION_KANTO", "REGION_JOHTO", "REGION_HOENN",
        "REGION_SINNOH", "REGION_UNOVA", "REGION_KALOS", "REGION_ALOLA", "REGION_GALAR", "REGION_HISUI", "REGION_PALDEA"};
    std::set<std::string> identifiers;
    for (unsigned i = 0; i < entries.size(); ++i)
    {
        auto &entry = entries.at(i);
        if (!entry.is_object() || !entry.contains("id") || !entry.at("id").is_string()
            || (entry.contains("name") && !entry.at("name").is_string()))
            fail("each entry needs a symbolic id and valid name");
        const std::string id = entry.at("id");
        if (!std::regex_match(id, std::regex("MAPSEC_[A-Z0-9_]+")) || id == "MAPSEC_NONE" || id == "MAPSEC_COUNT"
            || !identifiers.insert(id).second)
            fail("invalid, reserved or duplicate identifier: " + id);
        // Append through the old byte pool, then skip the three exact specials.
        // This retains every previous value and never assigns 215/253/254/255.
        const unsigned value = i < none ? i : i < first_special - 1 ? i + 1 : i + 4;
        if (entry.contains("value") && (!entry.at("value").is_number_integer()
            || entry.at("value").get<long long>() != value))
            fail(id + ": duplicate, sparse, reserved or moved value (expected " + std::to_string(value) + ")");
        if (i < none)
        {
            const auto &old = baseline.at(i);
            if (old.at("value") != i || entry.at("id") != old.at("id") || entry.value("name", json()) != old.at("name")
                || entry.contains("region"))
                fail(id + ": legacy value, name or region changed");
        }
        else if (!entry.contains("value") || !entry.contains("region") || entry.at("region") == "REGION_NONE"
            || !entry.contains("name") || entry.at("name").get<std::string>().empty())
            fail(id + ": new section requires explicit value and engine region");
        if (entry.contains("region") && (!entry.at("region").is_string()
            || !regions.count(entry.at("region").get<std::string>())))
            fail(id + ": invalid region metadata");
        entry["value"] = value;
    }
    data["mapsec_none"] = none;
    data["mapsec_count"] = entries.size() == none ? none + 1
        : entries.back().at("value").get<unsigned>() + 1;
}
#endif
