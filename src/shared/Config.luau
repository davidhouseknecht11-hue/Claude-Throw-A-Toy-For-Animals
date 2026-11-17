-- Throw a Toy: all game tuning in one place. Shared by server and client.
local Config = {}

Config.Rarities = {
	{ Name = "Common", Color = Color3.fromRGB(205, 205, 215), Weight = 60, Mult = 1 },
	{ Name = "Uncommon", Color = Color3.fromRGB(85, 220, 95), Weight = 25, Mult = 2.5 },
	{ Name = "Rare", Color = Color3.fromRGB(70, 155, 255), Weight = 10, Mult = 6 },
	{ Name = "Epic", Color = Color3.fromRGB(180, 95, 255), Weight = 4, Mult = 15 },
	{ Name = "Legendary", Color = Color3.fromRGB(255, 190, 40), Weight = 0.9, Mult = 40 },
	{ Name = "Mythic", Color = Color3.fromRGB(255, 60, 125), Weight = 0.1, Mult = 120 },
	{ Name = "Exclusive", Color = Color3.fromRGB(0, 255, 210), Weight = 0, Mult = 300 }, -- Enchanted Egg only, never thrown
	-- ultra-rare throws, each with its own Blender cinematic on the catch; never needed for zone completion
	{ Name = "Secret", Color = Color3.fromRGB(215, 20, 55), Weight = 0, Mult = 500 }, -- rolled separately: Config.SecretChance
}

-- Enchanted Egg exclusives earn your best (non-Exclusive) animal's income + Bonus, locked in when hatched.
Config.Exclusives = {
	{ Name = "Crystal Bunny", Chance = 35, Bonus = 0.5 }, -- +50%
	{ Name = "Nebula Fox", Chance = 30, Bonus = 1 }, -- +100%
	{ Name = "Angel Pup", Chance = 20, Bonus = 2 }, -- +200%
	{ Name = "Lava Tiger", Chance = 10, Bonus = 3 }, -- +300%
	{ Name = "Rainbow Pegacorn", Chance = 4, Bonus = 5 }, -- +500%
	{ Name = "Void Kitsune", Chance = 1, Bonus = 7 }, -- +700%
}
Config.RarityIndex = {} :: { [string]: number }
for i, r in Config.Rarities do
	Config.RarityIndex[r.Name] = i
end

