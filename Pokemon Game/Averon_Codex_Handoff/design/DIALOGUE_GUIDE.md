# Pokémon Averon — Dialogue director's guide

> **STORY DRAFT NOTE — 2026-10-17:** This is a tonal **example book**, not final dialogue. Example 16 (rigged Gym match records) and related Vale/Renn motives are **earlier proposals now disputed**. Latest owner thinking favors a **genuine Gym loss**, a later mistaken player suspicion and honest villain clarification, an independently motivated antagonist (motivation before Threshold), personal mentorship and private succession, while redemption details remain on hold. The villain's Sinnoh Arceus Plates/control-device continuation is only provisional. See [multi-session working story dossier](STORY_DEVELOPMENT_WORKING_DOSSIER_20261017.md). Preserve short, organic Pokémon dialogue and do not drop old lines into a live script verbatim.


This game should sound like a **good official Pokémon adventure**, not a grim visual novel and not a chat bot summarizing themes. The writing below is an ORIGINAL tonal sample. Do not copy dialogue from published Pokémon games. Names are provisional (Renn = childhood rival; Mira = easygoing rival; Calder = detective; Tavi = young researcher; Vale = villain leader).

## The voice test
- People speak **about things directly in front of them**. A farmer talks about their Berries and muddy boots, not 'the bond between humanity and nature.' A fisherman complains about losing bait. A trainer wants to battle because it's fun.
- A Pokémon NPC can be silly without winking at the audience. Keep distinctive speech patterns subtle; no wall of quirky catchphrases.
- No mystical prophecy or ominous non sequitur in a normal market stall. **Most scenes have absolutely no conspiratorial relevance.** Do not attach a suspicious government file to every side quest.
- Rival: friendly, competitive, sometimes impatient, occasionally quietly proud. Avoid repeating 'I'm better than you' or speeches about strength. His change appears through missed meetups, changed priorities, small choices in Pokémon care—not tearful monologues.
- Detective: competent, makes mistakes, listens to the player, doesn't magically solve clues the player hasn't investigated. Humor can come from being overprepared for ordinary inconveniences.
- Villains: low-rank grunts sometimes petty, ridiculous and greedy, like familiar Pokémon criminals. Some mid-ranks businesslike and efficient. Vale speaks calmly and sparsely; he has made an appalling choice and needn't explain it every five minutes.
- The player isn't simply an audience member in cutscenes. Prefer searchable rooms, short tasks, interrupted dialogue, active choices with small responses, and battles.
- Never put an 8-box philosophical explanation on a normal route. Major revelations get the longest scenes, but still involve actions, interruptions, and a memorable image rather than just talk.

## Text box budgets (suggestions, not hard engine specs)
- Normal NPC: 1–2 boxes, often with local flavor only.
- Friendly trainer: brief invitation before battle, playful or gracious line after.
- Rival meeting: normally 2–5 boxes and a battle or a small interaction; major reveal 6–10 if needed.
- Hidden clue: one tactile discovery and one short comment; explanation later or optional.
- Government transition: exactly two *mandatory* concise aftermath windows, mostly visible environmental changes and 2–3 distinct NPC lines each.
- Long explanations get a readable optional notebook/research terminal, not forced repeated speeches.
- Check per-box character widths and line lengths against **actual text engine font**. The examples here are prose to adapt to the real box engine, not preformatted script data.

## The six specific pitfalls to remove in edit passes
1. Generic grand claims: 'The balance of the world hangs in the balance' / 'Everything changes tonight.'
2. Exposition overtells: 'As you know, the government has controlled the region for decades...'
3. Everyone delivers rhyming, portentous aphorisms: 'Truth has a cost.' / 'Power reveals our nature.'
4. Repeated confession scenes where all characters describe why they became who they are.
5. Every local shopkeeper sharing an opinion about Team Vantage.
6. A forced emotional beat after every gym, cave, capture or side quest.

## Example 01 — Morning in Saltmere (no plot foreshadowing)
*Pip sits beside an opened tackle box.*

**Pip:** "Don't step on that screw. I dropped it somewhere."

**Player interacts with tackle box.**

**Pip:** "There it is! I was about to blame Wingull again."

*Pip pockets the screw and wanders off. No follow-up investigation.*

## Example 02 — Opening greenhouse (first meaningful household visit)
**Greenhouse keeper:** "Mind carrying that tray over? The little ones keep stealing the good light."

*Player carries a tray to the sun-facing bench; `STARTER_FIRST_HOUSE=GREENHOUSE` if unset. The other two household errands can still be done.*

**Keeper:** "Perfect. That's a lot better."

## Example 03 — First normal rival battle
**Renn:** "We made it farther than the pier. That's progress."

**Renn:** "All right, one battle before we go?"

*After battle, if player wins:*

**Renn:** "Okay, okay. I should've seen that coming."

*If Renn wins:*

**Renn:** "Ha! You picked a bad time to try that move."

**Renn:** "See you at the next town."

## Example 04 — Mira's normal sidestory
**Mira:** "I came up here for a rare Pokémon."

**Mira:** "Found six identical Geodude instead."

**Mira:** "Want to take the long way back? There's a better view."

*The optional trail contains a funny trainer, a scenic overlook and an item. No device clue.*

## Example 05 — Breakwater fisherman
**Fisherman:** "The big one got away. Again."

**Fisherman:** "At this point, I think it knows my schedule."

*Player can join fishing derby.*

## Example 06 — Recurring Vantage grunt's petty crime
**Kit:** "Hey! That's my cart."

**Player examines obviously stolen goods.**

**Kit:** "Fine. It's somebody's cart."

**Kit:** "You really going to make a thing out of this?"

*Short ordinary grunt battle; cart returned to owner. This event is NOT secretly part of Threshold.*

