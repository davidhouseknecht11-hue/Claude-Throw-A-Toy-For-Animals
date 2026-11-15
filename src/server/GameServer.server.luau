-- Throw a Toy: authoritative server. Throws, rolls, economy, plots, training, saving, Robux.
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local DSS = game:GetService("DataStoreService")
local HttpService = game:GetService("HttpService")
local MPS = game:GetService("MarketplaceService")
local TweenService = game:GetService("TweenService")
local CollectionService = game:GetService("CollectionService")

local Shared = RS:WaitForChild("Shared")
local Config = require(Shared:WaitForChild("Config"))
local Util = require(Shared:WaitForChild("Util"))
local Mutations = require(Shared:WaitForChild("Mutations"))
local Models = RS:WaitForChild("Models")
local Map = workspace:WaitForChild("Map")
local PlotsFolder = Map:WaitForChild("Plots")
local SellStand = Map:WaitForChild("SellStand")

local Remotes = Instance.new("Folder")
Remotes.Name = "Remotes"
local function remote(class: string, name: string): any
	local r = Instance.new(class)
	r.Name = name
	r.Parent = Remotes
	return r
end
local DataEvent = remote("RemoteEvent", "Data")
local ThrowEvent = remote("RemoteEvent", "Throw")
local ThrowResult = remote("RemoteEvent", "ThrowResult")
local ThrowFX = remote("RemoteEvent", "ThrowFX") -- lets every client play a player's throw animation
local Notify = remote("RemoteEvent", "Notify")
local TrainEvent = remote("RemoteEvent", "Train")
local Request = remote("RemoteFunction", "Request")
local HatchEvent = remote("RemoteEvent", "Hatch") -- egg results for the client reveal
Remotes.Parent = RS

local store
do
	local ok, s = pcall(function()
		return DSS:GetDataStore("ThrowAToy_v1")
	end)
	store = ok and s or nil
end

local rng = Random.new()
local Profiles = {} -- [Player] = profile

type Animal = { Id: string, Name: string, Size: string, Mutation: string, Placed: boolean }

local function defaultData()
	return {
		Cash = 0,
		Power = Config.StartPower,
		Toys = { ["Tennis Ball"] = true },
		Toy = "Tennis Ball",
		Bar = 1,
		Slots = Config.StartSlots,
		Animals = {} :: { Animal },
		Index = {},
		LuckUntil = 0,
		Throws = 0,
		LastOnline = 0,
	}
end

local function notify(player: Player, text: string, kind: string?)
	Notify:FireClient(player, text, kind or "info")
end

-- ===================== ECONOMY =====================
local function animalIncome(a: Animal): number
	local info = Config.AnimalInfo[a.Name]
	if not info then
		return 0
	end
	local size = Config.Find(Config.Sizes, a.Size) or Config.Sizes[1]
	local mut = Config.Find(Config.Mutations, a.Mutation) or Config.Mutations[1]
	return Config.BaseIncome(info.Zone, info.Rarity) * size.Mult * mut.Mult * (info.Boost or 1)
end

local function indexBonus(d): number
	local bonus = 1
	for _, z in Config.Zones do
		local all = true
		for _, a in z.Animals do
			if not d.Index[a[1]] then
				all = false
				break
			end
		end
		if all then
			bonus += Config.IndexZoneBonus
		end
	end
	return bonus
end

local function totalIncome(prof): number
	local sum = 0
	for _, a in prof.Data.Animals do
		if a.Placed then
			sum += animalIncome(a)
		end
	end
	return sum * indexBonus(prof.Data) * (prof.Passes.CashPass and 2 or 1)
end

local function placedCount(d): number
	local n = 0
	for _, a in d.Animals do
		if a.Placed then
			n += 1
		end
	end
	return n
end

-- ===================== PLOTS =====================
local function billboard(parent: Instance, size: UDim2, offset: Vector3, maxDist: number): (BillboardGui, TextLabel)
	local bb = Instance.new("BillboardGui")
	bb.Size = size
	bb.StudsOffset = offset
	bb.AlwaysOnTop = false
	bb.MaxDistance = maxDist
	bb.LightInfluence = 0
	local t = Instance.new("TextLabel")
	t.BackgroundTransparency = 1
	t.Size = UDim2.fromScale(1, 1)
	t.Font = Enum.Font.FredokaOne
	t.TextScaled = true
	t.TextColor3 = Color3.new(1, 1, 1)
	t.RichText = true
	t.Text = ""
	local s = Instance.new("UIStroke")
	s.Thickness = 2.5
	s.Color = Color3.fromRGB(25, 25, 35)
	s.Parent = t
	t.Parent = bb
	bb.Parent = parent
	return bb, t
end