-- Zones run down the corridor in this order. Colors drive the generated map and the throw-camera lighting.
Config.Zones = {
	{ Name = "Backyard", Icon = "🏡", Floor = Color3.fromRGB(98, 206, 72), Wall = Color3.fromRGB(150, 98, 60), Top = Color3.fromRGB(120, 220, 80),
		Sky = Color3.fromRGB(150, 205, 255),
		Animals = { { "Dog", "Common" }, { "Cat", "Common" }, { "Bunny", "Uncommon" }, { "Hamster", "Rare" },
			{ "Gummy Bear", "Secret" }, { "Cursed Teddy", "Secret" }, { "Cyber Dog", "Secret" } } },
	{ Name = "Farm", Icon = "🌾", Floor = Color3.fromRGB(224, 196, 110), Wall = Color3.fromRGB(176, 64, 52), Top = Color3.fromRGB(240, 210, 90),
		Sky = Color3.fromRGB(255, 215, 160),
		Animals = { { "Pig", "Common" }, { "Duck", "Common" }, { "Cow", "Uncommon" }, { "Sheep", "Rare" },
			{ "Nuclear Frog", "Secret" }, { "Alien Cat", "Secret" } } },
	{ Name = "Jungle", Icon = "🌴", Floor = Color3.fromRGB(46, 150, 70), Wall = Color3.fromRGB(70, 92, 60), Top = Color3.fromRGB(40, 175, 80),
		Sky = Color3.fromRGB(150, 230, 170),
		Animals = { { "Monkey", "Common" }, { "Fox", "Uncommon" }, { "Gorilla", "Rare" }, { "Tiger", "Epic" },
			{ "Lava Gorilla", "Secret" }, { "Shadow Panther", "Secret" } } },
	{ Name = "Safari", Icon = "🦁", Floor = Color3.fromRGB(232, 190, 110), Wall = Color3.fromRGB(196, 120, 64), Top = Color3.fromRGB(205, 180, 80),
		Sky = Color3.fromRGB(255, 190, 120),
		Animals = { { "Zebra", "Common" }, { "Giraffe", "Uncommon" }, { "Elephant", "Rare" }, { "Lion", "Epic" },
			{ "Diamond Elephant", "Secret" }, { "Golden Phoenix", "Secret" } } },
	{ Name = "Arctic", Icon = "❄️", Floor = Color3.fromRGB(236, 246, 255), Wall = Color3.fromRGB(140, 196, 240), Top = Color3.fromRGB(255, 255, 255),
		Sky = Color3.fromRGB(190, 230, 255),
		Animals = { { "Penguin", "Rare" }, { "Polar Bear", "Epic" }, { "Arctic Wolf", "Legendary" },
			{ "Ice Dragon", "Secret" }, { "Emperor Penguin", "Secret" }, { "Crystal Wolf", "Secret" } } },
	{ Name = "Fantasy", Icon = "🐉", Floor = Color3.fromRGB(120, 80, 210), Wall = Color3.fromRGB(60, 40, 120), Top = Color3.fromRGB(255, 120, 230),
		Sky = Color3.fromRGB(220, 150, 255),
		Animals = { { "Phoenix", "Legendary" }, { "Dragon", "Mythic" }, { "Griffin", "Mythic" },
			{ "Rainbow Dragon", "Secret" }, { "Galaxy Whale", "Secret" }, { "Galaxy Cat", "Secret" } } },
	-- World 2 (zones 7-18). Each zone's Secrets are a flat 1 in 10,000 each; all of them are also in the Rainbow Egg.
	{ Name = "Dinosaur Island", Icon = "🦖", Floor = Color3.fromHex("5AA03C"), Wall = Color3.fromHex("6A4A2A"), Top = Color3.fromHex("3C8A2A"),
		Sky = Color3.fromHex("B8E8A0"),
		Animals = { { "Raptor", "Common" }, { "Triceratops", "Uncommon" }, { "Pterodactyl", "Rare" }, { "T-Rex", "Epic" },
			{ "Ancient Dragon", "Secret" }, { "Skeleton Rex", "Secret" }, { "Earth Turtle", "Secret" } } },
	{ Name = "Lost Desert", Icon = "🏜️", Floor = Color3.fromHex("E8C878"), Wall = Color3.fromHex("C8964A"), Top = Color3.fromHex("F0D890"),
		Sky = Color3.fromHex("FFD8A0"),
		Animals = { { "Meerkat", "Common" }, { "Camel", "Uncommon" }, { "Fennec Fox", "Rare" }, { "Scorpion", "Epic" },
			{ "Pharaoh Cat", "Secret" }, { "Golden Sphinx", "Secret" }, { "Lava Scorpion", "Secret" } } },
	{ Name = "Sakura Gardens", Icon = "🌸", Floor = Color3.fromHex("8AD070"), Wall = Color3.fromHex("8A5A4A"), Top = Color3.fromHex("FFB0D0"),
		Sky = Color3.fromHex("FFD8E8"),
		Animals = { { "Koi Fish", "Common" }, { "Red Panda", "Uncommon" }, { "Crane", "Rare" }, { "Sakura Fox", "Epic" },
			{ "Sakura Kitsune", "Secret" }, { "Kitsune", "Secret" }, { "Nine-Tailed Fox", "Secret" } } },
	{ Name = "Lost Atlantis", Icon = "🔱", Floor = Color3.fromHex("2A6A8A"), Wall = Color3.fromHex("1A3A5A"), Top = Color3.fromHex("2AD8C8"),
		Sky = Color3.fromHex("8AE0F0"),
		Animals = { { "Seahorse", "Common" }, { "Dolphin", "Uncommon" }, { "Shark", "Rare" }, { "Sea Snake", "Epic" },
			{ "Atlantis Leviathan", "Secret" }, { "Sea Serpent", "Secret" }, { "Cyber Shark", "Secret" }, { "Alien Octopus", "Secret" }, { "Cosmic Jellyfish", "Secret" } } },
	{ Name = "Sky Kingdom", Icon = "☁️", Floor = Color3.fromHex("C8E8FF"), Wall = Color3.fromHex("8AB8E8"), Top = Color3.fromHex("FFFFFF"),
		Sky = Color3.fromHex("D8F0FF"),
		Animals = { { "Flying Squirrel", "Common" }, { "Owl", "Uncommon" }, { "Eagle", "Rare" }, { "Pegasus", "Epic" },
			{ "Cloud Emperor", "Secret" }, { "Celestial Unicorn", "Secret" }, { "Thunder Wolf", "Secret" }, { "Wind Spirit Deer", "Secret" }, { "Godly Owl", "Secret" } } },
	{ Name = "Halloween Town", Icon = "🎃", Floor = Color3.fromHex("3A2A4A"), Wall = Color3.fromHex("2A1A2A"), Top = Color3.fromHex("FF8A1C"),
		Sky = Color3.fromHex("C88AFF"),
		Animals = { { "Bat", "Common" }, { "Black Cat", "Uncommon" }, { "Zombie Dog", "Rare" }, { "Ghost", "Epic" },
			{ "Pumpkin Reaper", "Secret" }, { "Phantom Bunny", "Secret" }, { "Nightmare Owl", "Secret" }, { "Zombie Bear", "Secret" }, { "Reaper Raven", "Secret" }, { "Haunted Doll Cat", "Secret" } } },
	{ Name = "Tropical Paradise", Icon = "🏝️", Floor = Color3.fromHex("F0E0A0"), Wall = Color3.fromHex("3CB4A8"), Top = Color3.fromHex("4CD964"),
		Sky = Color3.fromHex("A0F0E0"),
		Animals = { { "Crab", "Common" }, { "Flamingo", "Uncommon" }, { "Toucan", "Rare" }, { "Sea Lion", "Epic" },
			{ "Tropical Phoenix", "Secret" }, { "Bubblegum Flamingo", "Secret" }, { "Watermelon Turtle", "Secret" }, { "Chocolate Crocodile", "Secret" } } },
	{ Name = "Toy Factory", Icon = "🧸", Floor = Color3.fromHex("9AA4B2"), Wall = Color3.fromHex("5A6070"), Top = Color3.fromHex("FFC21C"),
		Sky = Color3.fromHex("FFE8B0"),
		Animals = { { "Wind-Up Mouse", "Uncommon" }, { "Plush Bear", "Rare" }, { "Robot Rabbit", "Epic" },
			{ "Ultimate Toymaster", "Secret" }, { "Space Hamster", "Secret" }, { "Mecha Spider", "Secret" }, { "Mecha Lion", "Secret" }, { "Pizza Cat", "Secret" }, { "Marshmallow Sheep", "Secret" } } },
	{ Name = "Ice Age", Icon = "🧊", Floor = Color3.fromHex("DCEEFF"), Wall = Color3.fromHex("6A9ACA"), Top = Color3.fromHex("F4FAFF"),
		Sky = Color3.fromHex("C8E8FF"),
		Animals = { { "Giant Sloth", "Rare" }, { "Mammoth", "Epic" }, { "Saber-Tooth Tiger", "Legendary" },
			{ "Frozen Mammoth King", "Secret" }, { "Frost Saber", "Secret" }, { "Ice Cream Penguin", "Secret" } } },
	{ Name = "Mushroom Kingdom", Icon = "🍄", Floor = Color3.fromHex("4A8A3A"), Wall = Color3.fromHex("5A3A6A"), Top = Color3.fromHex("E8401C"),
		Sky = Color3.fromHex("E0C8FF"),
		Animals = { { "Forest Mouse", "Rare" }, { "Snail", "Epic" }, { "Mushroom Frog", "Legendary" },
			{ "Mycelium Dragon", "Secret" }, { "Crystal Butterfly", "Secret" } } },
	{ Name = "Heaven's Gate", Icon = "👼", Floor = Color3.fromHex("FFF4D8"), Wall = Color3.fromHex("E8D8A0"), Top = Color3.fromHex("FFE45C"),
		Sky = Color3.fromHex("FFF8D8"),
		Animals = { { "Celestial Deer", "Epic" }, { "Golden Eagle", "Legendary" }, { "Angelic Lion", "Mythic" },
			{ "Divine Seraphim", "Secret" }, { "Celestial Emperor", "Secret" }, { "Infinity Serpent", "Secret" }, { "Infinity Dragon", "Secret" }, { "Eternal Wolf", "Secret" } } },
	{ Name = "Underworld", Icon = "🔥", Floor = Color3.fromHex("2A0A0A"), Wall = Color3.fromHex("1C0A0A"), Top = Color3.fromHex("FF3B1C"),
		Sky = Color3.fromHex("FF8A6A"),
		Animals = { { "Demon Bat", "Legendary" }, { "Hellhound", "Mythic" }, { "Cursed Dragon", "Mythic" },
			{ "World Ender", "Secret" }, { "Demon Dragon", "Secret" }, { "Magma Phoenix", "Secret" }, { "Void Creature", "Secret" } } },
}

