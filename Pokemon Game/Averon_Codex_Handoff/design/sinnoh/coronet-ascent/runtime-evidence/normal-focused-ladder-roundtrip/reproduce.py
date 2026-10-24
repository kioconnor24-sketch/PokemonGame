"""Focused ordinary-input replay; THREE maps, not full six-map acceptance."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
root=Path('/workspace/averon-oreburgh-geography/Pokemon Game/Averon_Codex_Handoff/design/sinnoh/coronet-ascent')
s=importlib.util.spec_from_file_location('ascent_focused',root/'run_runtime_qa.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.MAPS=('MAP_SINNOH_MT_CORONET_OUTSIDE_NORTH','MAP_SINNOH_MT_CORONET_4F_ROOM_3','MAP_SINNOH_MT_CORONET_4F_ROOMS_1_AND_2')
raise SystemExit(m.run(SimpleNamespace(engine=Path('/workspace/averon-corridor-scratch/Pokemon Game/engine'),rom=Path('/workspace/averon-corridor-scratch/Pokemon Game/engine/pokeemerald.gba'),scratch=Path('/workspace/scratch/ascent-six-normal-ladder-roundtrip'),out=Path('/workspace/averon-session-evidence/ascent-six-normal-ladder-roundtrip'),profile='normal',recipe=Path('/workspace/averon-session-evidence/ascent-six-installed-recipe.json'),expect=None)))