local function prompt(parent: Instance, action: string, object: string, key: Enum.KeyCode?): ProximityPrompt
	local p = Instance.new("ProximityPrompt")
	p.ActionText = action
	p.ObjectText = object
	p.KeyboardKeyCode = key or Enum.KeyCode.E
	p.HoldDuration = 0
	p.MaxActivationDistance = 12
	p.RequiresLineOfSight = false
	p.Parent = parent
	return p
end

local function hex(c: Color3): string
	return c:ToHex()
end

local function decoratePet(model: Model, a: Animal)
	local mut = Config.Find(Config.Mutations, a.Mutation)
	local root = model.PrimaryPart
	if mut and mut.Color and root then
		Mutations.Apply(model, a.Mutation)
		local pe = Instance.new("ParticleEmitter")
		pe.Texture = "rbxasset://textures/particles/sparkles_main.dds"
		pe.Color = ColorSequence.new(mut.Color)
		pe.LightEmission = 1
		pe.Size = NumberSequence.new(0.6, 0)
		pe.Rate = a.Mutation == "Cosmic" and 14 or 6
		pe.Lifetime = NumberRange.new(0.8, 1.4)
		pe.Speed = NumberRange.new(1, 2)
		pe.SpreadAngle = Vector2.new(180, 180)
		pe.Parent = root
	end
	model:SetAttribute("Mutation", a.Mutation)
	model:SetAttribute("AnimalId", a.Id)
	CollectionService:AddTag(model, "PlotPet")
end

local function renderPlot(prof)
	local plot = prof.Plot
	if not plot then
		return
	end
	local pets = plot:FindFirstChild("Pets") or Instance.new("Folder")
	pets.Name = "Pets"
	pets.Parent = plot
	pets:ClearAllChildren()
	local floor = plot:WaitForChild("Floor") :: BasePart
	local cols = 6
	local spacingX = (floor.Size.X - 8) / (cols - 1)
	local i = 0
	for _, a in prof.Data.Animals do
		if not a.Placed then
			continue
		end
		local template = Models:FindFirstChild(a.Name)
		if not template then
			continue
		end
		local row, col = i // cols, i % cols
		i += 1
		local m = template:Clone()
		local size = Config.Find(Config.Sizes, a.Size) or Config.Sizes[1]
		m:ScaleTo(size.Scale)
		local local_ = CFrame.new(-floor.Size.X / 2 + 4 + col * spacingX, floor.Size.Y / 2 + 0.2, -floor.Size.Z / 2 + 5 + row * 7.5) -- on the pedestal
			* CFrame.Angles(0, math.rad(180), 0)
		m:PivotTo(floor.CFrame * local_)
		decoratePet(m, a)
		local info = Config.AnimalInfo[a.Name]
		local rc = Config.Rarities[Config.RarityIndex[info.Rarity]].Color
		local _, ext = m:GetBoundingBox()
		local prefix = (a.Mutation ~= "None" and (a.Mutation .. " ") or "") .. (a.Size ~= "Normal" and (a.Size .. " ") or "")
		local _, label = billboard(m.PrimaryPart :: BasePart, UDim2.fromOffset(150, 44), Vector3.new(0, ext.Y + 1.2, 0), 70)
		label.Text = string.format('<font color="#%s">%s%s</font>\n<font color="#7CFF6B">$%s/s</font>', hex(rc), prefix, a.Name,
			Util.Format(animalIncome(a)))
		m.Parent = pets
	end
	-- signs for the owner
	local d = prof.Data
	local slotLabel = plot:FindFirstChild("SlotSign") and plot.SlotSign:FindFirstChild("Info")
	if slotLabel then
		local t = slotLabel:FindFirstChildOfClass("TextLabel")
		if d.Slots >= Config.MaxSlots then
			t.Text = string.format("🐾 %d/%d  MAX", placedCount(d), d.Slots)
		else
			t.Text = string.format("🐾 %d > %d\n<font color=\"#7CFF6B\">$%s</font>", d.Slots, d.Slots + 2, Util.Format(Config.SlotPrice(d.Slots)))
		end
	end
	local barInfo = plot:FindFirstChild("UpgradePad") and plot.UpgradePad:FindFirstChild("Info")
	if barInfo then
		local t = barInfo:FindFirstChildOfClass("TextLabel")
		local nextBar = Config.Bars[d.Bar + 1]
		t.Text = nextBar and string.format("💪 Bar Lv %d > %d\n<font color=\"#7CFF6B\">$%s</font>", d.Bar, d.Bar + 1, Util.Format(nextBar.Price))
			or string.format("💪 Bar Lv %d  MAX", d.Bar)
	end
	for _, p in plot:GetChildren() do
		if p.Name == "BarFrame" and p:IsA("BasePart") then
			p.Color = Config.Bars[d.Bar].Color
		end
	end
end

