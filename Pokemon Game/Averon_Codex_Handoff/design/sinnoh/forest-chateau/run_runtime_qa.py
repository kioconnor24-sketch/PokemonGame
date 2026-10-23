#!/usr/bin/env python3
"""Run existing QA with this branch's actual driver against verified DEV source.

_wrapper(engine) otherwise imports the older scratch-tree driver. Preload the
tested source module explicitly; no engine/map/memory or controller edits here.
All other arguments are passed to existing map_qa run unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def validate_source(engine,recipe):
    engine=Path(engine).resolve()
    if recipe['status']!='DEV_ONLY_NOT_PRODUCTION_OR_SAVED_ORIGIN_ACCEPTANCE' or not (engine/'.map_qa_throwaway').is_file():
        raise ValueError('marked DEV source required')
    for path,expected in recipe['files'].items():
        target=(engine/path).resolve()
        if not target.is_relative_to(engine) or hashlib.sha256(target.read_bytes()).hexdigest()!=expected:
            raise ValueError('runtime source differs: '+path)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    p.add_argument('--engine',type=Path,required=True);p.add_argument('--recipe',type=Path,required=True)
    args,rest=p.parse_known_args(argv);validate_source(args.engine,json.loads(args.recipe.read_text()))
    scripts=Path(__file__).resolve().parent.parents[3]/'scripts/claude_play'
    sys.path.insert(0,str(scripts))
    import driver
    import map_qa
    wrapper=map_qa._wrapper(args.engine)
    if wrapper.driver is not driver or Path(driver.__file__).resolve()!=(scripts/'driver.py').resolve():
        raise ValueError('QA loaded a different driver')
    for module in (map_qa,driver):
        path=Path(module.__file__);print('QA source',str(path),hashlib.sha256(path.read_bytes()).hexdigest(),flush=True)
    return map_qa.main(['run','--engine',str(args.engine),*rest])


if __name__=='__main__':sys.exit(main())
