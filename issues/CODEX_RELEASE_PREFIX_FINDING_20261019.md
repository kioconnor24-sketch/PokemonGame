# v1.0 archive: bounded prefix provenance finding

Codex, 2026-10-19; read-only follow-up to merged #164. **No release, tag, asset, branch or historical evidence changed/deleted.** This is metadata evidence, not an artifact distribution or legal conclusion.

## Confirmed new facts

Both API/public-browser HTTP Range attempts returned501. A different approach succeeds: ordinary public GET, read **exactly65,536 bytes**, then close the response without downloading the745,541,366-byte archive. HTTP200 reports that full Content-Length. The observed prefix starts with ZIP local-header signature `PK\x03\x04`; prefix SHA256 is **`ba94cf3d11ab7ed83446e860e4dfea865922cd04fb3a3f5ef518c53dc655ab9f`**.

[Metadata receipt](CODEX_RELEASE_PREFIX_METADATA_20261019.json) identifies **49 local file headers** within this prefix, including `Pokemon Game/.git/`, `.git/config`, `.git/HEAD`, `.git/index`, hooks, logs and objects. Parsing stops at the bounded prefix/decompression limit; the final member's data is incomplete. Thus the public asset demonstrably includes Git working-copy metadata. This does **not** establish that the entire ZIP is source-only, contains a complete game ROM, contains credentials, or is free of either.

To advance past local entries with data-descriptor flag8, the inspection used bounded in-memory raw-deflate decoding solely to locate/validate descriptors (compressed/uncompressed lengths and CRC). At most65,537 output bytes per member,524,288 total and256 entries were allowed; incomplete streams stop inspection. Member text/content was not displayed, stored, extracted to filesystem or published. The committed JSON contains only local names, sizes/method/descriptor status and the prefix hash. No ZIP payload, ROM, private save or credential is uploaded.

## Reproduce the network boundary

This standard-library request reads only the prefix; do not use an unbounded response.read():

```python
import hashlib, urllib.request
url = 'https://github.com/kioconnor24-sketch/PokemonGame/releases/download/v1.0/Pokemon.Game.zip'
with urllib.request.urlopen(url, timeout=30) as response:
    prefix = response.read(65536)
assert len(prefix) == 65536
assert prefix.startswith(b'PK\x03\x04')
print(hashlib.sha256(prefix).hexdigest())
```

For metadata parsing: read30-byte `<4sHHHHHIIIHH` local headers; bound filename/extra lengths; for known sizes skip compressed bytes; for method8/flag8 locate bounded inflater EOF, then verify the12-byte descriptor (optional4-byte `PK\x07\x08` signature) before advancing. Stop on encryption, unsupported codec/ZIP64, truncated descriptor, CRC mismatch or either bound. Never extract a filename as a filesystem path. This was a bounded inspection of this artifact, not a new general ZIP security validator.

Receipt validation actually run:65,536 bytes/hash as above,49 entries matching the JSON count, expected config/HEAD/index names present; JSON member fields limited to metadata, no content payload. `git diff --check` PASS. No gameplay/native/build test is relevant to this R0 evidence-only PR.

## Remaining uncertainty and recommendation

The public v1.0 release still pins pre-M1 commit `97aa51dc2c282c5c3f933f13d94411fa4a706a90`, published2026-10-14; it is not this session's tested M1/Sinnoh build. Prior API metadata: release413284705, asset642074913, API whole-asset digest `568e9022eb134aa9ef23f8a54a4a049d2d435a49c2302169ab7c2799739fe848`. That digest is **not independently verified** here. Full central directory, complete contents, rights and secret absence remain unverified; no whole-archive claim follows from a prefix.

Recommend an eventual deliberately audited source/patch export excluding VCS working-copy metadata, with explicit source/build purpose and provenance. Keep existing release/history unchanged until the **owner** decides retain/relabel/restrict/replace and the remaining content/rights inspection is complete. Do not present v1.0 as a verified current game release or remove inherited binaries merely because they are binary. This receipt partially resolves the earlier metadata-access limitation, not the entire distribution review.