-- Map layout (studs). The generator in tools/build_place.py uses the same numbers.
Config.Map = {
	ThrowPad = Vector3.new(0, 0.5, -60),
	CorridorStartZ = -72, -- distance 0 is here
	ZoneLength = 230,
	CorridorHalfWidth = 34,
}

-- Toys are the "food": better toys = more luck. Price in cash.
Config.Toys = {
	{ Name = "Tennis Ball", Rarity = "Common", Price = 0, Luck = 1 },
	{ Name = "Squeaky Bone", Rarity = "Common", Price = 300, Luck = 1.3 },
	{ Name = "Rubber Duck", Rarity = "Uncommon", Price = 2500, Luck = 1.7 },
	{ Name = "Frisbee", Rarity = "Uncommon", Price = 25e3, Luck = 2.2 },
	{ Name = "Yarn Ball", Rarity = "Rare", Price = 300e3, Luck = 3 },
	{ Name = "Teddy Bear", Rarity = "Rare", Price = 4e6, Luck = 4 },
	{ Name = "Toy Rocket", Rarity = "Epic", Price = 60e6, Luck = 6 },
	{ Name = "Robot Toy", Rarity = "Legendary", Price = 1e9, Luck = 9 },
	{ Name = "Crystal Orb", Rarity = "Mythic", Price = 20e9, Luck = 15 },
	{ Name = "Meteor Ball", Rarity = "Mythic", Price = 400e9, Luck = 22 },
	{ Name = "Dragon Plush", Rarity = "Mythic", Price = 8e12, Luck = 30 },
	{ Name = "Galaxy Orb", Rarity = "Mythic", Price = 150e12, Luck = 42 },
	{ Name = "Prismatic Frisbee", Rarity = "Mythic", Price = 3e15, Luck = 58 },
	{ Name = "Void Orb", Rarity = "Exclusive", Price = 60e15, Luck = 80 },
	{ Name = "Phoenix Feather", Rarity = "Exclusive", Price = 1.2e18, Luck = 110 },
	{ Name = "King's Ball", Rarity = "Exclusive", Price = 25e18, Luck = 150 },
	{ Name = "Floating Crystal", Rarity = "Exclusive", Price = 500e18, Luck = 200 },
	{ Name = "Thunder Bolt", Rarity = "Secret", Price = 1e22, Luck = 270 },
	{ Name = "Galaxy Destroyer", Rarity = "Secret", Price = 2e23, Luck = 360 },
	{ Name = "Infinity Sphere", Rarity = "Secret", Price = 5e24, Luck = 500 },
}