## Example 07 — Renn after another failed Slateford Gym challenge
**Renn:** "Again."

**Player choice:** "Tough match?" / "Want a battle?"

**Renn:** "Dorian's good. He had an answer for everything."

**Renn:** "I need to try something different."

*He leaves; scene is quiet. Don't add music sting or a long stare at his Poké Ball.*

## Example 08 — Helpful Dorian, no theatrical villain clue
**Dorian:** "Aster's men took the mine lift."

**Dorian:** "I can get us through the other entrance. You handle the trainers."

*Dorian assists in a normal short dungeon encounter. Aster can remark "You picked a strange time to help" but not announce their shared allegiance. Later we learn Dorian used the player to remove a personal rival for influence.*

## Example 09 — Nadia Gym 5 twist (brief, sharp)
*Badge received. Player party HP unchanged.*

**Nadia:** "Good match."

*She closes the gym gate and sends out another Pokémon.*

**Nadia:** "One more, then. No rules this time."

*Two-Pokémon hostile battle starts immediately. No healing. If player loses, badge/progress are retained and the story continues.*

## Example 10 — Tavi and Calder investigate together
**Tavi:** "This isn't a machine part. It's a plan for the whole room."

**Calder:** "Could be an old government facility."

**Player searches cabinet and finds a second document bearing an official seal.**

**Calder:** "There. That tells us where to ask."

*The player physically discovers decisive evidence; the detective doesn't solve everything for them.*

## Example 11 — Renn reveals allegiance
*Player encounters Renn at a restricted roadblock.*

**Player's friend Mira:** "Renn? What are you doing here?"

**Renn:** "Working."

**Mira:** "For them?"

**Renn:** "Yeah."

**Renn:** "You should head back."

*Battle begins. Scripted loss; wake at Center without losing money or Nuzlocke teammates. Do not write six more pages of explanation.*

## Example 12 — Coup broadcast, short
**Station speaker:** "The regional council has been dissolved."

**Speaker:** "Government services will continue under the interim administration."

*Outside, the same vendors still sell food. Guards wear different coats. A commuter complains the platform number changed. No montage of screaming citizens.*

## Example 13 — Two post-coup reactions (mandatory window one)
**Vesper rail worker:** "First train to Frostmere in months. About time."

**Office clerk:** "I don't like who gave the order. But at least somebody signed it."

**Another resident:** "They took my neighbor's Growlithe. Said it was an inspection."

*Exit to next Gym remains open.*

## Example 14 — Post-coup reaction (mandatory window two)
**Gullhaven dockworker:** "The new engines are quieter."

**Passenger:** "Not sure the old ferry crews are enjoying it."

*Player can continue to Ashfall immediately. No speech on policy.*

## Example 15 — Old Threshold witness
**Dr. Quill:** "I signed the shutdown order."

**Calder:** "But you kept the machine?"

**Quill:** "I argued against it. Not loudly enough, apparently."

*Player places retrieved diagram on table. Quill notices a mark the thieves made.*

**Quill:** "That's new. That part wasn't in our design."

## Example 16 — Discovering the rigged matches (before final assault)
**Mira:** "These teams don't match the public Gym record."

**Player examines Dorian's private match notes.**

**Calder:** "Every time Renn changed a Pokémon, Dorian changed his counter."

**Mira:** "We should tell him."

*Renn may dismiss evidence first, without an instant moral reversal.*

## Example 17 — The device secret, reserved for very late
**Quill:** "Threshold could drain a Pokémon's power for a few moments. That was the point."

**Quill:** "Then the filter failed."

*Show original test footage or lab schematic, not just seven lines describing it.*

**Quill:** "The test Pokémon didn't survive."

**Calder:** "And Vale was there?"

**Quill:** "He saw everything."

*Player's own later evidence reveals how the lethal feedback would be amplified.*

## Example 18 — Vale after the reveal
**Vale:** "You saw the new rail line. The hospital equipment."

**Vale:** "We did what we said we would."

**Player/ally:** "And this?"

**Vale:** "This is where it ends."

*Leave his moral rationale to fewer than ten concise lines across the whole climactic sequence. Do not make him gloat about Pokémon dying.*

## Example 19 — Gauntlet ally heal
*After tenth one-Pokémon battle, ally arrives from side hall.*

**Sera:** "You're still standing? Good."

**Sera:** "Hold still. I've got supplies."

*Party fully healed. A route onward opens.*

**Sera:** "They're waiting upstairs."

## Example 20 — The alternate dimension
*Quiet, broken paths and no immediate explanation. On reaching the leader:*

**Vale:** "So it works here, too."

*He notices the player's Pokémon survive in the ambient environment. This is not the focused lethal feedback pulse.*

**Vale:** "...No. Not the way I planned."

*Final battle begins. No multi-page cosmology lecture.*

## Example 21 — Sinnoh Renn follow-up
**Renn:** "Didn't expect to see you here."

**Renn:** "They've got a good training hill past the bridge. Want to try it?"

*Player can accept rematch or decline. Keep tone ordinary.*

## Example 22 — The final summit
*Red stands facing the mountain view.*

*Player approaches. Red turns.*

**Red:** "..."

*Battle starts. This is the final canonical trainer test, with no lengthy explanation or ominous prophecy.*

## Revision protocol for every scene
- Read all dialogue aloud. If every character sounds like the same polished adult, rewrite.
- Replace abstract nouns with concrete objects or actions where possible.
- Delete any line that repeats information shown on screen or stated before.
- Remove one in three 'meaningful' lines from serious scenes on first revision.
- Give ordinary NPCs non-plot lives and practical concerns.
- Verify every joke fits the speaker and doesn't trivialize deaths or the late crisis.
- Compare with the atmosphere of traditional Pokémon games, without copying copyrighted game dialogue.
