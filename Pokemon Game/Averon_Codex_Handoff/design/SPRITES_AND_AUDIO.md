# Art, sprites, music and asset permissions

## Visual direction
Game Boy Advance-quality 2D pixel-art with a cohesive perspective and disciplined palettes. Newly drawn maps must look like a premium Emerald-era Pokémon region, never pasted high-resolution screenshots or off-style sprites. Distinct environments include stone seaside ports, bright forests, river waterfalls, dry sandstone markets, northern timber towns and southern volcanic resorts. All settlements receive day-to-day activity and architecture matching geography.

## Asset inventory and rights ledger
For every imported tileset, Pokémon sprite, overworld sprite, Pokémon icon, overworld follower, trainer sprite, sound effect or song, create `asset_id`, source URL, author, specific license or written reuse permission, transformation and file path, credits line, compatibility tests, date acquired. Maintain this record inside the engine repository; the design packet itself ships no community Pokémon art.

## Reuse workflow
1. Prefer assets already present in the pinned `pokeemerald-expansion` revision and check their usage conditions.
2. Reuse community Pokémon assets only after reading the artist's actual license/permission; credit appropriately. The art appearing on GitHub or in a fan hack does NOT imply permission to copy it.
3. Normalize palette, frames and dimensions to the engine's real requirements; do not promise automatic full Gen IX animations just because static PNGs exist.
4. Test battle frame, back frame, shiny color, menu icon, follower orientation, collisions and camera transitions for each class of newly imported asset.
5. Export a screen montage of Averon's tiles and characters before 'art done'.

## Trainer friends from real photographs
No photographs are included yet. Only accept images voluntarily provided by the user with permission to use the likenesses. For each friend: keep the defining hairstyle/clothing/general silhouette; create an original Pokémon-style full battle sprite and four-direction overworld walk sheet as needed, using the validated engine asset dimensions/palette. Test them in battle and field. Avoid using unapproved photographs publicly in project issues or GitHub repos. Do not infer a character's personal traits from their photo.

## Music
Original tracks or explicitly licensable arrangements are best for distribution. Cynthia should have a recognizable *dramatic Champion encounter*, but copying the copyrighted composition or recording is not automatically legal. Only include her exact existing theme if usage rights are established; otherwise commission an original energetic theme with separate melodic material. Red gets an original final challenge arrangement unless similarly cleared. Avoid large compressed sound files that exceed hardware ROM and audio budgets.

## Consistency review
Sprites fit the same visual perspective as tile art; no clashing outlines; avoid neon/black-on-black accessibility; facial expressions restrained; NPC overworld identifiers track script references; music transitions tested entering homes, Gyms, shops, ferries and key boss scenes. Keep natural ambient route soundscapes and bright music for most of the game.
