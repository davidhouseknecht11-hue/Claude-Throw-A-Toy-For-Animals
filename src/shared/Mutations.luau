-- Real mutations: the pet's own bricks are recolored (gold / rainbow / deep space) and a Blender-made prop is attached
-- (crown on the head, rainbow arc over the back, cosmic ring around the body). Used on plot pets (server) and on the
-- reveal / UI thumbnails (client) so a mutation looks the same everywhere.
local Models = game:GetService("ReplicatedStorage"):WaitForChild("Models")

local Mutations = {}

local GOLD_DARK, GOLD_LIGHT = Color3.fromRGB(150, 92, 8), Color3.fromRGB(255, 228, 100)
local SPACE_DARK, SPACE_LIGHT = Color3.fromRGB(14, 9, 44), Color3.fromRGB(120, 75, 255)
local STARLIGHT = Color3.fromRGB(160, 130, 255)
local PROP = { Golden = "Mut Crown", Rainbow = "Mut Rainbow", Cosmic = "Mut Ring" }
local RAINBOW = { Color3.fromRGB(255, 40, 60), Color3.fromRGB(50, 110, 255), Color3.fromRGB(40, 220, 90) } -- red, blue, green
local RAINBOW_STEP = 1.1 -- seconds per color

local function lum(c: Color3): number
	return c.R * 0.299 + c.G * 0.587 + c.B * 0.114
end

-- min/max corner of parts in `space` (object space of a CFrame)
local function bounds(parts: { BasePart }, space: CFrame): (Vector3, Vector3)
	local lo, hi = Vector3.one * math.huge, -Vector3.one * math.huge
	for _, p in parts do
		local h = p.Size / 2
		for _, s in { Vector3.new(1, 1, 1), Vector3.new(1, 1, -1), Vector3.new(1, -1, 1), Vector3.new(1, -1, -1),
			Vector3.new(-1, 1, 1), Vector3.new(-1, 1, -1), Vector3.new(-1, -1, 1), Vector3.new(-1, -1, -1) } do
			local v = space:PointToObjectSpace(p.CFrame:PointToWorldSpace(h * s))
			lo, hi = lo:Min(v), hi:Max(v)
		end
	end
	return lo, hi
end

local function bricks(model: Model): { BasePart }
	local out = {}
	for _, p in model:GetChildren() do
		if p:IsA("BasePart") and p ~= model.PrimaryPart then
			table.insert(out, p)
		end
	end
	return out
end

local function recolor(parts: { BasePart }, mutation: string, pivot: CFrame, lo: Vector3, span: Vector3)
	for _, p in parts do
		local l = lum(p.Color)
		if p.Material == Enum.Material.Neon or l < 0.12 then
			continue -- eyes, noses and glowing bits keep their look
		end
		if mutation == "Golden" then
			p.Color = GOLD_DARK:Lerp(GOLD_LIGHT, math.clamp((l - 0.12) / 0.8, 0, 1))
			p.Reflectance = 0.25
		elseif mutation == "Rainbow" then
			p:SetAttribute("Shade", 0.55 + 0.45 * l) -- keeps the pet's light/dark detail while the color cycles
			p.Color = RAINBOW[1]:Lerp(Color3.new(), 0.45 - 0.45 * l)
		elseif mutation == "Cosmic" then
			if l > 0.82 then
				p.Material = Enum.Material.Neon
				p.Color = STARLIGHT
			else
				p.Color = SPACE_DARK:Lerp(SPACE_LIGHT, l ^ 1.5)
			end
		end
	end
end

local function attachProp(model: Model, mutation: string, parts: { BasePart }, pivot: CFrame, lo: Vector3, hi: Vector3)
	local tpl = Models:FindFirstChild(PROP[mutation])
	if not tpl then
		return
	end
	local prop = tpl:Clone()
	local pparts = bricks(prop)
	local plo, phi = bounds(pparts, prop:GetPivot())
	local psize = phi - plo
	local span, mid = hi - lo, (lo + hi) / 2
	local bone, scale, place
	if mutation == "Golden" then -- crown sits on top of the head
		local head = {}
		for _, p in parts do
			if p.Name == "head" then
				table.insert(head, p)
			end
		end
		local hlo, hhi = bounds(#head > 0 and head or parts, pivot)
		local hmid = (hlo + hhi) / 2
		bone, scale = "head", (hhi.X - hlo.X) * 0.7 / psize.X
		place = pivot * CFrame.new(hmid.X, hhi.Y - 0.08 * scale, hmid.Z)
	elseif mutation == "Rainbow" then -- arc over the back, nose to tail
		bone, scale = "body", math.max(span.Z * 1.2 / psize.X, span.Y * 1.3 / psize.Y) -- clears the whole pet
		place = pivot * CFrame.new(mid.X, lo.Y, mid.Z) * CFrame.Angles(0, math.pi / 2, 0)
	else -- cosmic ring around the middle, tilted like a planet's
		bone, scale = "body", math.max(span.X, span.Z) * 1.35 / psize.X
		place = pivot * CFrame.new(mid.X, lo.Y + span.Y * 0.45 - psize.Y * scale / 2, mid.Z) * CFrame.Angles(math.rad(16), 0, math.rad(8))
	end
	prop:ScaleTo(math.max(scale, 0.05))
	prop:PivotTo(place * CFrame.new(0, -plo.Y * math.max(scale, 0.05), 0))
	for _, p in bricks(prop) do
		p.Name = bone -- the pet animator moves it with that bone (crown bobs with the head)
		p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = true, false, false, false
		p.Parent = model
	end
	prop:Destroy()
end

-- Apply once to a pet model that is already scaled and placed.
function Mutations.Apply(model: Model, mutation: string?)
	if not mutation or not PROP[mutation] or model:GetAttribute("Mutated") then
		return
	end
	model:SetAttribute("Mutated", mutation)
	local parts = bricks(model)
	local pivot = model:GetPivot()
	local lo, hi = bounds(parts, pivot)
	recolor(parts, mutation, pivot, lo, hi - lo)
	attachProp(model, mutation, parts, pivot, lo, hi)
end

-- Rainbow pets fade through red -> blue -> green: returns the bricks to recolor each frame with Mutations.Shimmer.
function Mutations.RainbowParts(model: Model): { BasePart }
	local out = {}
	for _, p in model:GetChildren() do
		if p:IsA("BasePart") and p:GetAttribute("Shade") then
			table.insert(out, p)
		end
	end
	return out
end

function Mutations.RainbowColor(t: number): Color3
	local x = (t / RAINBOW_STEP) % #RAINBOW
	local i = math.floor(x)
	local f = x - i
	f = f * f * (3 - 2 * f) -- smoothstep: holds each color a moment, then glides to the next
	return RAINBOW[i + 1]:Lerp(RAINBOW[(i + 1) % #RAINBOW + 1], f)
end
assert(Mutations.RainbowColor(0) == RAINBOW[1] and Mutations.RainbowColor(RAINBOW_STEP) == RAINBOW[2], "RainbowColor self-check failed")

function Mutations.Shimmer(parts: { BasePart }, t: number)
	if #parts == 0 then
		return
	end
	local c = Mutations.RainbowColor(t)
	for _, p in parts do
		p.Color = c:Lerp(Color3.new(), 1 - (p:GetAttribute("Shade") :: number))
	end
end

return Mutations