-- ===================== DATA SYNC =====================
local function snapshot(prof)
	local d = prof.Data
	local animals = {}
	for _, a in d.Animals do
		table.insert(animals, { Id = a.Id, Name = a.Name, Size = a.Size, Mutation = a.Mutation, Placed = a.Placed, Income = animalIncome(a) })
	end
	return {
		Cash = d.Cash, Power = d.Power, Toys = d.Toys, Toy = d.Toy, Bar = d.Bar, Slots = d.Slots, Animals = animals,
		Index = d.Index, LuckUntil = d.LuckUntil, Income = totalIncome(prof), IndexBonus = indexBonus(d),
		Passes = prof.Passes, ServerTime = os.time(),
	}
end

local function pushData(player: Player)
	local prof = Profiles[player]
	if not prof then
		return
	end
	local d = prof.Data
	player:SetAttribute("Cash", d.Cash)
	player:SetAttribute("Power", d.Power)
	player:SetAttribute("Income", totalIncome(prof))
	local ls = player:FindFirstChild("leaderstats")
	if ls then
		ls.Power.Value = Util.Format(d.Power)
		ls.Cash.Value = "$" .. Util.Format(d.Cash)
	end
	DataEvent:FireClient(player, snapshot(prof))
end

local function refresh(player: Player)
	local prof = Profiles[player]
	if prof then
		renderPlot(prof)
		pushData(player)
	end
end

-- ===================== ANIMALS =====================
local function addAnimal(player: Player, a: Animal)
	local prof = Profiles[player]
	local d = prof.Data
	if #d.Animals >= Config.MaxAnimals then
		local gain = animalIncome(a) * Config.SellSeconds
		d.Cash += gain
		notify(player, "Backpack full! Auto-sold " .. a.Name .. " for $" .. Util.Format(gain), "warn")
		return
	end
	a.Placed = placedCount(d) < d.Slots
	table.insert(d.Animals, a)
	if not a.Placed then
		notify(player, a.Name .. " went to your backpack (plot full)", "info")
	end
end

local function findAnimal(d, id: string): (Animal?, number?)
	for i, a in d.Animals do
		if a.Id == id then
			return a, i
		end
	end
	return nil, nil
end

-- ===================== TRAINING =====================
-- Pull-ups are posed through the arm joints (server-side, so everyone sees them): hands grip the bar wide,
-- and each rep raises the body while the shoulders lower and the elbows bend.
-- Classic rigs use Motor6D (pose = C0); upgraded avatars use AnimationConstraint (pose = Attachment0.CFrame).
-- Both place the child at parent * pose * Transform * child^-1, so rotating the pose rotates the limb the same way.
type Joint = { T: Instance, Prop: string, C0: CFrame, Kind: string, Side: number }
local function armJoints(char: Model): ({ Joint }, boolean)
	local joints = {}
	local function add(name: string, kind: string, side: number)
		local j = char:FindFirstChild(name, true)
		local target, prop
		if j and j:IsA("Motor6D") then
			target, prop = j, "C0"
		elseif j and j:IsA("AnimationConstraint") and j.Attachment0 then
			target, prop = j.Attachment0, "CFrame"
		end
		if target then
			table.insert(joints, { T = target, Prop = prop, C0 = (target :: any)[prop], Kind = kind, Side = side })
		end
	end
	local r15 = char:FindFirstChild("RightUpperArm") ~= nil
	if r15 then
		add("RightShoulder", "shoulder", 1)
		add("LeftShoulder", "shoulder", -1)
		add("RightElbow", "elbow", 1)
		add("LeftElbow", "elbow", -1)
	else
		add("Right Shoulder", "shoulder6", 1)
		add("Left Shoulder", "shoulder6", -1)
	end
	return joints, r15
end

-- C0 for a joint at pull-up phase p (0 = dead hang, 1 = chin over bar)
local function pullPose(j: Joint, p: number): CFrame
	if j.Kind == "shoulder" then
		return j.C0 * CFrame.Angles(0, 0, j.Side * math.rad(168 - 73 * p))
	elseif j.Kind == "elbow" then
		return j.C0 * CFrame.Angles(0, 0, j.Side * math.rad(85 * p))
	end
	return j.C0 * CFrame.Angles(0, 0, j.Side * -math.rad(180 - 55 * p)) -- R6: no elbow, arms just lower
end

local function stopTraining(player: Player)
	local prof = Profiles[player]
	if not prof or not prof.Training then
		return
	end
	prof.Training = false
	prof.TrainToken = (prof.TrainToken or 0) + 1 -- ends the rep loop even if training restarts before it wakes
	for _, tw in prof.TrainTweens or {} do
		tw:Cancel() -- a running rep tween would keep moving the body / arms after we reset them
	end
	prof.TrainTweens = nil
	player:SetAttribute("Training", false)
	local spot = prof.Plot and prof.Plot:FindFirstChild("TrainSpot")
	local trainPrompt = spot and spot:FindFirstChildOfClass("ProximityPrompt")
	if trainPrompt then
		trainPrompt.Enabled = true
	end
	for _, j in prof.TrainJoints or {} do
		if j.T.Parent then
			(j.T :: any)[j.Prop] = j.C0
		end
	end
	prof.TrainJoints = nil
	local char = player.Character
	local hum = char and char:FindFirstChildOfClass("Humanoid")
	if hum then
		hum.PlatformStand = false
	end
	local hrp = char and char:FindFirstChild("HumanoidRootPart")
	if hrp then
		hrp.Anchored = false
		hrp.CFrame = hrp.CFrame * CFrame.new(0, -1, 3)
	end