-- Pull-up bar levels: power gained per rep.
Config.Bars = {
	{ Price = 0, PerRep = 1, Color = Color3.fromRGB(70, 90, 200) },
	{ Price = 500, PerRep = 3, Color = Color3.fromRGB(60, 190, 90) },
	{ Price = 6000, PerRep = 8, Color = Color3.fromRGB(240, 200, 40) },
	{ Price = 75e3, PerRep = 20, Color = Color3.fromRGB(255, 120, 40) },
	{ Price = 1e6, PerRep = 50, Color = Color3.fromRGB(230, 50, 60) },
	{ Price = 15e6, PerRep = 120, Color = Color3.fromRGB(190, 70, 255) },
	{ Price = 250e6, PerRep = 300, Color = Color3.fromRGB(60, 230, 255) },
	{ Price = 5e9, PerRep = 800, Color = Color3.fromRGB(255, 70, 200) },
	{ Price = 150e9, PerRep = 2500, Color = Color3.fromRGB(255, 200, 40) },
	{ Price = 5e12, PerRep = 8000, Color = Color3.fromRGB(110, 230, 255) },
	{ Price = 200e12, PerRep = 25000, Color = Color3.fromRGB(255, 120, 200) },
	{ Price = 8e15, PerRep = 80000, Color = Color3.fromRGB(255, 255, 255) },
}
Config.RepSeconds = 0.6

