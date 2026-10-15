# Observed upstream findings (M0; static inspection only)

Pinned source: `73b3fbeb574327cd9420c89e56bef5aa3c08fead`.
None of these observations is a runtime pass.

| Source | Observed default | Implication |
|---|---|---|
| include/config/caps.h | B_EXP_CAP_TYPE = EXP_CAP_NONE; B_LEVEL_CAP_TYPE = LEVEL_CAP_NONE; B_RARE_CANDY_CAP = FALSE | Averon hard caps are not enabled |
| include/config/item.h | I_EXP_SHARE_ITEM = GEN_5; I_EXP_SHARE_FLAG = 0 | Candidate held-item behavior; test all party slots in M2 |
| include/config/overworld.h | OW_POKEMON_OBJECT_EVENTS = TRUE; OW_FOLLOWERS_ENABLED = FALSE | Followers need enabling and script/collision tests in M1 |
| include/config/species_enabled.h | P_GEN_1_POKEMON through P_GEN_9_POKEMON = TRUE | Configuration presence only; not a complete species/form/obtainability audit |
| same | P_MEGA_EVOLUTIONS, P_PRIMAL_REVERSIONS, P_ULTRA_BURST_FORMS, P_GIGANTAMAX_FORMS, P_TERA_FORMS = TRUE | Untouched base differs from Averon requirements; explicit mechanics restrictions needed in M2 |
| include/config/battle.h | B_FLAG_DYNAMAX_BATTLE = 0; B_FLAG_TERA_ORB_CHARGED = 0; B_TERA_ORB_ALWAYS_CHARGED = FALSE | Does not establish that every access path is disabled |
| include/config/general.h | GEN_LATEST = GEN_9 | Generation default is not coverage proof |

Native script example in `data/maps/Route103/scripts.inc`:

```asm
Route103_EventScript_StartMayBattleTreecko::
    trainerbattle_no_intro TRAINER_MAY_ROUTE_103_TREECKO, Route103_Text_MayDefeated
    goto Route103_EventScript_AfterMayBattle
    end
```

The same file uses `map_script MAP_SCRIPT_ON_TRANSITION`, `lockall`,
`switch VAR_STARTER_MON`, `case`, `msgbox`, `applymovement`, `waitmovement`.
These are observed patterns, not a proposed Saltmere script or reserved IDs.

## Build/provenance inspection

INSTALL.md documents `make`, parallel `make -jN`, and `pokeemerald.gba` output.
Makefile defaults to Emerald, `all: rom`, `COMPARE ?= 0`, and arm-none-eabi tools.
The ordinary documented build does not ask for a retail ROM. A targeted search
found no `baserom` dependency, but found bundled multiboot binaries
`data/mb_berry_fix.gba`, `data/mb_ereader.gba`, and `data/mb_colosseum.gba`.
Their presence is not a compiled game from this session. Full prerequisite and
asset-rights review remains open. No external retail ROM was obtained.
README asks for RHH attribution and references CREDITS.md; public source access
does not establish redistribution rights. Keep generated ROMs local and ignored.

Both MSYS2.md and CYGWIN.md explicitly state current Expansion builds do not
work there. WSL.md recommends WSL2 with sources on the Linux filesystem,
or WSL1 for Windows filesystem sources. Preserve this checkout; if WSL2 is
used, create a build checkout at the same pin inside Linux and record its path.