end

local function startTraining(player: Player)
	local prof = Profiles[player]
	if not prof or prof.Training or prof.Busy then
		return
	end
	local char = player.Character
	local hrp = char and char:FindFirstChild("HumanoidRootPart") :: BasePart
	local spot = prof.Plot and prof.Plot:FindFirstChild("TrainSpot") :: BasePart
	if not (hrp and spot) then
		return
	end
	prof.Training = true
	player:SetAttribute("Training", true)
	local trainPrompt = spot:FindFirstChildOfClass("ProximityPrompt")
	if trainPrompt then
		trainPrompt.Enabled = false -- don't float "Train" over the player mid-rep
	end
	-- Measure this avatar (sizes vary) while it still stands normally: arm length and shoulder height over the root.
	local upperArm = char:FindFirstChild("RightUpperArm") or char:FindFirstChild("Right Arm")
	local lowerArm, hand = char:FindFirstChild("RightLowerArm"), char:FindFirstChild("RightHand")
	local upperLen = upperArm and upperArm.Size.Y or 1.2
	local armLen = lowerArm and (upperLen + lowerArm.Size.Y + (hand and hand.Size.Y * 0.6 or 0.3)) or upperLen
	local shoulderOff = upperArm and (upperArm.Position.Y + upperArm.Size.Y / 2 - hrp.Position.Y) or 1
	local barY = spot.Position.Y + 3.4 -- TrainSpot sits 3.4 studs under the bar
	local joints, r15 = armJoints(char)
	prof.TrainJoints = joints
	local hum = char:FindFirstChildOfClass("Humanoid")
	if hum then
		hum.PlatformStand = true -- stops walk/fall animations fighting the pose
	end
	hrp.Anchored = true
	-- dead hang: hands just under the bar; at the top the upper arms go horizontal, lifting the body ~one upper arm
	local low = spot.CFrame.Rotation + Vector3.new(spot.Position.X, barY - armLen * 0.97 - shoulderOff, spot.Position.Z)
	local high = low * CFrame.new(0, r15 and upperLen * 0.95 or armLen * 0.5, 0)
	hrp.CFrame = low
	for _, j in joints do
		(j.T :: any)[j.Prop] = pullPose(j, 0)
	end
	local token = (prof.TrainToken or 0) + 1
	prof.TrainToken = token
	task.spawn(function()
		local info = TweenInfo.new(Config.RepSeconds / 2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, 0, true)
		while prof.TrainToken == token and player.Parent and hrp.Parent do
			-- every rep starts from the exact dead-hang pose, so tiny drift can't build up into a glitch
			hrp.CFrame = low
			local tweens = { TweenService:Create(hrp, info, { CFrame = high }) }
			for _, j in joints do
				(j.T :: any)[j.Prop] = pullPose(j, 0)
				table.insert(tweens, TweenService:Create(j.T, info, { [j.Prop] = pullPose(j, 1) }))
			end
			prof.TrainTweens = tweens
			for _, tw in tweens do
				tw:Play()
			end
			task.wait(Config.RepSeconds)
			if prof.TrainToken ~= token then
				break
			end
			prof.Data.Power += Config.Bars[prof.Data.Bar].PerRep * (prof.Passes.TrainPass and 2 or 1)
			player:SetAttribute("Power", prof.Data.Power)
			local ls = player:FindFirstChild("leaderstats")
			if ls then
				ls.Power.Value = Util.Format(prof.Data.Power)
			end
		end
	end)
end

TrainEvent.OnServerEvent:Connect(function(player, on)
	if on == false then
		stopTraining(player)
	end
end)