Config.Sizes = {
	{ Name = "Normal", Chance = 75, Mult = 1, Scale = 1 },
	{ Name = "Big", Chance = 18, Mult = 1.5, Scale = 1.3 },
	{ Name = "Large", Chance = 6, Mult = 2.5, Scale = 1.6 },
	{ Name = "Huge", Chance = 1, Mult = 5, Scale = 2.1 },
}
Config.Mutations = {
	{ Name = "None", Chance = 89.5, Mult = 1 },
	{ Name = "Golden", Chance = 7.5, Mult = 3, Color = Color3.fromRGB(255, 200, 40) },
	{ Name = "Rainbow", Chance = 2.5, Mult = 8, Color = Color3.fromRGB(255, 90, 200) },
	{ Name = "Cosmic", Chance = 0.5, Mult = 25, Color = Color3.fromRGB(90, 70, 255) },
}

Config.StartPower = 10
Config.WalkSpeed = 24
Config.PetScale = 2.5 -- plot pets: a Normal dog stands ~7 studs, bigger than the player like the reference
Config.StartSlots = 6
Config.MaxSlots = 30
Config.MaxAnimals = 1000 -- plot + inventory slots; extra catches auto-sell
Config.SellSeconds = 60 -- an animal sells for this many seconds of its income
Config.IndexZoneBonus = 0.1 -- +10% income per fully discovered zone
Config.OfflineCapHours = 8
Config.OfflineRate = 0.5
Config.ThrowCooldown = 1.5 -- seconds after the reveal finishes
Config.RevealSeconds = 5.5 -- animal walks in, name reveal, result card
Config.OneInSeconds = 2.4 -- how much longer that reveal runs
Config.SecretChance = 1 / 10000 -- the odds players SEE for each Secret (index, luck panel, "1 in" reveal)
Config.LuckySecretChance = 0.01 -- a Super Lucky Throw's chance of a Secret (the luck panel already shows ~1%)
Config.SecretRollChance = 1 / 250 -- the odds actually rolled per throw for EACH Secret in the zone; luck doesn't change it
Config.SecretSeconds = 3.2 -- a Secret's Blender cinematic runs this much longer than a normal reveal (replaces OneInSeconds)

function Config.FlightTime(distance: number): number
	return 1.2 + math.sqrt(distance) / 9 -- grows slower than distance: ~3s for one zone, ~8s across all 18
end
assert(math.abs(Config.FlightTime(4140) - 8.35) < 0.05, "FlightTime self-check failed")

