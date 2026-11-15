# Throw a Toy

A spinoff of Throw Food for Animals: throw toys down a 6-zone canyon, lure animals, fill your plot, get rich.

## Open it
Open `ThrowAToy.rbxlx` in Roblox Studio and press Play. Everything is inside: map, 22 animals + 9 toys, scripts, UI, VFX.

## Setup
Studs (Roblox stud texture 10509831729) and all 17 sounds (uploaded to your account) are already wired in via `assets.json`.
New sounds can take a few minutes to pass Roblox moderation before they play.
1. **Saving**: Game Settings > Security > Enable Studio Access to API Services (to test saving in Studio).
2. **Robux shop** (the Shop button; the Noob's stall is the toy shop): create these on the Creator Dashboard and paste
   each id into `Config.Shop` (`Id = 0` buttons say "Not for sale yet"). Keep the Robux numbers equal to the dashboard prices.
   - Developer products: Enchanted Egg x1/x3/x10 (6 egg-only Exclusive pets, see `Config.Exclusives`), Rainbow Egg x1/x3,
     Cash packs 1-4 (the bigger of 10 min / 1 h / 6 h / 24 h of income or 25% / 1x / 3x / 10x the cash you hold).
   - Game passes: x2 Cash, x2 Training Power.
   - Optional: `LuckProductId` (100x luck, 15 min) shows a HUD button once set.

## Gameplay
- Stand on the orange pad, tap when the meter is high: green top = PERFECT (+1% power).
- Farther throws reach later zones and higher luck. Luck = distance x toy x boost.
- Rarity: Common > Uncommon > Rare > Epic > Legendary > Mythic. Sizes: Big/Large/Huge. Mutations: Golden/Rainbow/Cosmic.
- Train on your plot's pull-up bar for power. Upgrade the bar (pad) and plot slots (sign) with cash.
- Index: complete a zone for +10% income. Animals earn offline (50%, up to 8h).

## Edit
| What | Where |
|---|---|
| Balance (prices, luck, zones, odds) | `src/shared/Config.luau` |
| Server logic | `src/server/GameServer.server.luau` |
| UI, throw camera, VFX | `src/client/GameClient.client.luau` |
| Animal/toy models | `blender/pets.py` + `blender/build_pets.py` (run in Blender, writes `build/models.json`, FBX, renders) |
| Map | `tools/build_place.py` |
| Sounds | `tools/make_sounds.py` |

Rebuild after editing: `python tools/build_place.py` (models: run the Blender script first).