-- ===================== THROWING =====================
ThrowEvent.OnServerEvent:Connect(function(player: Player, quality: any)
	local prof = Profiles[player]
	if not prof or prof.Busy or prof.Training then
		return
	end
	-- shortcut: the meter value comes from the client, so a cheater can always throw "perfect"; move the meter to server time if that matters
	if typeof(quality) ~= "number" or quality ~= quality then
		return
	end
	quality = math.clamp(quality, 0, 1)
	local hrp = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if not hrp or (hrp.Position - Config.Map.ThrowPad).Magnitude > 30 then
		return
	end
	prof.Busy = true
	local d = prof.Data
	local dist = math.min(Config.ThrowDistance(d.Power, quality), Config.Map.ZoneLength * #Config.Zones - 8)
	local rating, powerGain = Config.ThrowRating(quality, d.Power)
	local perfect = rating == Config.Ratings[1]
	d.Power += powerGain
	local zone = Config.ZoneAt(dist)
	local toy = Config.ToyInfo[d.Toy] or Config.Toys[1]
	local boosted = d.LuckUntil > os.time()
	local luck = Config.LuckAt(dist) * toy.Luck * (boosted and Config.LuckBoost or 1)
	local pick, pA = Util.Pick(Config.Zones[zone].Animals, function(a)
		local ri = Config.RarityIndex[a[2]]
		return Config.Rarities[ri].Weight * luck ^ ((ri - 1) / 5)
	end, rng)
	local luckSoft = math.min(luck, 60)
	local size, pS = Util.Pick(Config.Sizes, function(s)
		return s.Chance * (s.Name ~= "Normal" and luckSoft ^ 0.15 or 1)
	end, rng)
	local mut, pM = Util.Pick(Config.Mutations, function(m)
		return m.Chance * (m.Name ~= "None" and luckSoft ^ 0.2 or 1)
	end, rng)
	local odds = math.max(1, math.floor(1 / (pA * pS * pM) + 0.5)) -- this exact animal + size + mutation, at this luck
	local oneIn = odds >= Config.OneInMin
	local animal: Animal = { Id = HttpService:GenerateGUID(false), Name = pick[1], Size = size.Name, Mutation = mut.Name, Placed = false }
	local isNew = not d.Index[pick[1]]
	local landing = Vector3.new(rng:NextNumber(-14, 14), 0, Config.Map.CorridorStartZ - dist)
	ThrowResult:FireClient(player, {
		Landing = landing, Distance = dist, Zone = zone, Luck = luck, Perfect = perfect, Rating = rating.Name, PowerGain = powerGain,
		Animal = animal, Rarity = pick[2], Income = animalIncome(animal), New = isNew, Toy = d.Toy, Boosted = boosted,
		Odds = odds, OneIn = oneIn,
	})
	player:SetAttribute("Power", d.Power)
	ThrowFX:FireAllClients(player)
	task.delay(Config.FlightTime(dist) + Config.RevealSeconds + (oneIn and Config.OneInSeconds or 0), function()
		if Profiles[player] ~= prof then
			return
		end
		d.Index[pick[1]] = true
		d.Throws += 1
		addAnimal(player, animal)
		refresh(player)
		task.wait(Config.ThrowCooldown)
		prof.Busy = false
	end)
end)

-- ===================== REQUESTS (shop, plot, animals) =====================
local Actions = {}

function Actions.BuyToy(player, prof, name: string)
	local toy = Config.ToyInfo[name]
	if not toy then
		return false, "Unknown toy"
	end
	local d = prof.Data
	if not d.Toys[name] then
		if d.Cash < toy.Price then
			return false, "Not enough cash!"
		end
		d.Cash -= toy.Price
		d.Toys[name] = true
	end
	d.Toy = name
	return true, "Equipped " .. name .. "!"
end

function Actions.Place(player, prof, id: string)
	local d = prof.Data
	local a = findAnimal(d, id)
	if not a then
		return false, "Animal not found"
	end
	if not a.Placed and placedCount(d) >= d.Slots then
		return false, "Your plot is full! Buy more slots."
	end
	a.Placed = not a.Placed
	return true
end

function Actions.Sell(player, prof, id: string)
	local d = prof.Data
	local a, i = findAnimal(d, id)
	if not a then
		return false, "Animal not found"
	end
	local gain = animalIncome(a) * Config.SellSeconds
	table.remove(d.Animals, i)
	d.Cash += gain
	return true, "Sold " .. a.Name .. " for $" .. Util.Format(gain)
end

function Actions.SellBackpack(player, prof)
	local d = prof.Data
	local gain, n = 0, 0
	for i = #d.Animals, 1, -1 do
		local a = d.Animals[i]
		if not a.Placed then
			gain += animalIncome(a) * Config.SellSeconds
			n += 1
			table.remove(d.Animals, i)
		end
	end
	if n == 0 then
		return false, "Nothing in your backpack to sell"
	end
	d.Cash += gain
	return true, string.format("Sold %d animals for $%s", n, Util.Format(gain))
end

function Actions.EquipBest(player, prof)
	local d = prof.Data
	local sorted = table.clone(d.Animals)
	table.sort(sorted, function(x, y)
		return animalIncome(x) > animalIncome(y)
	end)
	for i, a in sorted do
		a.Placed = i <= d.Slots
	end
	return true, "Equipped your best animals!"
end

function Actions.UpgradeBar(player, prof)
	local d = prof.Data
	local nextBar = Config.Bars[d.Bar + 1]
	if not nextBar then
		return false, "Bar is maxed!"
	end
	if d.Cash < nextBar.Price then
		return false, "Not enough cash!"
	end
	d.Cash -= nextBar.Price
	d.Bar += 1
	return true, "Bar upgraded! +" .. nextBar.PerRep .. " power per rep"
end

function Actions.BuySlot(player, prof)
	local d = prof.Data
	if d.Slots >= Config.MaxSlots then
		return false, "Plot is maxed!"
	end
	local price = Config.SlotPrice(d.Slots)
	if d.Cash < price then
		return false, "Not enough cash!"
	end
	d.Cash -= price
	d.Slots = math.min(Config.MaxSlots, d.Slots + 2)
	return true, "+2 plot slots!"
end

function Actions.BuyLuck(player, prof)
	if Config.LuckProductId == 0 then
		return false, "Luck boost isn't for sale yet"
	end
	MPS:PromptProductPurchase(player, Config.LuckProductId)
	return true
end

function Actions.BuyShop(player, prof, key: string)
	local item = Config.ShopItem[key]
	if not item then
		return false
	end
	if prof.Passes[key] then
		return false, "You already own this!"
	end
	if item.Id == 0 then
		return false, "Not for sale yet!"
	end
	if item.Text then -- game passes have a description, products don't
		MPS:PromptGamePassPurchase(player, item.Id)
	else
		MPS:PromptProductPurchase(player, item.Id)
	end
	return true
end

local function runAction(player: Player, action: string, arg: any): (boolean, string?)
	local prof = Profiles[player]
	local fn = Actions[action]
	if not prof or not fn or (arg ~= nil and typeof(arg) ~= "string") then
		return false, "Try again in a moment"
	end
	local ok, msg = fn(player, prof, arg)
	if ok then
		refresh(player)
	end
	return ok, msg
end

Request.OnServerInvoke = function(player, action, arg)
	if typeof(action) ~= "string" then
		return false
	end
	return runAction(player, action, arg)
end

-- ===================== WORLD PROMPTS =====================
local function ownerOnly(plot: Model, fn: (Player) -> ())
	return function(player: Player)
		local prof = Profiles[player]
		if prof and prof.Plot == plot then
			fn(player)
		else
			notify(player, "That's not your plot!", "warn")
		end
	end
end

local function feedback(player: Player, ok: boolean, msg: string?)
	if msg then
		notify(player, msg, ok and "good" or "bad")
	end
end

for _, plot in PlotsFolder:GetChildren() do
	local spot = plot:FindFirstChild("TrainSpot")
	if spot then
		local p = prompt(spot, "Train", "Pull-up Bar")
		p.Triggered:Connect(ownerOnly(plot, startTraining))
	end
	local pad = plot:FindFirstChild("UpgradePad")
	if pad then
		billboard(pad, UDim2.fromOffset(220, 70), Vector3.new(0, 4, 0), 80).Name = "Info"
		prompt(pad, "Upgrade Bar", "Pull-up Bar").Triggered:Connect(ownerOnly(plot, function(player)
			feedback(player, runAction(player, "UpgradeBar"))
		end))
	end
	local sign = plot:FindFirstChild("SlotSign")
	if sign then
		billboard(sign, UDim2.fromOffset(220, 70), Vector3.new(0, 4.5, 0), 80).Name = "Info"
		prompt(sign, "Buy +2 Slots", "Plot").Triggered:Connect(ownerOnly(plot, function(player)
			feedback(player, runAction(player, "BuySlot"))
		end))
	end
	local owner = plot:FindFirstChild("OwnerSign")
	if owner then
		local bb, t = billboard(owner, UDim2.fromOffset(260, 50), Vector3.new(0, 3, 0), 150)
		bb.Name = "Owner"
		t.Text = "Empty Plot"
	end
end
do
	local board = Map:FindFirstChild("Base") and Map.Base:FindFirstChild("TitleBoard")
	if board then
		local sg = Instance.new("SurfaceGui")
		sg.Face = Enum.NormalId.Back -- faces the plaza
		sg.PixelsPerStud = 40
		sg.LightInfluence = 0
		local t = Instance.new("TextLabel")
		t.Size = UDim2.fromScale(1, 1)
		t.BackgroundTransparency = 1
		t.Font = Enum.Font.FredokaOne
		t.TextScaled = true
		t.Text = "🧸 THROW A TOY 🧸"
		t.TextColor3 = Color3.new(1, 1, 1)
		local st = Instance.new("UIStroke")
		st.Thickness = 8
		st.Color = Color3.fromRGB(120, 20, 90)
		st.Parent = t
		t.Parent = sg
		sg.Parent = board
	end
	local counter = SellStand:FindFirstChild("Counter") or SellStand
	prompt(counter, "Sell Backpack", "Sell Stand").Triggered:Connect(function(player)
		feedback(player, runAction(player, "SellBackpack"))
	end)
end

do
	local corridor = Map:FindFirstChild("Corridor")
	for _, z in Config.Zones do
		local zm = corridor and corridor:FindFirstChild(z.Name)
		local sign = zm and zm:FindFirstChild("ZoneSign")
		if sign then
			-- sized in studs so far-away signs shrink with distance instead of covering the screen
			local _, t = billboard(sign, UDim2.fromScale(34, 8), Vector3.new(0, 1, 0), 700)
			t.Text = z.Icon .. " " .. z.Name:upper()
		end
	end
	local counter = SellStand:FindFirstChild("Counter")
	if counter then
		local _, t = billboard(counter, UDim2.fromOffset(220, 70), Vector3.new(0, 10, 0), 160)
		t.Text = '<font color="#FF5050">💰 SELL</font>'
	end
	-- Noob shop vendor: the client opens the shop when this prompt fires
	local vendor = Map:FindFirstChild("ShopVendor")
	local vTorso = vendor and vendor:FindFirstChild("Torso")
	if vTorso then
		local p = prompt(vTorso, "Shop", "Toy Shop")
		p.Name = "ShopPrompt"
		p.MaxActivationDistance = 14
		local _, vt = billboard(vendor:FindFirstChild("Head") or vTorso, UDim2.fromOffset(240, 64), Vector3.new(0, 2.6, 0), 140)
		vt.Text = '<font color="#5CC8FF">🧸 TOY SHOP</font>'
	end
end

-- ===================== PLAYERS =====================
local function assignPlot(player: Player): Model?
	local taken = {}
	for _, prof in Profiles do
		if prof.Plot then
			taken[prof.Plot] = true
		end
	end
	local plots = PlotsFolder:GetChildren()
	table.sort(plots, function(a, b)
		return a.Name < b.Name
	end)
	for _, plot in plots do
		if not taken[plot] then
			return plot
		end
	end
	return nil
end

local function sendHome(player: Player)
	local prof = Profiles[player]
	local char = player.Character
	local spawnPart = prof and prof.Plot and prof.Plot:FindFirstChild("Spawn")
	if char and spawnPart then
		char:PivotTo(spawnPart.CFrame + Vector3.new(0, 4, 0))
	end
end

local function load(player: Player)
	local data, ok = nil, true
	if store then
		ok = false
		for attempt = 1, 3 do
			local success, result = pcall(function()
				return store:GetAsync("u" .. player.UserId)
			end)
			if success then
				data, ok = result, true
				break
			end
			task.wait(attempt)
		end
	end
	local d = defaultData()
	if type(data) == "table" then
		for k, v in data do
			d[k] = v
		end
	end
	return d, ok
end

local function save(player: Player)
	local prof = Profiles[player]
	if not (store and prof and prof.CanSave) then
		return
	end
	prof.Data.LastOnline = os.time()
	local payload = prof.Data
	local ok, err = pcall(function()
		store:UpdateAsync("u" .. player.UserId, function()
			return payload
		end)
	end)
	if not ok then
		warn("Save failed for", player.Name, err)
	end
end

Players.PlayerAdded:Connect(function(player)
	local ls = Instance.new("Folder")
	ls.Name = "leaderstats"
	local pw = Instance.new("StringValue")
	pw.Name = "Power"
	pw.Parent = ls
	local cash = Instance.new("StringValue")
	cash.Name = "Cash"
	cash.Parent = ls
	ls.Parent = player

	local d, loaded = load(player)
	if not player.Parent then
		return
	end
	local prof = { Data = d, Plot = assignPlot(player), Busy = false, Training = false, CanSave = loaded, Passes = {} }
	Profiles[player] = prof
	if not loaded then
		-- never overwrite a save we failed to read
		notify(player, "Couldn't load your save. Progress this session won't be saved. Rejoin to retry.", "bad")
	end
	for _, pass in Config.Shop.Passes do
		if pass.Id ~= 0 then
			local okPass, owns = pcall(MPS.UserOwnsGamePassAsync, MPS, player.UserId, pass.Id)
			prof.Passes[pass.Key] = okPass and owns or nil
		end
	end
	if prof.Plot then
		local owner = prof.Plot:FindFirstChild("OwnerSign")
		local label = owner and owner:FindFirstChild("Owner")
		if label then
			label:FindFirstChildOfClass("TextLabel").Text = player.DisplayName .. "'s Plot"
		end
		prof.Plot:SetAttribute("OwnerId", player.UserId)
	end
	player:SetAttribute("PlotName", prof.Plot and prof.Plot.Name or "")
	-- offline earnings
	if d.LastOnline > 0 then
		local away = math.clamp(os.time() - d.LastOnline, 0, Config.OfflineCapHours * 3600)
		local earned = totalIncome(prof) * away * Config.OfflineRate
		if earned >= 1 then
			d.Cash += earned
			task.delay(4, notify, player, "While you were away your animals earned $" .. Util.Format(earned) .. "!", "good")
		end
	end
	player.CharacterAdded:Connect(function(char)
		stopTraining(player)
		task.wait(0.2)
		sendHome(player)
		local hum = char:WaitForChild("Humanoid") :: Humanoid
		hum:GetPropertyChangedSignal("Jump"):Connect(function()
			if hum.Jump then
				stopTraining(player)
			end
		end)
	end)
	if player.Character then
		sendHome(player)
	end
	refresh(player)
end)

Players.PlayerRemoving:Connect(function(player)
	local prof = Profiles[player]
	if not prof then
		return
	end
	save(player)
	if prof.Plot then
		local pets = prof.Plot:FindFirstChild("Pets")
		if pets then
			pets:ClearAllChildren()
		end
		local owner = prof.Plot:FindFirstChild("OwnerSign")
		local label = owner and owner:FindFirstChild("Owner")
		if label then
			label:FindFirstChildOfClass("TextLabel").Text = "Empty Plot"
		end
		prof.Plot:SetAttribute("OwnerId", nil)
	end
	Profiles[player] = nil
end)

game:BindToClose(function()
	local threads = {}
	for player in Profiles do
		table.insert(threads, task.spawn(save, player))
	end
	task.wait(3)
end)

-- ===================== ROBUX SHOP =====================
local ProductById = {}
for key, item in Config.ShopItem do
	if item.Id ~= 0 and not item.Text then
		ProductById[item.Id] = item
	end
end

local allAnimals = {}
for _, z in Config.Zones do
	for _, a in z.Animals do
		table.insert(allAnimals, { a[1], Config.Rarities[Config.RarityIndex[a[2]]].Weight })
	end
end

local function hatch(player: Player, prof, egg, count: number)
	local d, results = prof.Data, {}
	for _ = 1, count do
		local pick, chance = Util.Pick(egg.Pool or allAnimals, function(e)
			return e[2]
		end, rng)
		local size, mut = egg.Size, egg.Mutation
		if not size then
			local s, p = Util.Pick(Config.Sizes, function(sz) return sz.Chance end, rng)
			size, chance = s.Name, chance * p
		end
		if not mut then
			local m, p = Util.Pick(Config.Mutations, function(mm) return mm.Chance end, rng)
			mut, chance = m.Name, chance * p
		end
		local animal: Animal = { Id = HttpService:GenerateGUID(false), Name = pick[1], Size = size, Mutation = mut, Placed = false }
		d.Index[pick[1]] = true
		addAnimal(player, animal)
		table.insert(results, { Name = animal.Name, Size = size, Mutation = mut, Odds = math.max(1, math.floor(1 / chance + 0.5)) })
	end
	HatchEvent:FireClient(player, egg.Name, results)
end

local function grantProduct(player: Player, prof, item)
	if item.Egg then
		hatch(player, prof, item.Egg, item.Count)
	else
		local gain = Config.CashPackValue(item, totalIncome(prof), prof.Data.Cash)
		prof.Data.Cash += gain
		notify(player, "+$" .. Util.Format(gain) .. " cash!", "good")
	end
	refresh(player)
end

MPS.ProcessReceipt = function(receipt)
	local player = Players:GetPlayerByUserId(receipt.PlayerId)
	local prof = player and Profiles[player]
	if not prof then
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end
	if receipt.ProductId == Config.LuckProductId then
		prof.Data.LuckUntil = math.max(prof.Data.LuckUntil, os.time()) + Config.LuckBoostSeconds
		notify(player, "🍀 " .. Config.LuckBoost .. "x LUCK active!", "good")
		pushData(player)
		save(player)
		return Enum.ProductPurchaseDecision.PurchaseGranted
	end
	local item = ProductById[receipt.ProductId]
	if item then
		grantProduct(player, prof, item)
		save(player)
		return Enum.ProductPurchaseDecision.PurchaseGranted
	end
	return Enum.ProductPurchaseDecision.NotProcessedYet
end

MPS.PromptGamePassPurchaseFinished:Connect(function(player, passId, bought)
	local prof = Profiles[player]
	if not (prof and bought) then
		return
	end
	for _, pass in Config.Shop.Passes do
		if pass.Id == passId then
			prof.Passes[pass.Key] = true
			notify(player, pass.Name .. " unlocked forever!", "good")
			pushData(player)
		end
	end
end)

-- income + autosave loops
task.spawn(function()
	local t = 0
	while true do
		task.wait(1)
		t += 1
		for player, prof in Profiles do
			prof.Data.Cash += totalIncome(prof)
			player:SetAttribute("Cash", prof.Data.Cash)
			local ls = player:FindFirstChild("leaderstats")
			if ls then
				ls.Cash.Value = "$" .. Util.Format(prof.Data.Cash)
			end
		end
		if t % 90 == 0 then
			for player in Profiles do
				task.spawn(save, player)
			end
		end
	end
end)