-- Monetization. Set these after creating the products on the Creator Dashboard (0 = hidden).
Config.LuckProductId = 3732504698 -- developer product "100x Luck": your next throw is a Super Lucky Throw
Config.LuckBoost = 100
Config.LuckBoostSeconds = 15 * 60
Config.LuckyRolls = 100 -- a Super Lucky Throw keeps the best of 100 rolls for mutation, size and the Secret check

-- chances ordered worst -> best; returns the chance of each outcome when the best of n independent rolls is kept
function Config.BestOf(chances: { number }, n: number): { number }
	local total = 0
	for _, c in chances do
		total += c
	end
	local out, tail = {}, 0
	local prevTail = 0 -- P(best is strictly better than i)
	for i = #chances, 1, -1 do
		tail += chances[i] / total
		local t = 1 - (1 - math.min(tail, 1)) ^ n
		out[i] = t - prevTail
		prevTail = t
	end
	return out
end
do -- self-check: best of 1 is unchanged; best of 100 on a 1% top tier is ~63.4%
	local one = Config.BestOf({ 99, 1 }, 1)
	local hundred = Config.BestOf({ 99, 1 }, 100)
	assert(math.abs(one[2] - 0.01) < 1e-9 and math.abs(hundred[2] - 0.634) < 1e-3 and math.abs(hundred[1] + hundred[2] - 1) < 1e-9, "BestOf self-check failed")
end

-- Robux shop (layout from the Figma "Roblox shop" frame). Id = developer product / game pass id from the Creator
-- Dashboard; 0 = button says "not for sale yet". Robux is display only: keep it equal to the dashboard price.
-- Eggs and cash packs are Developer Products (repeat buys). Pass = true marks one sold as a one-time Game Pass instead.
Config.Shop = {
	Eggs = {
		{ Name = "ENCHANTED EGG", Badge = "NEW!", Blurb = "A little magic. A legendary new friend.", Icon = "Icon Egg Enchanted",
			Pool = {}, -- filled from Config.Exclusives below
			Buy = { { Key = "Enchanted1", Count = 1, Robux = 35, Id = 3732056166 }, { Key = "Enchanted3", Count = 3, Robux = 90, Id = 3732056226 },
				{ Key = "Enchanted10", Count = 10, Robux = 299, Id = 3732056303 } } },
		{ Name = "RAINBOW EGG", Badge = "SECRET", Blurb = "GUARANTEED Rainbow Huge SECRET!", Icon = "Icon Egg Rainbow",
			Mutation = "Rainbow", Size = "Huge", Pool = {}, -- pool: every Secret pet, equal chance (filled below)
			Buy = { { Key = "Rainbow1", Count = 1, Robux = 45, Id = 3732055877 },
				{ Key = "Rainbow3", Count = 3, Robux = 129, Id = 3732056024 } } },
	},
	-- packs grow as you get richer: the bigger of Seconds of income or Share of the cash you hold (see CashPackValue)
	CashPacks = {
		{ Key = "Cash1", Seconds = 600, Share = 0.25, Robux = 11, Id = 3732056492 },
		{ Key = "Cash2", Seconds = 3600, Share = 1, Robux = 29, Id = 3732056564, Tag = "GOOD VALUE" },
		{ Key = "Cash3", Seconds = 6 * 3600, Share = 3, Robux = 39, Id = 3732056659, Tag = "GREAT VALUE" },
		{ Key = "Cash4", Seconds = 24 * 3600, Share = 10, Robux = 59, Id = 3732056740, Tag = "BEST VALUE" },
	},
	MinIncome = 20,
	Passes = { -- game passes
		{ Key = "CashPass", Name = "x2 CASH", Text = "Double cash from every animal!", Icon = "Icon Cash", Robux = 45, Id = 2087968788 },
		{ Key = "TrainPass", Name = "x2 TRAINING POWER", Text = "Double power on every pull-up!", Icon = "Icon Muscle", Robux = 75, Id = 2088430721 },
	},
}
for _, e in Config.Exclusives do
	table.insert(Config.Shop.Eggs[1].Pool, { e.Name, e.Chance })
