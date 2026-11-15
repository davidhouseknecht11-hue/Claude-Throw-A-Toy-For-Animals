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
}

-- Enchanted Egg exclusives: earn like a Fantasy-zone pet x Exclusive rarity x Boost (a Void Kitsune out-earns ~100 Mythics).
Config.Exclusives = {
	{ Name = "Crystal Bunny", Chance = 35, Boost = 1 },
	{ Name = "Galaxy Cat", Chance = 30, Boost = 1.5 },
	{ Name = "Angel Pup", Chance = 20, Boost = 2.5 },
	{ Name = "Lava Tiger", Chance = 10, Boost = 4 },
	{ Name = "Rainbow Pegacorn", Chance = 4, Boost = 8 },
	{ Name = "Void Kitsune", Chance = 1, Boost = 20 },
}
Config.RarityIndex = {} :: { [string]: number }
for i, r in Config.Rarities do
	Config.RarityIndex[r.Name] = i
end

-- Zones run down the corridor in this order. Colors drive the generated map and the throw-camera lighting.
Config.Zones = {
	{ Name = "Backyard", Icon = "🏡", Floor = Color3.fromRGB(98, 206, 72), Wall = Color3.fromRGB(150, 98, 60), Top = Color3.fromRGB(120, 220, 80),
		Sky = Color3.fromRGB(150, 205, 255),
		Animals = { { "Dog", "Common" }, { "Cat", "Common" }, { "Bunny", "Uncommon" }, { "Hamster", "Rare" } } },
	{ Name = "Farm", Icon = "🌾", Floor = Color3.fromRGB(224, 196, 110), Wall = Color3.fromRGB(176, 64, 52), Top = Color3.fromRGB(240, 210, 90),
		Sky = Color3.fromRGB(255, 215, 160),
		Animals = { { "Pig", "Common" }, { "Duck", "Common" }, { "Cow", "Uncommon" }, { "Sheep", "Rare" } } },
	{ Name = "Jungle", Icon = "🌴", Floor = Color3.fromRGB(46, 150, 70), Wall = Color3.fromRGB(70, 92, 60), Top = Color3.fromRGB(40, 175, 80),
		Sky = Color3.fromRGB(150, 230, 170),
		Animals = { { "Monkey", "Common" }, { "Fox", "Uncommon" }, { "Gorilla", "Rare" }, { "Tiger", "Epic" } } },
	{ Name = "Safari", Icon = "🦁", Floor = Color3.fromRGB(232, 190, 110), Wall = Color3.fromRGB(196, 120, 64), Top = Color3.fromRGB(205, 180, 80),
		Sky = Color3.fromRGB(255, 190, 120),
		Animals = { { "Zebra", "Common" }, { "Giraffe", "Uncommon" }, { "Elephant", "Rare" }, { "Lion", "Epic" } } },
	{ Name = "Arctic", Icon = "❄️", Floor = Color3.fromRGB(236, 246, 255), Wall = Color3.fromRGB(140, 196, 240), Top = Color3.fromRGB(255, 255, 255),
		Sky = Color3.fromRGB(190, 230, 255),
		Animals = { { "Penguin", "Rare" }, { "Polar Bear", "Epic" }, { "Arctic Wolf", "Legendary" } } },
	{ Name = "Fantasy", Icon = "🐉", Floor = Color3.fromRGB(120, 80, 210), Wall = Color3.fromRGB(60, 40, 120), Top = Color3.fromRGB(255, 120, 230),
		Sky = Color3.fromRGB(220, 150, 255),
		Animals = { { "Phoenix", "Legendary" }, { "Dragon", "Mythic" }, { "Crystal Wolf", "Mythic" } } },
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
Config.StartSlots = 6
Config.MaxSlots = 30
Config.MaxAnimals = 120 -- plot + backpack; extra catches auto-sell
Config.SellSeconds = 60 -- an animal sells for this many seconds of its income
Config.IndexZoneBonus = 0.1 -- +10% income per fully discovered zone
Config.OfflineCapHours = 8
Config.OfflineRate = 0.5
Config.ThrowCooldown = 1.5 -- seconds after the reveal finishes
Config.RevealSeconds = 5.5 -- animal walks in, name reveal, result card

function Config.FlightTime(distance: number): number
	return 1.4 + distance / 230
end

-- Monetization. Set these after creating the products on the Creator Dashboard (0 = hidden).
Config.LuckProductId = 0 -- developer product: 100x luck for 15 minutes
Config.LuckBoost = 100
Config.LuckBoostSeconds = 15 * 60

-- Robux shop (layout from the Figma "Roblox shop" frame). Id = developer product / game pass id from the Creator
-- Dashboard; 0 = button says "not for sale yet". Robux is display only: keep it equal to the dashboard price.
Config.Shop = {
	Eggs = {
		{ Name = "ENCHANTED EGG", Badge = "NEW!", Blurb = "A little magic. A legendary new friend.", Icon = "Icon Egg Enchanted",
			Pool = {}, -- filled from Config.Exclusives below
			Buy = { { Key = "Enchanted1", Count = 1, Robux = 72, Id = 0 }, { Key = "Enchanted3", Count = 3, Robux = 180, Id = 0 },
				{ Key = "Enchanted10", Count = 10, Robux = 585, Id = 0 } } },
		{ Name = "RAINBOW EGG", Badge = "LIMITED", Blurb = "Hatch a random Rainbow Huge animal!", Icon = "Icon Egg Rainbow",
			Mutation = "Rainbow", Size = "Huge", -- pool: every animal, weighted by rarity
			Buy = { { Key = "Rainbow1", Count = 1, Robux = 90, Id = 0 }, { Key = "Rainbow3", Count = 3, Robux = 225, Id = 0 } } },
	},
	-- packs grow as you get richer: the bigger of Seconds of income or Share of the cash you hold (see CashPackValue)
	CashPacks = {
		{ Key = "Cash1", Seconds = 600, Share = 0.25, Robux = 22, Id = 0 },
		{ Key = "Cash2", Seconds = 3600, Share = 1, Robux = 54, Id = 0, Tag = "GOOD VALUE" },
		{ Key = "Cash3", Seconds = 6 * 3600, Share = 3, Robux = 72, Id = 0, Tag = "GREAT VALUE" },
		{ Key = "Cash4", Seconds = 24 * 3600, Share = 10, Robux = 180, Id = 0, Tag = "BEST VALUE" },
	},
	MinIncome = 20,
	Passes = { -- game passes
		{ Key = "CashPass", Name = "x2 CASH", Text = "Double cash from every animal!", Icon = "Icon Cash", Robux = 90, Id = 0 },
		{ Key = "TrainPass", Name = "x2 TRAINING POWER", Text = "Double power on every pull-up!", Icon = "Icon Muscle", Robux = 135, Id = 0 },
	},
}
for _, e in Config.Exclusives do
	table.insert(Config.Shop.Eggs[1].Pool, { e.Name, e.Chance })
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
Config.AnimalInfo = {} :: { [string]: { Zone: number, Rarity: string, Boost: number? } }
for zi, z in Config.Zones do
	for _, a in z.Animals do
		Config.AnimalInfo[a[1]] = { Zone = zi, Rarity = a[2] }
	end
end
for _, e in Config.Exclusives do
	Config.AnimalInfo[e.Name] = { Zone = #Config.Zones, Rarity = "Exclusive", Boost = e.Boost }
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
