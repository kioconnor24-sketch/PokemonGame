#!/usr/bin/env python3
"""Maniac Tunnel -> Solaceon Ruins link (W19): the dug tunnel off Route 214 reaches the ruins' depths, as in DS.

OFF-ENGINE staging joining two Claude batches: W13's ManiacTunnel (one dug-out room behind Route 214's cliff mouth)
and W15's Solaceon Ruins network. Both are re-staged with exactly one new ladder cell and one appended warp:
ManiacTunnel gets a Granite Cave down-ladder at (16, 4), SolaceonRuins_B2F_East an up-ladder at (24, 16). Between
them, a new ManiacTunnel_B1F (56 x 16, W1 cave kit, General + Cave): a long dug passage with four rock outcrops and
an up-ladder at each end. No objects, Unown condition, story or sections (MAPSEC_PENDING_OWNER).

  build_maniac_ruins_link.py --engine ENGINE --out DIR
"""
import argparse
import importlib.util
import json
import pathlib
import struct

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


w13 = load("w13", SINNOH / "sendoff-spring/build_sendoff_spring.py")
w15 = load("w15", SINNOH / "solaceon-depths/build_solaceon_depths.py")
w1 = w15.w1
TUNNEL_LADDER = (16, 4)
RUINS_LADDER = (24, 16)
PASSAGE_W, PASSAGE_H = 56, 16
PASSAGE_ENDS = {"tunnel": (5, 4), "ruins": (50, 11)}


def passage(eng):
    cv = w1.Cave(eng, PASSAGE_W, PASSAGE_H)
    cv.room(3, 3, 52, 12)
    for x0 in (10, 21, 32, 43):
        cv.block(x0, 5, x0 + 5, 10)
    for x, y in PASSAGE_ENDS.values():
        cv.ladder(x, y, eng, down=False)
    return cv


def add_ladder(eng, cells, width, at, down):
    x, y = at
    assert cells[y * width + x] & 1023 == 513 and not cells[y * width + x] & 0xC00, at       # plain cave floor
    assert all(not cells[(y + dy) * width + x + dx] & 0xC00 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))), at
    out = list(cells)
    out[y * width + x] = eng.word("GraniteCave_1F", 17, 11, 575) if down else eng.word("GraniteCave_B1F", 4, 21, 573)
    return out


def build(engine_root):
    eng, _, w13maps, _, _ = w13.build(engine_root)
    _, w15maps, w15layouts = w15.build(engine_root)
    t_hdr, (t_cells, t_w, t_h, *_) = w13maps["ManiacTunnel"]
    r_hdr = w15maps["SolaceonRuins_B2F_East"]
    r_cells, r_w, r_h = w15layouts["SolaceonRuins_B2F_East"]
    t_hdr, r_hdr = json.loads(json.dumps(t_hdr)), json.loads(json.dumps(r_hdr))
    ti, ri = len(t_hdr["warp_events"]), len(r_hdr["warp_events"])
    t_hdr["warp_events"].append({"x": TUNNEL_LADDER[0], "y": TUNNEL_LADDER[1], "elevation": 0,
                                 "dest_map": "MAP_MANIAC_TUNNEL_B1F", "dest_warp_id": "0"})
    r_hdr["warp_events"].append({"x": RUINS_LADDER[0], "y": RUINS_LADDER[1], "elevation": 0,
                                 "dest_map": "MAP_MANIAC_TUNNEL_B1F", "dest_warp_id": "1"})
    cv = passage(eng)
    p_hdr = w1.header("MAP_MANIAC_TUNNEL_B1F", "ManiacTunnel_B1F", "LAYOUT_MANIAC_TUNNEL_B1F", w15.MUSIC,
                      "MAP_TYPE_UNDERGROUND", [(*PASSAGE_ENDS["tunnel"], "MAP_MANIAC_TUNNEL", ti),
                                               (*PASSAGE_ENDS["ruins"], "MAP_SOLACEON_RUINS_B2F_EAST", ri)])
    return eng, {"ManiacTunnel": (t_hdr, (add_ladder(eng, t_cells, t_w, TUNNEL_LADDER, True), t_w, t_h)),
                 "SolaceonRuins_B2F_East": (r_hdr, (add_ladder(eng, r_cells, r_w, RUINS_LADDER, False), r_w, r_h)),
                 "ManiacTunnel_B1F": (p_hdr, (cv.cells, cv.w, cv.h))}


def check(maps):
    """The two new ladder pairs are reciprocal (warp index for warp index)."""
    by_id = {h["id"]: h for h, _ in maps.values()}
    for mid, h in by_id.items():
        for i, w in enumerate(h["warp_events"]):
            if w["dest_map"] in by_id and w["dest_map"] != mid:
                back = by_id[w["dest_map"]]["warp_events"][int(w["dest_warp_id"])]
                assert (back["dest_map"], int(back["dest_warp_id"])) == (mid, i), (mid, i, w, back)
    return True


def write(engine_root, out):
    eng, maps = build(engine_root)
    check(maps)
    out = pathlib.Path(out)
    bank = w1.render.Bank(eng.root / "data/tilesets/primary/general", eng.root / "data/tilesets/secondary/cave")
    border = struct.pack("<4H", *[w1.Cave(eng, 1, 1).k[529]] * 4)
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "maps": {}}
    for name, (hdr, (cells, w, h)) in maps.items():
        d = out / "staged" / name
        d.mkdir(parents=True, exist_ok=True)
        data = struct.pack("<%dH" % len(cells), *cells)
        (d / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
        (d / "scripts.inc").write_text(w1.scripts(name))
        (d / "map.bin").write_bytes(data)
        (d / "border.bin").write_bytes(border)
        (d / "layout.json").write_text(json.dumps({"id": hdr["layout"], "name": name + "_Layout", "width": w,
                                                   "height": h, "primary_tileset": "gTileset_General",
                                                   "secondary_tileset": "gTileset_Cave"}, indent=2) + "\n")
        w1.render.render_cells(bank, cells, w, d / "preview.png")
        receipt["maps"][name] = {"map_sha256": w1.sha(data), "warps": len(hdr["warp_events"])}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(write(a.engine, a.out)["status"])