end
for _, z in Config.Zones do
	for _, a in z.Animals do
		if a[2] == "Secret" then
			table.insert(Config.Shop.Eggs[2].Pool, { a[1], 1 })
		end
	end
end

function Config.CashPackValue(pack, income: number, cash: number): number
	return math.floor(math.max(math.max(income, Config.Shop.MinIncome) * pack.Seconds, cash * pack.Share))
end
assert(Config.CashPackValue(Config.Shop.CashPacks[4], 0, 1e6) == 10e6 and Config.CashPackValue(Config.Shop.CashPacks[1], 0, 0) == 12000,
	"CashPackValue self-check failed")

Config.ShopItem = {} :: { [string]: any } -- Key -> entry (egg buys also get .Egg)
for _, egg in Config.Shop.Eggs do
	for _, b in egg.Buy do
		b.Egg = egg
		Config.ShopItem[b.Key] = b
	end
end
for _, list in { Config.Shop.CashPacks, Config.Shop.Passes } do
	for _, it in list do
		Config.ShopItem[it.Key] = it
	end
end

function Config.SlotPrice(slots: number): number
	return math.floor(150 * 3 ^ ((slots - Config.StartSlots) / 2))
end

function Config.ThrowDistance(power: number, quality: number): number
	return (25 + 15 * power ^ 0.4) * (0.35 + 0.65 * math.clamp(quality, 0, 1))
end

-- Every throw trains power; better meter timing trains more (like the original). Highest Min first.
Config.Ratings = {
	{ Name = "PERFECT!", Min = 0.92, Color = Color3.fromRGB(80, 230, 90) },
	{ Name = "GOOD", Min = 0.65, Color = Color3.fromRGB(190, 240, 70) },
	{ Name = "OK", Min = 0.35, Color = Color3.fromRGB(255, 190, 50) },
	{ Name = "BAD", Min = 0, Color = Color3.fromRGB(240, 60, 60) },
}

-- Gain climbs smoothly with the marker (squared, so the top is worth far more): +1..+5 for a new player,
-- ~+24 at the top for 2K power. The flat 5 keeps the number moving even at low power.
function Config.ThrowRating(quality: number, power: number): (any, number)
	local gain = math.max(1, math.floor(quality ^ 2 * (5 + power * 0.0095) + 0.5))
	for _, r in Config.Ratings do
		if quality >= r.Min then
			return r, gain
		end
	end
	return Config.Ratings[#Config.Ratings], gain
end
assert(Config.ThrowRating(1, 2000).Name == "PERFECT!" and select(2, Config.ThrowRating(0.7, 2000)) == 12
	and select(2, Config.ThrowRating(1, 10)) == 5 and select(2, Config.ThrowRating(0, 10)) == 1, "ThrowRating self-check failed")

function Config.ZoneAt(distance: number): number
	return math.clamp(math.floor(distance / Config.Map.ZoneLength) + 1, 1, #Config.Zones)
end

function Config.LuckAt(distance: number): number
	return 1 + distance / 40
end

function Config.BaseIncome(zoneIndex: number, rarity: string): number
	return 2 * 12 ^ (zoneIndex - 1) * Config.Rarities[Config.RarityIndex[rarity]].Mult
end

-- name -> {Zone = index, Rarity = name}
Config.AnimalInfo = {} :: { [string]: { Zone: number, Rarity: string, Bonus: number? } }
for zi, z in Config.Zones do
	for _, a in z.Animals do
		Config.AnimalInfo[a[1]] = { Zone = zi, Rarity = a[2] }
	end
end
for _, e in Config.Exclusives do
	Config.AnimalInfo[e.Name] = { Zone = #Config.Zones, Rarity = "Exclusive", Bonus = e.Bonus }
end
Config.ToyInfo = {} :: { [string]: any }
for i, t in Config.Toys do
	Config.ToyInfo[t.Name] = t
	t.Index = i
end

function Config.Find(list: { any }, name: string): any
	for _, v in list do
		if v.Name == name then
			return v
		end
	end
	return nil
end

return Config
