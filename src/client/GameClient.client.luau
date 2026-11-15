-- Throw a Toy: client. HUD, throw meter, throw camera + VFX, reveal, shop, animals, index, training, pet idle anims.
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UIS = game:GetService("UserInputService")
local Lighting = game:GetService("Lighting")
local SoundService = game:GetService("SoundService")
local CollectionService = game:GetService("CollectionService")

local player = Players.LocalPlayer
local Shared = RS:WaitForChild("Shared")
local Config = require(Shared:WaitForChild("Config"))
local Util = require(Shared:WaitForChild("Util"))
local PetRig = require(Shared:WaitForChild("PetRig"))
local ThrowAnim = require(Shared:WaitForChild("ThrowAnim"))
local Mutations = require(Shared:WaitForChild("Mutations"))
local Models = RS:WaitForChild("Models")
local Sounds = RS:WaitForChild("Sounds")
local Remotes = RS:WaitForChild("Remotes")
local Map = workspace:WaitForChild("Map")
local ThrowPad = Map:WaitForChild("ThrowPad") :: BasePart

local Data = nil -- latest server snapshot
local busy = false -- mid-throw
local camera = workspace.CurrentCamera

-- ===================== PET ANIMATOR =====================
-- Pets are bricks named by bone; each bone rotates about its Blender pivot (PetRig). One BulkMoveTo per pet per frame.
type Rig = { Model: Model, Root: BasePart, Parts: { any }, Pivots: { [string]: Vector3 }, Phase: number }
local function buildRig(model: Model): Rig?
	local root = model.PrimaryPart
	if not root then
		return nil
	end
	local piv = PetRig[model:GetAttribute("Animal") or model.Name] or {}
	local scale = model:GetScale()
	local parts = {}
	for _, p in model:GetChildren() do
		if p:IsA("BasePart") and p ~= root then
			table.insert(parts, { p, p.Name, root.CFrame:ToObjectSpace(p.CFrame) })
		end
	end
	local pivots = {}
	for bone, v in piv do
		pivots[bone] = v * scale
	end
	return { Model = model, Root = root, Parts = parts, Pivots = pivots, Phase = math.random() * 10 }
end

local function boneRot(bone: string, t: number, walk: boolean): CFrame?
	local side = bone:sub(-1) == "L" and 1 or -1
	if bone == "tail" then
		return CFrame.Angles(0, math.sin(t * (walk and 14 or 6)) * 0.45, 0)
	elseif bone == "head" then
		return walk and CFrame.Angles(math.sin(t * 12) * 0.06, 0, 0) or CFrame.Angles(math.sin(t * 1.3) * 0.07, math.sin(t * 0.45) * 0.3, 0)
	elseif bone:sub(1, 3) == "ear" then
		return CFrame.Angles(0, 0, side * math.sin(t * 2.2) ^ 8 * 0.35)
	elseif bone:sub(1, 4) == "wing" then
		return CFrame.Angles(0, 0, side * math.sin(t * (walk and 14 or 3)) * (walk and 0.6 or 0.18))
	elseif bone:sub(1, 3) == "leg" then
		if not walk then
			return nil
		end
		local diag = (bone == "legFL" or bone == "legBR") and 0 or math.pi
		return CFrame.Angles(math.sin(t * 14 + diag) * 0.6, 0, 0)
	elseif bone:sub(1, 3) == "arm" then
		return CFrame.Angles(math.sin(t * (walk and 12 or 1.6)) * (walk and 0.6 or 0.08) * side, 0, 0)
	end
	return nil
end

local function pose(rig: Rig, rootCF: CFrame, t: number, walk: boolean)
	local parts, cfs, cache = {}, {}, {}
	t += rig.Phase
	for _, e in rig.Parts do
		local bone = e[2]
		local b = cache[bone]
		if b == nil then
			local r = boneRot(bone, t, walk)
			local pv = rig.Pivots[bone]
			b = (r and pv) and (CFrame.new(pv) * r * CFrame.new(-pv)) or false
			cache[bone] = b
		end
		table.insert(parts, e[1])
		table.insert(cfs, rootCF * (b and b * e[3] or e[3]))
	end
	table.insert(parts, rig.Root)
	table.insert(cfs, rootCF)
	workspace:BulkMoveTo(parts, cfs, Enum.BulkMoveMode.FireCFrameChanged)
end

-- ===================== SOUND =====================
local function play(name: string, pitch: number?, volume: number?)
	local s = Sounds:FindFirstChild(name)
	if not s or s.SoundId == "" then
		return
	end
	local c = s:Clone()
	c.PlaybackSpeed = pitch or 1
	if volume then
		c.Volume = volume
	end
	c.Parent = SoundService
	c:Play()
	c.Ended:Once(function()
		c:Destroy()
	end)
	task.delay(10, function()
		if c.Parent then
			c:Destroy()
		end
	end)
end

do
	local music = Sounds:FindFirstChild("Music")
	if music and music.SoundId ~= "" then
		local m = music:Clone()
		m.Looped = true
		m.Volume = 0.25
		m.Parent = SoundService
		m:Play()
	end
end

-- ===================== UI KIT =====================
local FONT = Enum.Font.FredokaOne
local C = {
	Pink = Color3.fromRGB(255, 70, 190), Purple = Color3.fromRGB(150, 70, 255), Dark = Color3.fromRGB(28, 26, 40),
	Panel = Color3.fromRGB(42, 38, 62), Green = Color3.fromRGB(70, 220, 90), Red = Color3.fromRGB(240, 60, 70),
	Orange = Color3.fromRGB(255, 150, 30), Gold = Color3.fromRGB(255, 205, 50), White = Color3.new(1, 1, 1),
	Blue = Color3.fromRGB(60, 150, 255),
}

local function make(class: string, props: { [string]: any }?, children: { Instance }?): any
	local inst = Instance.new(class)
	for k, v in props or {} do
		if k ~= "Parent" and k ~= "StrokeSize" and k ~= "Radius" then -- helper-only keys
			(inst :: any)[k] = v
		end
	end
	for _, ch in children or {} do
		ch.Parent = inst
	end
	if props and props.Parent then
		inst.Parent = props.Parent
	end
	return inst
end

local function corner(r: number?)
	return make("UICorner", { CornerRadius = UDim.new(0, r or 12) })
end
local function stroke(th: number?, col: Color3?)
	return make("UIStroke", { Thickness = th or 3, Color = col or C.Dark, ApplyStrokeMode = Enum.ApplyStrokeMode.Border })
end
local function textStroke(th: number?)
	return make("UIStroke", { Thickness = th or 2.5, Color = C.Dark })
end
local function gradient(a: Color3, b: Color3, rot: number?)
	return make("UIGradient", { Color = ColorSequence.new(a, b), Rotation = rot or 90 })
end
local function label(props): TextLabel
	props.BackgroundTransparency = props.BackgroundTransparency or 1
	props.Font = props.Font or FONT
	props.TextColor3 = props.TextColor3 or C.White
	props.TextScaled = props.TextScaled ~= false
	props.RichText = true
	local l = make("TextLabel", props, { textStroke(props.StrokeSize) })
	return l
end

local function bounce(gui: GuiObject)
	local sc = gui:FindFirstChild("BounceScale") or make("UIScale", { Name = "BounceScale", Parent = gui })
	sc.Scale = 0.88
	TweenService:Create(sc, TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
end

local function button(props, onClick: () -> ()): TextButton
	local color = props.Color or C.Green
	props.Color = nil
	props.AutoButtonColor = false
	props.BackgroundColor3 = C.White
	props.Font = FONT
	props.TextColor3 = C.White
	props.TextScaled = true
	props.RichText = true
	local b = make("TextButton", props, {
		corner(props.Radius or 12), stroke(3), gradient(color:Lerp(C.White, 0.25), color, 90),
		make("UIStroke", { Thickness = 2.5, Color = C.Dark, ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual }),
		make("UIPadding", { PaddingTop = UDim.new(0.14, 0), PaddingBottom = UDim.new(0.14, 0), PaddingLeft = UDim.new(0, 6), PaddingRight = UDim.new(0, 6) }),
	})
	local sc = make("UIScale", { Parent = b })
	b.MouseEnter:Connect(function()
		TweenService:Create(sc, TweenInfo.new(0.12), { Scale = 1.06 }):Play()
	end)
	b.MouseLeave:Connect(function()
		TweenService:Create(sc, TweenInfo.new(0.12), { Scale = 1 }):Play()
	end)
	b.MouseButton1Down:Connect(function()
		TweenService:Create(sc, TweenInfo.new(0.06), { Scale = 0.93 }):Play()
	end)
	b.Activated:Connect(function()
		TweenService:Create(sc, TweenInfo.new(0.2, Enum.EasingStyle.Back), { Scale = 1 }):Play()
		play("Click")
		onClick()
	end)
	return b
end

local function setButtonColor(b: TextButton, color: Color3)
	local g = b:FindFirstChildOfClass("UIGradient")
	if g then
		g.Color = ColorSequence.new(color:Lerp(C.White, 0.25), color)
	end
end

-- 3D thumbnail of a model in a ViewportFrame
local function viewport(name: string, parent: Instance, silhouette: boolean?, front: boolean?, mutation: string?): ViewportFrame?
	local template = Models:FindFirstChild(name)
	if not template then
		return nil
	end
	local vf = make("ViewportFrame", {
		Size = UDim2.fromScale(1, 1), BackgroundTransparency = 1, Ambient = front and Color3.fromRGB(235, 235, 240) or Color3.fromRGB(180, 180, 190),
		LightColor = Color3.new(1, 1, 1), LightDirection = Vector3.new(-1, -1.4, -1.2),
		ImageColor3 = silhouette and Color3.new(0, 0, 0) or C.White, Parent = parent,
	})
	local m = template:Clone()
	m:PivotTo(CFrame.new())
	Mutations.Apply(m, mutation)
	m.Parent = vf
	local cf, size = m:GetBoundingBox()
	local cam = make("Camera", { FieldOfView = 30, Parent = vf })
	vf.CurrentCamera = cam
	local r = math.max(size.X, size.Y, size.Z)
	-- models face -Z: pets are seen from the front-left like the original's index cards, icons straight on
	local dir = (front and Vector3.new(0.2, 0.15, -1) or Vector3.new(-0.6, 0.3, -1)).Unit
	cam.CFrame = CFrame.lookAt(cf.Position + dir * r * 2.1, cf.Position)
	return vf
end

-- ===================== SCREEN GUI =====================
local gui = make("ScreenGui", { Name = "ThrowAToyUI", ResetOnSpawn = false, IgnoreGuiInset = true, ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Parent = player:WaitForChild("PlayerGui") })
local hud = make("Frame", { Name = "HUD", Size = UDim2.fromScale(1, 1), BackgroundTransparency = 1, Parent = gui })
local overlay = make("Frame", { Name = "Overlay", Size = UDim2.fromScale(1, 1), BackgroundTransparency = 1, Parent = gui })

-- toasts
local toastHolder = make("Frame", { Size = UDim2.new(0.5, 0, 0.5, 0), Position = UDim2.fromScale(0.25, 0.1), BackgroundTransparency = 1, Parent = overlay },
	{ make("UIListLayout", { HorizontalAlignment = Enum.HorizontalAlignment.Center, Padding = UDim.new(0, 6) }) })
local function toast(text: string, kind: string?)
	local col = ({ good = C.Green, bad = C.Red, warn = C.Orange })[kind or ""] or C.White
	local t = label({ Text = text, Size = UDim2.new(1, 0, 0, 34), TextColor3 = col, Parent = toastHolder, TextTransparency = 1 })
	TweenService:Create(t, TweenInfo.new(0.2), { TextTransparency = 0 }):Play()
	bounce(t)
	if kind == "bad" or kind == "warn" then
		play("Error")
	end
	task.delay(3, function()
		TweenService:Create(t, TweenInfo.new(0.4), { TextTransparency = 1 }):Play()
		local s = t:FindFirstChildOfClass("UIStroke")
		if s then
			TweenService:Create(s, TweenInfo.new(0.4), { Transparency = 1 }):Play()
		end
		task.wait(0.45)
		t:Destroy()
	end)
end
Remotes.Notify.OnClientEvent:Connect(toast)

-- side buttons
local function sideButton(name: string, icon: string, pos: UDim2, color: Color3, onClick: () -> ())
	local holder = make("Frame", { Size = UDim2.fromOffset(96, 96), Position = pos, BackgroundTransparency = 1, Parent = hud })
	local b = button({ Size = UDim2.fromScale(1, 1), Text = "", Color = color, Radius = 18, Parent = holder }, onClick)
	local iconHolder = make("Frame", { Size = UDim2.fromScale(0.86, 0.72), Position = UDim2.fromScale(0.07, -0.04), BackgroundTransparency = 1, Parent = b })
	viewport(icon, iconHolder, false, true)
	label({ Text = name, Size = UDim2.fromScale(1.15, 0.36), Position = UDim2.fromScale(-0.075, 0.68), Parent = b })
	return b
end

-- stats bottom-left
local stats = make("Frame", { Size = UDim2.fromOffset(300, 120), Position = UDim2.new(0, 14, 1, -132), BackgroundTransparency = 1, Parent = hud },
	{ make("UIListLayout", { Padding = UDim.new(0, 2), VerticalAlignment = Enum.VerticalAlignment.Bottom }) })
local function statRow(icon: string, h: number, color: Color3): TextLabel
	local row = make("Frame", { Size = UDim2.new(1, 0, 0, h), BackgroundTransparency = 1, Parent = stats })
	local ic = make("Frame", { Size = UDim2.fromOffset(h + 6, h + 6), Position = UDim2.fromOffset(-4, -3), BackgroundTransparency = 1, Parent = row })
	viewport(icon, ic, false, true)
	return label({ Size = UDim2.new(1, -h - 6, 1, 0), Position = UDim2.fromOffset(h + 6, 0), TextXAlignment = Enum.TextXAlignment.Left, TextColor3 = color, Parent = row })
end
local powerLabel = statRow("Icon Muscle", 38, Color3.fromRGB(110, 210, 255))
local cashLabel = statRow("Icon Coin", 44, Color3.fromRGB(120, 255, 110))
local incomeLabel = label({ Text = "+$0/s", Size = UDim2.new(1, 0, 0, 24), TextXAlignment = Enum.TextXAlignment.Left, TextColor3 = Color3.fromRGB(200, 255, 190), Parent = stats })

local function updateStats()
	local cash = player:GetAttribute("Cash") or 0
	local power = player:GetAttribute("Power") or 0
	cashLabel.Text = "$" .. Util.Format(cash)
	powerLabel.Text = Util.Format(power)
	incomeLabel.Text = "+$" .. Util.Format(player:GetAttribute("Income") or 0) .. "/s"
end
player:GetAttributeChangedSignal("Cash"):Connect(updateStats)
player:GetAttributeChangedSignal("Income"):Connect(updateStats)
local lastPower = player:GetAttribute("Power") or 0
player:GetAttributeChangedSignal("Power"):Connect(function()
	local p = player:GetAttribute("Power") or 0
	if p > lastPower then
		bounce(powerLabel)
	end
	lastPower = p
	updateStats()
end)

-- luck boost button (top right)
local luckBtn = button({ Size = UDim2.fromOffset(190, 64), Position = UDim2.new(1, -206, 0, 70), Color = C.Purple, Text = "🍀 100x LUCK", Visible = Config.LuckProductId ~= 0, Parent = hud }, function()
	Remotes.Request:InvokeServer("BuyLuck")
end)
local luckTimer = label({ Text = "", Size = UDim2.new(1, 0, 0, 22), Position = UDim2.new(0, 0, 1, 4), TextColor3 = C.Gold, Parent = luckBtn })

-- ===================== PANELS =====================
local openPanel: Frame? = nil
local function panel(title: string, color: Color3): (Frame, Frame)
	local f = make("Frame", { Size = UDim2.fromScale(0.62, 0.66), Position = UDim2.fromScale(0.5, 0.5), AnchorPoint = Vector2.new(0.5, 0.5),
		BackgroundColor3 = C.Panel, Visible = false, Parent = gui }, {
		corner(18), stroke(4),
		make("UISizeConstraint", { MaxSize = Vector2.new(860, 560), MinSize = Vector2.new(340, 300) }),
	})
	local header = make("Frame", { Size = UDim2.new(1, 0, 0, 62), BackgroundColor3 = C.White, Parent = f }, { corner(18), gradient(color:Lerp(C.White, 0.2), color, 0), stroke(4) })
	label({ Text = title, Size = UDim2.new(0.7, 0, 0.75, 0), Position = UDim2.new(0, 20, 0.12, 0), TextXAlignment = Enum.TextXAlignment.Left, Parent = header, StrokeSize = 3 })
	local closeBtn
	closeBtn = button({ Size = UDim2.fromOffset(48, 48), Position = UDim2.new(1, -56, 0, 7), Text = "X", Color = C.Red, Parent = header }, function()
		f.Visible = false
		openPanel = nil
	end)
	local body = make("Frame", { Size = UDim2.new(1, -28, 1, -84), Position = UDim2.new(0, 14, 0, 72), BackgroundTransparency = 1, Parent = f })
	return f, body
end
local function toggle(f: Frame, onOpen: (() -> ())?)
	if openPanel and openPanel ~= f then
		openPanel.Visible = false
	end
	f.Visible = not f.Visible
	openPanel = f.Visible and f or nil
	if f.Visible then
		play("Open")
		local sc = f:FindFirstChild("PopScale") or make("UIScale", { Name = "PopScale", Parent = f })
		sc.Scale = 0.7
		TweenService:Create(sc, TweenInfo.new(0.35, Enum.EasingStyle.Back), { Scale = 1 }):Play()
		if onOpen then
			onOpen()
		end
	end
end

-- ---------- SHOP ----------
local shopFrame, shopBody = panel("🧸 Toy Shop", C.Pink)
local shopList = make("ScrollingFrame", { Size = UDim2.fromScale(1, 1), BackgroundTransparency = 1, ScrollBarThickness = 8, CanvasSize = UDim2.new(),
	AutomaticCanvasSize = Enum.AutomaticSize.X, ScrollingDirection = Enum.ScrollingDirection.X, Parent = shopBody },
	{ make("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 14), VerticalAlignment = Enum.VerticalAlignment.Center }) })
local shopCards = {}
for _, toy in Config.Toys do
	local rc = Config.Rarities[Config.RarityIndex[toy.Rarity]].Color
	local card = make("Frame", { Size = UDim2.new(0, 190, 0.95, 0), BackgroundColor3 = C.White, Parent = shopList },
		{ corner(16), stroke(4), gradient(rc:Lerp(C.White, 0.35), rc:Lerp(C.Dark, 0.25), 90) })
	label({ Text = toy.Name, Size = UDim2.new(0.92, 0, 0.12, 0), Position = UDim2.fromScale(0.04, 0.03), Parent = card })
	label({ Text = toy.Rarity, Size = UDim2.new(0.8, 0, 0.08, 0), Position = UDim2.fromScale(0.1, 0.15), TextColor3 = rc:Lerp(C.White, 0.5), Parent = card })
	local vpHolder = make("Frame", { Size = UDim2.fromScale(0.8, 0.42), Position = UDim2.fromScale(0.1, 0.24), BackgroundTransparency = 1, Parent = card })
	viewport(toy.Name, vpHolder)
	label({ Text = "🍀 x" .. toy.Luck .. " Luck", Size = UDim2.new(0.9, 0, 0.09, 0), Position = UDim2.fromScale(0.05, 0.67), TextColor3 = C.Gold, Parent = card })
	local b
	b = button({ Size = UDim2.new(0.86, 0, 0.17, 0), Position = UDim2.fromScale(0.07, 0.79), Text = "", Parent = card }, function()
		local ok, msg = Remotes.Request:InvokeServer("BuyToy", toy.Name)
		if msg then
			toast(msg, ok and "good" or "bad")
		end
		if ok then
			play("Buy")
		end
	end)
	shopCards[toy.Name] = b
end
local function refreshShop()
	if not Data then
		return
	end
	for name, b in shopCards do
		local toy = Config.ToyInfo[name]
		if Data.Toy == name then
			b.Text = "EQUIPPED"
			setButtonColor(b, C.Blue)
		elseif Data.Toys[name] then
			b.Text = "EQUIP"
			setButtonColor(b, C.Green)
		else
			b.Text = toy.Price == 0 and "FREE" or ("$" .. Util.Format(toy.Price))
			setButtonColor(b, Data.Cash >= toy.Price and C.Green or C.Red)
		end
	end
end

-- ---------- ROBUX SHOP ----------
-- Layout follows the Figma "Roblox shop" frame: every box below is that frame's pixel rect, turned into scale so the
-- whole sheet resizes with the screen. Art is the game's own brick models in ViewportFrames.
local ROBUX = "rbxasset://textures/ui/common/robux.png"
local SH = {
	Head1 = Color3.fromRGB(255, 166, 30), Head2 = Color3.fromRGB(255, 205, 60), Bg = Color3.fromRGB(22, 22, 30),
	Tab = Color3.fromRGB(44, 46, 60), TabOn = Color3.fromRGB(140, 80, 255), Lime = Color3.fromRGB(95, 215, 25),
	Muted = Color3.fromRGB(170, 175, 195), Gold = Color3.fromRGB(255, 200, 40), Mint = Color3.fromRGB(110, 230, 140),
}
local function rect(props, x: number, y: number, w: number, h: number, pw: number, ph: number)
	props.Size = UDim2.fromScale(w / pw, h / ph)
	props.Position = UDim2.fromScale(x / pw, y / ph)
	return props
end
local function shopBuy(key: string)
	local ok, msg = Remotes.Request:InvokeServer("BuyShop", key)
	if msg then
		toast(msg, ok and "good" or "bad")
	end
end
local function robuxButton(parent: Instance, robux: number, key: string, x, y, w, h, pw, ph): TextButton
	local b = button(rect({ Text = "", Color = SH.Lime, Parent = parent }, x, y, w, h, pw, ph), function()
		shopBuy(key)
	end)
	local row = make("Frame", { Size = UDim2.fromScale(1, 1), BackgroundTransparency = 1, Parent = b }, {
		make("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Center,
			VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0.03, 0), SortOrder = Enum.SortOrder.LayoutOrder }),
	})
	make("ImageLabel", { Image = ROBUX, Size = UDim2.fromScale(0.85, 0.85), SizeConstraint = Enum.SizeConstraint.RelativeYY,
		BackgroundTransparency = 1, LayoutOrder = 1, Parent = row })
	label({ Text = tostring(robux), Size = UDim2.fromScale(0.3, 1.25), LayoutOrder = 2, Parent = row, StrokeSize = 3 })
	return b
end
local function card(parent: Instance, c1: Color3, c2: Color3, x, y, w, h, pw, ph): Frame
	return make("Frame", rect({ BackgroundColor3 = C.White, Parent = parent }, x, y, w, h, pw, ph),
		{ corner(18), stroke(4, c1:Lerp(C.White, 0.55)), gradient(c1, c2, 20) })
end
local function art(parent: Instance, model: string, x, y, w, h, pw, ph)
	-- cash stacks read better from the 3/4 angle; everything else straight on
	viewport(model, make("Frame", rect({ BackgroundTransparency = 1, Parent = parent }, x, y, w, h, pw, ph)), false, model ~= "Icon Cash")
end
local function caption(parent: Instance, text: string, color: Color3?, x, y, w, h, pw, ph, align: Enum.TextXAlignment?): TextLabel
	return label(rect({ Text = text, TextColor3 = color, TextXAlignment = align or Enum.TextXAlignment.Left, Parent = parent }, x, y, w, h, pw, ph))
end
local function flat(l: TextLabel) -- small grey sub-captions have no outline in the design
	l.UIStroke.Enabled = false
end
local sized = {} -- [section] = height / width; heights follow the width (UIAspectRatioConstraint collapses in a list)
local function section(parent: Instance, order: number, w: number, h: number): Frame
	local f = make("Frame", { Size = UDim2.fromScale(1, 0), BackgroundTransparency = 1, LayoutOrder = order, Parent = parent })
	sized[f] = h / w
	return f
end

local robuxFrame = make("Frame", { Size = UDim2.fromScale(0.9, 0.9), Position = UDim2.fromScale(0.5, 0.5), AnchorPoint = Vector2.new(0.5, 0.5),
	BackgroundColor3 = SH.Bg, Visible = false, Parent = gui }, {
	corner(22), stroke(5, C.Dark),
	make("UIAspectRatioConstraint", { AspectRatio = 1200 / 1100 }),
	make("UISizeConstraint", { MaxSize = Vector2.new(1000, 920) }),
})
do -- header (Figma: 1200 x 104)
	local head = make("Frame", { Size = UDim2.fromScale(1, 104 / 1100), BackgroundColor3 = C.White, Parent = robuxFrame },
		{ corner(22), gradient(SH.Head1, SH.Head2, 0) })
	caption(head, "SHOP", nil, 30, 14, 160, 76, 1200, 104)
	flat(caption(head, "Upgrade your adventure!", Color3.fromRGB(110, 60, 0), 226, 34, 300, 32, 1200, 104))
	button(rect({ Text = "X", Color = C.Red, Parent = head }, 1092, 17, 76, 68, 1200, 104), function()
		robuxFrame.Visible = false
		openPanel = nil
	end)
end
local scroll = make("ScrollingFrame", { Size = UDim2.fromScale(1, 1 - 178 / 1100), Position = UDim2.fromScale(0, 178 / 1100), BackgroundTransparency = 1,
	ScrollBarThickness = 8, CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, Parent = robuxFrame }, {
	make("UIListLayout", { Padding = UDim.new(0, 18), SortOrder = Enum.SortOrder.LayoutOrder, HorizontalAlignment = Enum.HorizontalAlignment.Center }),
	make("UIPadding", { PaddingLeft = UDim.new(32 / 1200, 0), PaddingRight = UDim.new(32 / 1200, 0), PaddingTop = UDim.new(0, 14), PaddingBottom = UDim.new(0, 20) }),
})

-- FEATURED: title row, then one card per egg (Figma: 1136 wide; enchanted 346 tall, rainbow 210)
local sections = {}
do
	local s = section(scroll, 1, 1136, 40)
	sections.Featured = s
	caption(s, "FEATURED", nil, 0, 0, 160, 36, 1136, 40)
	flat(caption(s, "Fresh finds. Big upgrades.", SH.Muted, 174, 8, 260, 26, 1136, 40))
	local resets = caption(s, "", SH.Gold, 760, 6, 340, 26, 1136, 40, Enum.TextXAlignment.Right)
	task.spawn(function()
		while true do
			local left = 86400 - os.time() % 86400 -- next UTC midnight
			resets.Text = string.format("RESETS IN  %02d:%02d:%02d", left // 3600, left // 60 % 60, left % 60)
			task.wait(1)
		end
	end)
end
for i, egg in Config.Shop.Eggs do
	local big = #egg.Buy >= 3
	local W, H = 1136, big and 346 or 210
	local s = section(scroll, 1 + i, W, H)
	if i == 2 then
		sections.Eggs = s
	end
	local f = big and card(s, Color3.fromRGB(176, 72, 245), Color3.fromRGB(110, 60, 230), 0, 0, W, H, W, H)
		or card(s, C.White, C.White, 0, 0, W, H, W, H)
	if not big then -- rainbow sheen like the Figma card
		f.UIGradient.Color = ColorSequence.new({
			ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 120, 150)), ColorSequenceKeypoint.new(0.25, Color3.fromRGB(255, 215, 70)),
			ColorSequenceKeypoint.new(0.5, Color3.fromRGB(120, 230, 160)), ColorSequenceKeypoint.new(0.75, Color3.fromRGB(110, 180, 255)),
			ColorSequenceKeypoint.new(1, Color3.fromRGB(230, 130, 255)) })
	end
	make("Frame", rect({ BackgroundColor3 = C.White, BackgroundTransparency = 0.82, Parent = f }, big and 18 or 40, big and 48 or 30, big and 278 or 170, big and 278 or 170, W, H),
		{ make("UICorner", { CornerRadius = UDim.new(1, 0) }) })
	art(f, egg.Icon, big and 20 or 40, big and 30 or 20, big and 276 or 180, big and 300 or 186, W, H)
	local badge = make("Frame", rect({ BackgroundColor3 = big and SH.Lime or C.Dark, Parent = f }, 22, 16, big and 90 or 130, 34, W, H), { corner(8), stroke(3) })
	label({ Text = egg.Badge, Size = UDim2.fromScale(0.86, 0.86), Position = UDim2.fromScale(0.07, 0.07), Parent = badge })
	local tx = big and 324 or 234
	caption(f, egg.Name, SH.Gold, tx, big and 18 or 14, 420, big and 58 or 48, W, H)
	caption(f, egg.Blurb, nil, tx + 2, big and 80 or 66, 430, 30, W, H)
	if big then
		local total = 0
		for _, e in egg.Pool do
			total += e[2]
		end
		local odds = {}
		for _, e in egg.Pool do
			local rc = Config.Rarities[Config.RarityIndex[Config.AnimalInfo[e[1]].Rarity]].Color
			table.insert(odds, string.format('<font color="#%s">%s</font>  %g%%', rc:ToHex(), e[1], math.floor(e[2] / total * 1000 + 0.5) / 10))
		end
		local oddsBox = make("Frame", rect({ BackgroundColor3 = C.Dark, BackgroundTransparency = 0.08, Visible = false, ZIndex = 5, Parent = f }, 760, 74, 350, 240, W, H), { corner(12), stroke(3) })
		label({ Text = table.concat(odds, "\n"), Size = UDim2.fromScale(0.9, 0.9), Position = UDim2.fromScale(0.05, 0.05), ZIndex = 6, TextXAlignment = Enum.TextXAlignment.Left, Parent = oddsBox })
		button(rect({ Text = "ODDS", Color = Color3.fromRGB(50, 30, 110), Parent = f }, 977, 24, 132, 42, W, H), function()
			oddsBox.Visible = not oddsBox.Visible
		end)
		local rarest = egg.Pool[#egg.Pool]
		local chips = {
			{ #egg.Pool .. " EXCLUSIVE PETS", "Only in this egg" },
			{ string.format("%g%% %s", rarest[2] / total * 100, Config.AnimalInfo[rarest[1]].Rarity:upper()), "Chase the rarest" },
			{ "LIMITED DROP", "Get it before it's gone" },
		}
		for k, chip in chips do
			local cf = make("Frame", rect({ BackgroundColor3 = Color3.fromRGB(60, 20, 120), BackgroundTransparency = 0.45, Parent = f }, 326 + (k - 1) * 261, 130, 245, 71, W, H),
				{ corner(10), stroke(2, Color3.fromRGB(200, 150, 255)) })
			caption(cf, chip[1], SH.Gold, 14, 8, 220, 30, 245, 71)
			caption(cf, chip[2], nil, 14, 40, 220, 22, 245, 71)
		end
	end
	for k, b in egg.Buy do
		if big then
			local bx = 326 + (k - 1) * 261
			caption(f, "Buy x" .. b.Count, nil, bx, 212, 245, 30, W, H, Enum.TextXAlignment.Center)
			robuxButton(f, b.Robux, b.Key, bx, 250, 245, 62, W, H)
		else
			local bx = 360 + (k - 1) * 452
			caption(f, "Buy x" .. b.Count, nil, bx - 100, 132, 90, 30, W, H)
			robuxButton(f, b.Robux, b.Key, bx, 118, 300, 62, W, H)
		end
	end
end

-- CASH PACKS (Figma: title row + four 269 x 256 cards)
local cashAmounts = {}
do
	local W, H = 1136, 306
	local s = section(scroll, 10, W, H)
	sections.Cash = s
	caption(s, "CASH PACKS", nil, 0, 0, 180, 36, W, H)
	flat(caption(s, "A little boost goes a long way.", SH.Muted, 200, 8, 300, 26, W, H))
	caption(s, "INSTANT DELIVERY", SH.Mint, 880, 8, 216, 24, W, H, Enum.TextXAlignment.Right)
	local tagColors = { ["GOOD VALUE"] = C.Blue, ["GREAT VALUE"] = C.Orange, ["BEST VALUE"] = C.Pink }
	for k, pack in Config.Shop.CashPacks do
		local cw, ch = 269, 256
		local f = card(s, Color3.fromRGB(90, 225, 100), Color3.fromRGB(40, 175, 70), (k - 1) * 289, 49, cw, ch, W, H)
		art(f, "Icon Cash", 30 - k * 6, 14, 209 + k * 12, 150, cw, ch) -- stacks grow with the pack
		if pack.Tag then
			local col = tagColors[pack.Tag] or C.Blue
			local t = make("Frame", rect({ BackgroundColor3 = C.White, Parent = f }, 14, 10, 241, 31, cw, ch), { corner(8), stroke(3), gradient(col:Lerp(C.White, 0.25), col, 90) })
			label({ Text = pack.Tag, Size = UDim2.fromScale(0.9, 0.8), Position = UDim2.fromScale(0.05, 0.1), Parent = t })
		end
		local amt = make("Frame", rect({ BackgroundColor3 = Color3.fromRGB(20, 110, 40), BackgroundTransparency = 0.3, Parent = f }, 14, 156, 241, 31, cw, ch), { corner(14) })
		cashAmounts[pack] = label({ Text = "", Size = UDim2.fromScale(0.9, 0.95), Position = UDim2.fromScale(0.05, 0.02), Parent = amt })
		robuxButton(f, pack.Robux, pack.Key, 12, 194, 245, 57, cw, ch)
	end
end
local function refreshCashPacks()
	local income, cash = player:GetAttribute("Income") or 0, player:GetAttribute("Cash") or 0
	for pack, l in cashAmounts do
		l.Text = "+$" .. Util.Format(Config.CashPackValue(pack, income, cash))
	end
end
player:GetAttributeChangedSignal("Income"):Connect(refreshCashPacks)
player:GetAttributeChangedSignal("Cash"):Connect(function()
	if robuxFrame.Visible then
		refreshCashPacks()
	end
end)

-- GAMEPASSES (Figma: title row + two 556 x 230 cards)
local passButtons = {}
do
	local W, H = 1136, 300
	local s = section(scroll, 11, W, H)
	sections.Passes = s
	caption(s, "GAMEPASSES", nil, 0, 0, 190, 36, W, H)
	flat(caption(s, "One purchase. Permanent perks.", SH.Muted, 210, 8, 300, 26, W, H))
	local looks = { { Color3.fromRGB(40, 205, 255), Color3.fromRGB(30, 120, 240) }, { Color3.fromRGB(176, 72, 245), Color3.fromRGB(110, 60, 230) } }
	for k, pass in Config.Shop.Passes do
		local cw, ch = 556, 230
		local look = looks[(k - 1) % #looks + 1]
		local f = card(s, look[1], look[2], (k - 1) % 2 * 580, 50 + (k - 1) // 2 * 250, cw, ch, W, H)
		caption(f, pass.Name, nil, 20, 12, 500, 46, cw, ch)
		make("Frame", rect({ BackgroundColor3 = C.White, BackgroundTransparency = 0.8, Parent = f }, 18, 66, 148, 148, cw, ch), { make("UICorner", { CornerRadius = UDim.new(1, 0) }) })
		art(f, pass.Icon, 26, 74, 132, 132, cw, ch)
		caption(f, pass.Text, nil, 199, 70, 330, 74, cw, ch).TextWrapped = true
		passButtons[pass.Key] = robuxButton(f, pass.Robux, pass.Key, 195, 155, 341, 57, cw, ch)
	end
end
local function refreshPasses()
	for key, b in passButtons do
		local owned = Data and Data.Passes and Data.Passes[key]
		setButtonColor(b, owned and C.Blue or SH.Lime)
		for _, d in b:GetDescendants() do
			if d:IsA("TextLabel") then
				d.Text = owned and "OWNED" or tostring(Config.ShopItem[key].Robux)
			elseif d:IsA("ImageLabel") then
				d.Visible = not owned
			end
		end
	end
end

do -- footer
	local s = section(scroll, 12, 1136, 40)
	flat(caption(s, "All prices in Robux  •  Purchases support future updates", SH.Muted, 0, 8, 520, 26, 1136, 40))
	caption(s, "THANKS FOR PLAYING!", SH.Gold, 800, 8, 300, 26, 1136, 40, Enum.TextXAlignment.Right)
end

do -- tabs (Figma: 1200 x 74 under the header) scroll to their section
	local tabs = make("Frame", { Size = UDim2.fromScale(1, 74 / 1100), Position = UDim2.fromScale(0, 104 / 1100), BackgroundTransparency = 1, Parent = robuxFrame })
	local list = { { "Featured", sections.Featured, 28, 190 }, { "Eggs", sections.Eggs, 230, 140 }, { "Cash & boosts", sections.Cash, 382, 238 }, { "Gamepasses", sections.Passes, 632, 226 } }
	local btns = {}
	for _, t in list do
		local b
		b = button(rect({ Text = t[1], Color = SH.Tab, Parent = tabs }, t[3], 14, t[4], 46, 1200, 74), function()
			for _, o in btns do
				setButtonColor(o, o == b and SH.TabOn or SH.Tab)
			end
			local y = t[2].AbsolutePosition.Y - scroll.AbsolutePosition.Y + scroll.CanvasPosition.Y - 10
			TweenService:Create(scroll, TweenInfo.new(0.35, Enum.EasingStyle.Quad), { CanvasPosition = Vector2.new(0, math.max(0, y)) }):Play()
		end)
		table.insert(btns, b)
	end
	setButtonColor(btns[1], SH.TabOn)
end

local function fitSections()
	for f, ratio in sized do
		f.Size = UDim2.new(1, 0, 0, math.floor(f.AbsoluteSize.X * ratio))
	end
end
scroll:GetPropertyChangedSignal("AbsoluteSize"):Connect(fitSections)

local function refreshRobuxShop()
	fitSections()
	refreshCashPacks()
	refreshPasses()
end

-- egg hatch reveal: a row of the hatched animals, rarest called out
Remotes.Hatch.OnClientEvent:Connect(function(eggName: string, results)
	if robuxFrame.Visible then
		robuxFrame.Visible = false
		openPanel = nil
	end
	local best = 0
	local n = math.min(#results, 10)
	local holder = make("Frame", { Size = UDim2.fromOffset(math.min(n, 5) * 150 + 30, (n > 5 and 2 or 1) * 170 + 80), Position = UDim2.fromScale(0.5, 0.45),
		AnchorPoint = Vector2.new(0.5, 0.5), BackgroundColor3 = SH.Bg, Parent = overlay }, { corner(20), stroke(5, SH.TabOn) })
	label({ Text = eggName .. (n > 1 and (" x" .. n) or ""), Size = UDim2.new(1, -20, 0, 50), Position = UDim2.fromOffset(10, 10), TextColor3 = SH.Gold, Parent = holder })
	for k = 1, n do
		local a = results[k]
		local ri = Config.RarityIndex[Config.AnimalInfo[a.Name].Rarity]
		best = math.max(best, ri)
		local rc = Config.Rarities[ri].Color
		local cell = make("Frame", { Size = UDim2.fromOffset(140, 160), Position = UDim2.fromOffset(15 + (k - 1) % 5 * 150, 66 + (k - 1) // 5 * 170),
			BackgroundColor3 = C.White, Parent = holder }, { corner(14), stroke(3), gradient(rc:Lerp(C.White, 0.3), rc:Lerp(C.Dark, 0.3), 90) })
		local vp = make("Frame", { Size = UDim2.fromScale(0.9, 0.62), Position = UDim2.fromScale(0.05, 0.02), BackgroundTransparency = 1, Parent = cell })
		viewport(a.Name, vp, nil, nil, a.Mutation)
		label({ Text = a.Name, Size = UDim2.fromScale(0.94, 0.17), Position = UDim2.fromScale(0.03, 0.64), Parent = cell })
		if a.Odds and a.Odds >= Config.OneInMin then
			label({ Text = "1 in " .. Util.Format(a.Odds), Size = UDim2.fromScale(0.9, 0.16), Position = UDim2.fromScale(0.05, 0.02), TextColor3 = SH.Gold, Parent = cell })
		end
		local tags = {}
		if a.Size ~= "Normal" then
			table.insert(tags, a.Size)
		end
		if a.Mutation ~= "None" then
			table.insert(tags, a.Mutation)
		end
		label({ Text = #tags > 0 and table.concat(tags, " "):upper() or Config.Rarities[ri].Name, Size = UDim2.fromScale(0.94, 0.14), Position = UDim2.fromScale(0.03, 0.82), TextColor3 = SH.Gold, Parent = cell })
		bounce(cell)
	end
	bounce(holder)
	play(best >= 5 and "Legendary" or (best >= 3 and "Rare" or "Catch"))
	task.delay(4.5, function()
		holder:Destroy()
	end)
end)

-- ---------- ANIMALS ----------
local animalsFrame, animalsBody = panel("🐾 My Animals", C.Orange)
local plotCount = label({ Text = "ON YOUR PLOT 0/6", Size = UDim2.new(0.6, 0, 0, 30), TextXAlignment = Enum.TextXAlignment.Left, TextColor3 = C.Gold, Parent = animalsBody })
local animalsList = make("ScrollingFrame", { Size = UDim2.new(1, 0, 1, -100), Position = UDim2.new(0, 0, 0, 36), BackgroundTransparency = 1, ScrollBarThickness = 8,
	CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, Parent = animalsBody },
	{ make("UIGridLayout", { CellSize = UDim2.new(0.5, -8, 0, 92), CellPadding = UDim2.fromOffset(8, 8), SortOrder = Enum.SortOrder.LayoutOrder }) })
button({ Size = UDim2.new(0.48, 0, 0, 52), Position = UDim2.new(0, 0, 1, -56), Text = "⭐ EQUIP BEST", Color = C.Orange, Parent = animalsBody }, function()
	local ok, msg = Remotes.Request:InvokeServer("EquipBest")
	if msg then
		toast(msg, ok and "good" or "bad")
	end
end)
button({ Size = UDim2.new(0.48, 0, 0, 52), Position = UDim2.new(0.52, 0, 1, -56), Text = "💰 SELL BACKPACK", Color = C.Red, Parent = animalsBody }, function()
	local ok, msg = Remotes.Request:InvokeServer("SellBackpack")
	if msg then
		toast(msg, ok and "good" or "bad")
	end
	if ok then
		play("Buy")
	end
end)

local function refreshAnimals()
	if not Data or not animalsFrame.Visible then
		return
	end
	for _, ch in animalsList:GetChildren() do
		if ch:IsA("Frame") then
			ch:Destroy()
		end
	end
	local placed = 0
	local sorted = table.clone(Data.Animals)
	table.sort(sorted, function(a, b)
		if a.Placed ~= b.Placed then
			return a.Placed
		end
		return a.Income > b.Income
	end)
	for i, a in sorted do
		if a.Placed then
			placed += 1
		end
		local info = Config.AnimalInfo[a.Name]
		local rc = Config.Rarities[Config.RarityIndex[info.Rarity]].Color
		local row = make("Frame", { LayoutOrder = i, BackgroundColor3 = C.Dark, Parent = animalsList }, { corner(12), stroke(3, a.Placed and C.Green or C.Dark) })
		local thumb = make("Frame", { Size = UDim2.fromOffset(80, 80), Position = UDim2.fromOffset(6, 6), BackgroundColor3 = rc:Lerp(C.Dark, 0.4), Parent = row }, { corner(10) })
		viewport(a.Name, thumb, nil, nil, a.Mutation)
		local tags = {}
		if a.Mutation ~= "None" then
			local mc = (Config.Find(Config.Mutations, a.Mutation).Color :: Color3):ToHex()
			table.insert(tags, string.format('<font color="#%s">%s</font>', mc, a.Mutation:upper()))
		end
		if a.Size ~= "Normal" then
			table.insert(tags, a.Size:upper())
		end
		label({ Text = table.concat(tags, " "), Size = UDim2.new(0.4, 0, 0, 16), Position = UDim2.fromOffset(94, 6), TextXAlignment = Enum.TextXAlignment.Left, Parent = row })
		label({ Text = a.Name, Size = UDim2.new(0.45, 0, 0, 28), Position = UDim2.fromOffset(94, 22), TextXAlignment = Enum.TextXAlignment.Left, TextColor3 = rc, Parent = row })
		label({ Text = "$" .. Util.Format(a.Income) .. "/s", Size = UDim2.new(0.4, 0, 0, 22), Position = UDim2.fromOffset(94, 54), TextXAlignment = Enum.TextXAlignment.Left, TextColor3 = C.Green, Parent = row })
		button({ Size = UDim2.new(0.3, 0, 0, 36), Position = UDim2.new(0.68, 0, 0, 6), Text = a.Placed and "PICK UP" or "PLACE", Color = a.Placed and C.Blue or C.Green, Parent = row }, function()
			local ok, msg = Remotes.Request:InvokeServer("Place", a.Id)
			if msg then
				toast(msg, ok and "good" or "bad")
			end
		end)
		local confirm = false
		local sell
		sell = button({ Size = UDim2.new(0.3, 0, 0, 36), Position = UDim2.new(0.68, 0, 0, 48), Text = "SELL", Color = C.Red, Parent = row }, function()
			if not confirm then
				confirm = true
				sell.Text = "SURE?"
				task.delay(2, function()
					confirm = false
					if sell.Parent then
						sell.Text = "SELL"
					end
				end)
				return
			end
			local ok, msg = Remotes.Request:InvokeServer("Sell", a.Id)
			if msg then
				toast(msg, ok and "good" or "bad")
			end
			if ok then
				play("Buy")
			end
		end)
	end
	plotCount.Text = string.format("ON YOUR PLOT %d/%d   •   BACKPACK %d", placed, Data.Slots, #Data.Animals - placed)
end

-- ---------- INDEX ----------
local indexFrame, indexBody = panel("📖 Animal Index", C.Blue)
local indexTabs = make("Frame", { Size = UDim2.new(1, 0, 0, 46), BackgroundTransparency = 1, Parent = indexBody },
	{ make("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 6) }) })
local indexGrid = make("ScrollingFrame", { Size = UDim2.new(1, 0, 1, -110), Position = UDim2.new(0, 0, 0, 54), BackgroundTransparency = 1, ScrollBarThickness = 8,
	CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, Parent = indexBody },
	{ make("UIGridLayout", { CellSize = UDim2.fromOffset(120, 140), CellPadding = UDim2.fromOffset(10, 10) }) })
local indexFooter = label({ Text = "", Size = UDim2.new(1, 0, 0, 40), Position = UDim2.new(0, 0, 1, -44), TextColor3 = C.Gold, Parent = indexBody })
local indexZone = 1
local function refreshIndex()
	if not Data or not indexFrame.Visible then
		return
	end
	for _, ch in indexGrid:GetChildren() do
		if ch:IsA("Frame") then
			ch:Destroy()
		end
	end
	local zone = Config.Zones[indexZone]
	local found, total = 0, 0
	for _, z in Config.Zones do
		for _, a in z.Animals do
			total += 1
			if Data.Index[a[1]] then
				found += 1
			end
		end
	end
	for _, a in zone.Animals do
		local name, rarity = a[1], a[2]
		local has = Data.Index[name] == true
		local rc = Config.Rarities[Config.RarityIndex[rarity]].Color
		local cell = make("Frame", { BackgroundColor3 = C.White, Parent = indexGrid }, { corner(14), stroke(3), gradient(rc:Lerp(C.White, 0.3), rc:Lerp(C.Dark, 0.3), 90) })
		local vh = make("Frame", { Size = UDim2.new(1, -12, 0, 92), Position = UDim2.fromOffset(6, 6), BackgroundTransparency = 1, Parent = cell })
		viewport(name, vh, not has)
		label({ Text = has and name or "???", Size = UDim2.new(1, -8, 0, 22), Position = UDim2.new(0, 4, 0, 96), Parent = cell })
		label({ Text = rarity, Size = UDim2.new(1, -8, 0, 16), Position = UDim2.new(0, 4, 0, 118), TextColor3 = rc:Lerp(C.White, 0.5), Parent = cell })
	end
	indexFooter.Text = string.format("Unlocked %d/%d   •   Complete a zone for +%d%% income   •   Bonus now: x%.1f", found, total,
		Config.IndexZoneBonus * 100, Data.IndexBonus or 1)
end
for zi, z in Config.Zones do
	button({ Size = UDim2.new(1 / #Config.Zones, -6, 1, 0), Text = z.Icon .. " " .. z.Name, Color = z.Floor:Lerp(C.Dark, 0.15), Parent = indexTabs }, function()
		indexZone = zi
		refreshIndex()
	end)
end

sideButton("Index", "Icon Book", UDim2.new(0, 14, 0.5, -150), C.Blue, function()
	toggle(indexFrame, refreshIndex)
end)
sideButton("Shop", "Icon Egg Enchanted", UDim2.new(0, 14, 0.5, -40), C.Pink, function()
	toggle(robuxFrame, refreshRobuxShop) -- Robux shop; the Noob vendor's stall opens the toy shop
end)
sideButton("Animals", "Icon Paw", UDim2.new(1, -106, 0.5, -60), C.Orange, function()
	toggle(animalsFrame, refreshAnimals)
end)

Remotes.Data.OnClientEvent:Connect(function(d)
	Data = d
	refreshShop()
	refreshPasses()
	refreshAnimals()
	refreshIndex()
	updateStats()
end)

task.spawn(function()
	while true do
		task.wait(1)
		if Data then
			local left = (Data.LuckUntil or 0) - (Data.ServerTime or 0)
			Data.ServerTime = (Data.ServerTime or 0) + 1
			luckTimer.Text = left > 0 and ("ACTIVE " .. Util.Time(left)) or ""
			if shopFrame.Visible then
				Data.Cash = player:GetAttribute("Cash") or Data.Cash
				refreshShop()
			end
		end
	end
end)

-- ===================== TRAINING UI =====================
local trainUI = make("Frame", { Size = UDim2.fromOffset(420, 120), Position = UDim2.new(0.5, 0, 1, -30), AnchorPoint = Vector2.new(0.5, 1), BackgroundTransparency = 1, Visible = false, Parent = hud })
local trainLabel = label({ Text = "", Size = UDim2.new(1, 0, 0, 40), Parent = trainUI, TextColor3 = Color3.fromRGB(110, 210, 255) })
button({ Size = UDim2.fromOffset(180, 56), Position = UDim2.new(0.5, -90, 0, 52), Text = "STOP", Color = C.Red, Parent = trainUI }, function()
	Remotes.Train:FireServer(false)
end)
local function updateTrain()
	local on = player:GetAttribute("Training") == true
	trainUI.Visible = on
	-- the default Animate script keeps playing idle/fall tracks on top of the server's pull-up pose (the arm jitter); pause it
	local char = player.Character
	local animate = char and char:FindFirstChild("Animate")
	local animator = char and char:FindFirstChildWhichIsA("Animator", true)
	if animate and animate:IsA("LocalScript") then
		animate.Enabled = not on
	end
	if on and animator then
		for _, track in animator:GetPlayingAnimationTracks() do
			track:Stop(0)
		end
	end
	if on and Data then
		local bar = Config.Bars[Data.Bar]
		trainLabel.Text = string.format("💪 Bar Lv %d  •  +%s power / rep", Data.Bar, Util.Format(bar.PerRep))
	end
end
player:GetAttributeChangedSignal("Training"):Connect(updateTrain)
player:GetAttributeChangedSignal("Power"):Connect(function()
	if player:GetAttribute("Training") and Data then
		play("Rep", 0.9 + math.random() * 0.2, 0.5)
		local perRep = Config.Bars[Data.Bar].PerRep * (Data.Passes and Data.Passes.TrainPass and 2 or 1)
		local pop = label({ Text = "+" .. Util.Format(perRep) .. " 💪", Size = UDim2.fromOffset(160, 40),
			Position = UDim2.new(0.5, math.random(-120, 60), 0.55, 0), TextColor3 = Color3.fromRGB(110, 210, 255), Parent = overlay })
		TweenService:Create(pop, TweenInfo.new(0.8), { Position = pop.Position - UDim2.fromOffset(0, 90), TextTransparency = 1 }):Play()
		task.delay(0.8, pop.Destroy, pop)
	end
end)
UIS.JumpRequest:Connect(function()
	if player:GetAttribute("Training") then
		Remotes.Train:FireServer(false)
	end
end)

local function vfxFolder(): Folder
	local f = workspace:FindFirstChild("LocalVFX")
	if not f then
		f = make("Folder", { Name = "LocalVFX", Parent = workspace })
	end
	return f
end

local function cloneModel(name: string, scale: number): Model?
	local t = Models:FindFirstChild(name)
	if not t then
		return nil
	end
	local m = t:Clone()
	m:ScaleTo(scale)
	for _, p in m:GetDescendants() do
		if p:IsA("BasePart") then
			p.Anchored = true
			p.CanCollide = false
			p.CanQuery = false
		end
	end
	m.Parent = vfxFolder()
	return m
end

-- ===================== HELD TOY + THROW ARM =====================
local heldToy: Model? = nil
local heldName = ""
local function rightHand(): BasePart?
	local char = player.Character
	return char and (char:FindFirstChild("RightHand") or char:FindFirstChild("Right Arm")) :: BasePart?
end
local function setHeld(on: boolean)
	local want = on and Data and Data.Toy or nil
	if heldToy and (not want or heldName ~= want) then
		heldToy:Destroy()
		heldToy = nil
	end
	if want and not heldToy then
		heldToy = cloneModel(want, 0.55)
		heldName = want
	end
end
RunService.RenderStepped:Connect(function()
	local hand = heldToy and rightHand()
	if heldToy and hand then
		heldToy:PivotTo(hand.CFrame * CFrame.new(0, -hand.Size.Y / 2 - 0.35, 0))
	end
end)
local function swoosh()
	local hand = rightHand()
	if not hand then
		return
	end
	local a0 = make("Attachment", { Position = Vector3.new(0, hand.Size.Y / 2, 0), Parent = hand })
	local a1 = make("Attachment", { Position = Vector3.new(0, -hand.Size.Y / 2 - 0.5, 0), Parent = hand })
	make("Trail", { Attachment0 = a0, Attachment1 = a1, Lifetime = 0.22, LightEmission = 1, Color = ColorSequence.new(C.White),
		Transparency = NumberSequence.new(0.05, 1), Parent = hand })
	task.delay(0.7, function()
		a0:Destroy()
		a1:Destroy()
	end)
end

-- Plays the shared spline throw on your character and returns at the release frame (follow-through keeps going).
local function throwArm()
	local char = player.Character
	if not char then
		task.wait(0.4)
		return
	end
	local released = false
	ThrowAnim.Play(char, function()
		released = true
	end)
	task.delay(ThrowAnim.Release - 0.12, swoosh)
	while not released do
		RunService.Heartbeat:Wait()
	end
end

-- ===================== THROW METER =====================
local meter = make("Frame", { Size = UDim2.fromOffset(70, 300), Position = UDim2.new(0.5, 0, 0.5, 0), AnchorPoint = Vector2.new(0.5, 0.5), BackgroundColor3 = C.White, Visible = false, Parent = overlay }, {
	corner(35), stroke(5),
	make("UIGradient", { Rotation = 90, Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, Color3.fromRGB(80, 230, 90)), ColorSequenceKeypoint.new(0.35, Color3.fromRGB(190, 240, 70)),
		ColorSequenceKeypoint.new(0.65, Color3.fromRGB(255, 190, 50)), ColorSequenceKeypoint.new(1, Color3.fromRGB(240, 60, 60)) }) }),
})
for i = 1, 4 do
	make("Frame", { Size = UDim2.new(0.7, 0, 0, 3), Position = UDim2.new(0.15, 0, i / 5, 0), BackgroundColor3 = C.Dark, BackgroundTransparency = 0.6, BorderSizePixel = 0, Parent = meter })
end
make("Frame", { Size = UDim2.new(1, 8, 0.08, 0), Position = UDim2.new(0, -4, 0, 0), BackgroundColor3 = C.White, BackgroundTransparency = 0.5, Parent = meter }, { corner(20) })
local marker = make("Frame", { Size = UDim2.new(1.5, 0, 0, 18), AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 1), BackgroundColor3 = C.White, ZIndex = 3, Parent = meter }, { corner(9), stroke(4) })
local meterHint = label({ Text = "TAP TO THROW!", Size = UDim2.fromOffset(380, 56), Position = UDim2.new(0.5, 0, 1, 26), AnchorPoint = Vector2.new(0.5, 0), Parent = meter, StrokeSize = 4 })
local meterPct = label({ Text = "", Size = UDim2.fromOffset(100, 40), Position = UDim2.new(1, 16, 0, 0), AnchorPoint = Vector2.new(0, 0.5), Parent = marker })

local onPad = false
local throwCount = 0 -- results received; lets the failsafe tell a refused throw from a running one
local meterT = 0
local meterValue = 0

-- Like the original, the pad holds you in place (centered, facing the canyon) until you throw.
local savedMove: { number }? = nil
local function lockOnPad(on: boolean)
	local char = player.Character
	local hum = char and char:FindFirstChildOfClass("Humanoid")
	local hrp = char and char:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not (hum and hrp) then
		return
	end
	local lift = hum.RigType == Enum.HumanoidRigType.R6 and 3 or hum.HipHeight + hrp.Size.Y / 2
	local function standAt(offsetZ: number)
		local p = ThrowPad.Position + Vector3.new(0, ThrowPad.Size.Y / 2 + lift, offsetZ)
		hrp.CFrame = CFrame.lookAt(p, p + Vector3.new(0, 0, -1))
		hrp.AssemblyLinearVelocity = Vector3.zero
	end
	if on and not savedMove then
		savedMove = { hum.WalkSpeed, hum.JumpPower, hum.JumpHeight }
		hum.WalkSpeed, hum.JumpPower, hum.JumpHeight = 0, 0, 0
		standAt(0)
	elseif not on and savedMove then
		hum.WalkSpeed, hum.JumpPower, hum.JumpHeight = savedMove[1], savedMove[2], savedMove[3]
		savedMove = nil
		standAt(ThrowPad.Size.Z / 2 + 9) -- step back off the pad so it doesn't grab you again instantly
	end
end
player.CharacterAdded:Connect(function()
	savedMove = nil -- a new character starts unlocked
end)

RunService.RenderStepped:Connect(function(dt)
	local hrp = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	local near = hrp and (hrp.Position - ThrowPad.Position).Magnitude < 11 and not busy and not player:GetAttribute("Training")
	if near ~= onPad then
		onPad = near and true or false
		meter.Visible = onPad
		setHeld(onPad)
		if onPad then
			meterT = 0
			bounce(meter)
			lockOnPad(true)
		elseif not busy then
			camera.CameraType = Enum.CameraType.Custom
		end
	end
	if onPad then
		meterT += dt
		meterValue = (1 - math.cos(meterT * 3.4)) / 2
		marker.Position = UDim2.fromScale(0.5, 1 - meterValue)
		local rating, gain = Config.ThrowRating(meterValue, Data and Data.Power or 0)
		meterPct.Text = "+" .. Util.Format(gain)
		meterPct.TextColor3 = rating.Color
		meterHint.Rotation = math.sin(meterT * 6) * 3
		-- close over-the-shoulder camera looking down the canyon, like the original
		camera.CameraType = Enum.CameraType.Scriptable
		local want = CFrame.lookAt(hrp.Position + Vector3.new(2.4, 1.8, 6.5), hrp.Position + Vector3.new(0, 1.2, -14))
		camera.CFrame = camera.CFrame:Lerp(want, math.min(1, dt * 8))
	end
end)

-- ===================== THROW SEQUENCE =====================
local banner = make("Frame", { Size = UDim2.fromOffset(520, 140), Position = UDim2.new(0.5, 0, 0, 20), AnchorPoint = Vector2.new(0.5, 0), BackgroundTransparency = 1, Visible = false, Parent = overlay })
local luckLabel = label({ Text = "1.00X", Size = UDim2.new(1, 0, 0, 74), Parent = banner, TextColor3 = C.Gold, StrokeSize = 5 })
label({ Text = "LUCK", Size = UDim2.new(1, 0, 0, 26), Position = UDim2.fromOffset(0, 70), Parent = banner })
local zoneBanner = make("Frame", { Size = UDim2.new(1.3, 0, 0, 48), Position = UDim2.new(-0.15, 0, 0, 102), BackgroundColor3 = C.Dark, BackgroundTransparency = 0.35, Parent = banner }, { corner(10) })
local zoneLabel = label({ Text = "", Size = UDim2.fromScale(1, 0.85), Position = UDim2.fromScale(0, 0.08), Parent = zoneBanner })
local revealLabel = label({ Text = "", Size = UDim2.new(0.8, 0, 0, 90), Position = UDim2.new(0.1, 0, 0.72, 0), Visible = false, Parent = overlay, StrokeSize = 6 })
local flash = make("Frame", { Size = UDim2.fromScale(1, 1), BackgroundColor3 = C.White, BackgroundTransparency = 1, ZIndex = 10, Parent = overlay })

local function screenFlash(color: Color3, strength: number)
	flash.BackgroundColor3 = color
	flash.BackgroundTransparency = 1 - strength
	TweenService:Create(flash, TweenInfo.new(0.6), { BackgroundTransparency = 1 }):Play()
end

local shakeAmount = 0
local function shake(amount: number)
	shakeAmount = math.max(shakeAmount, amount)
end


local function burst(pos: Vector3, color: Color3, count: number, speed: number, texture: string?)
	local p = make("Part", { Anchored = true, CanCollide = false, CanQuery = false, Transparency = 1, Size = Vector3.one, Position = pos, Parent = vfxFolder() })
	local e = make("ParticleEmitter", {
		Texture = texture or "rbxasset://textures/particles/sparkles_main.dds", Color = ColorSequence.new(color), LightEmission = 0.8,
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.4), NumberSequenceKeypoint.new(1, 0) }),
		Lifetime = NumberRange.new(0.6, 1.3), Speed = NumberRange.new(speed * 0.5, speed), SpreadAngle = Vector2.new(180, 180),
		Acceleration = Vector3.new(0, -25, 0), Drag = 2, Rate = 0, RotSpeed = NumberRange.new(-200, 200), Parent = p,
	})
	e:Emit(count)
	task.delay(2, p.Destroy, p)
end

local function confetti(pos: Vector3, count: number)
	local cols = { C.Pink, C.Gold, C.Green, C.Blue, C.Purple, C.Orange }
	for _, col in cols do
		burst(pos + Vector3.new(0, 3, 0), col, count // #cols, 45, "rbxasset://textures/particles/explosion01_core_main.dds")
	end
end

local function shockwave(pos: Vector3, color: Color3)
	local ring = make("Part", { Anchored = true, CanCollide = false, CanQuery = false, Material = Enum.Material.Neon, Color = color, Shape = Enum.PartType.Cylinder,
		Size = Vector3.new(0.4, 2, 2), CFrame = CFrame.new(pos + Vector3.new(0, 0.3, 0)) * CFrame.Angles(0, 0, math.rad(90)), Parent = vfxFolder() })
	TweenService:Create(ring, TweenInfo.new(0.7, Enum.EasingStyle.Quint), { Size = Vector3.new(0.2, 34, 34), Transparency = 1 }):Play()
	task.delay(0.8, ring.Destroy, ring)
end

local function lightPillar(pos: Vector3, color: Color3)
	local beam = make("Part", { Anchored = true, CanCollide = false, CanQuery = false, Material = Enum.Material.Neon, Color = color, Transparency = 0.3,
		Size = Vector3.new(6, 400, 6), CFrame = CFrame.new(pos + Vector3.new(0, 200, 0)), Parent = vfxFolder() })
	make("PointLight", { Color = color, Range = 40, Brightness = 6, Parent = beam })
	TweenService:Create(beam, TweenInfo.new(2.5), { Size = Vector3.new(0.5, 400, 0.5), Transparency = 1 }):Play()
	task.delay(2.6, beam.Destroy, beam)
end

-- lighting per zone during the throw
local atmosphere = Lighting:FindFirstChildOfClass("Atmosphere")
local cc = Lighting:FindFirstChildOfClass("ColorCorrectionEffect")
local baseLighting = { Ambient = Lighting.Ambient, Tint = cc and cc.TintColor or C.White, Atmo = atmosphere and atmosphere.Color or C.White }
local function zoneLighting(zone: number?)
	local info = TweenInfo.new(0.8)
	local sky = zone and Config.Zones[zone].Sky
	if cc then
		TweenService:Create(cc, info, { TintColor = sky and C.White:Lerp(sky, 0.25) or baseLighting.Tint }):Play()
	end
	if atmosphere then
		TweenService:Create(atmosphere, info, { Color = sky or baseLighting.Atmo }):Play()
	end
end


local function letterReveal(name: string, color: Color3)
	revealLabel.Visible = true
	revealLabel.TextColor3 = C.White
	local shown = {}
	for i = 1, #name do
		shown[i] = name:sub(i, i) == " " and " " or "_"
	end
	revealLabel.Text = table.concat(shown, " ")
	local order = {}
	for i = 1, #name do
		if name:sub(i, i) ~= " " then
			table.insert(order, i)
		end
	end
	-- reveal in a shuffled order for suspense
	for i = #order, 2, -1 do
		local j = math.random(1, i)
		order[i], order[j] = order[j], order[i]
	end
	local step = math.clamp(1.6 / #order, 0.06, 0.18)
	for k, i in order do
		shown[i] = name:sub(i, i):upper()
		revealLabel.Text = table.concat(shown, " ")
		play("Tick", 1 + k * 0.05, 0.6)
		bounce(revealLabel)
		task.wait(step)
	end
	revealLabel.TextColor3 = color
	bounce(revealLabel)
end

local function resultCard(r)
	local rc = Config.Rarities[Config.RarityIndex[r.Rarity]].Color
	local a = r.Animal
	local card = make("Frame", { Size = UDim2.fromOffset(420, 170), Position = UDim2.new(0.5, 0, 0.36, 0), AnchorPoint = Vector2.new(0.5, 0.5), BackgroundColor3 = C.White, Parent = overlay },
		{ corner(20), stroke(5), gradient(rc:Lerp(C.White, 0.3), rc:Lerp(C.Dark, 0.35), 90) })
	local vh = make("Frame", { Size = UDim2.fromOffset(150, 150), Position = UDim2.fromOffset(10, 10), BackgroundTransparency = 1, Parent = card })
	viewport(a.Name, vh, nil, nil, a.Mutation)
	label({ Text = r.Rarity:upper(), Size = UDim2.fromOffset(240, 30), Position = UDim2.fromOffset(170, 14), TextXAlignment = Enum.TextXAlignment.Left, Parent = card })
	local tags = {}
	if a.Mutation ~= "None" then
		table.insert(tags, a.Mutation)
	end
	if a.Size ~= "Normal" then
		table.insert(tags, a.Size)
	end
	label({ Text = (#tags > 0 and (table.concat(tags, " ") .. " ") or "") .. a.Name, Size = UDim2.fromOffset(240, 44), Position = UDim2.fromOffset(170, 46), TextXAlignment = Enum.TextXAlignment.Left, Parent = card, StrokeSize = 3 })
	label({ Text = "$" .. Util.Format(r.Income) .. "/s", Size = UDim2.fromOffset(240, 30), Position = UDim2.fromOffset(170, 94), TextXAlignment = Enum.TextXAlignment.Left, TextColor3 = C.Green, Parent = card })
	if r.New then
		local badge = label({ Text = "NEW!", Size = UDim2.fromOffset(110, 44), Position = UDim2.new(1, -60, 0, -18), Rotation = 12, TextColor3 = C.Gold, Parent = card, StrokeSize = 4 })
		task.spawn(function()
			while badge.Parent do
				TweenService:Create(badge, TweenInfo.new(0.4), { Rotation = -8 }):Play()
				task.wait(0.4)
				TweenService:Create(badge, TweenInfo.new(0.4), { Rotation = 12 }):Play()
				task.wait(0.4)
			end
		end)
	end
	label({ Text = "Zone: " .. Config.Zones[r.Zone].Name .. "  •  " .. string.format("%.1fx luck", r.Luck), Size = UDim2.fromOffset(240, 22),
		Position = UDim2.fromOffset(170, 130), TextXAlignment = Enum.TextXAlignment.Left, TextColor3 = C.White, Parent = card })
	local sc = make("UIScale", { Scale = 0, Parent = card })
	TweenService:Create(sc, TweenInfo.new(0.45, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	return card
end

local function popText(text: string, color: Color3, yScale: number)
	local t = label({ Text = text, Size = UDim2.fromOffset(500, 70), Position = UDim2.new(0.5, 0, yScale, 0), AnchorPoint = Vector2.new(0.5, 0.5), TextColor3 = color, Parent = overlay, StrokeSize = 5 })
	bounce(t)
	TweenService:Create(t, TweenInfo.new(1.4), { Position = t.Position - UDim2.fromOffset(0, 60) }):Play()
	task.delay(1.0, function()
		TweenService:Create(t, TweenInfo.new(0.4), { TextTransparency = 1 }):Play()
		task.wait(0.4)
		t:Destroy()
	end)
end

-- "1 in X": the screen dims, the odds count up fast with rising ticks, then slam in with a flash.
local function commas(n: number): string
	if n >= 1e7 then
		return Util.Format(n)
	end
	local s = tostring(math.floor(n))
	return (s:reverse():gsub("(%d%d%d)", "%1,"):reverse():gsub("^,", ""))
end
local function oneInReveal(odds: number, color: Color3, onFrame: () -> ())
	local dim = make("Frame", { Size = UDim2.fromScale(1, 1), BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 1, ZIndex = 20, Parent = overlay })
	TweenService:Create(dim, TweenInfo.new(0.25), { BackgroundTransparency = 0.45 }):Play()
	local top = label({ Text = "1 in", Size = UDim2.fromOffset(300, 60), Position = UDim2.fromScale(0.5, 0.36), AnchorPoint = Vector2.new(0.5, 0.5), ZIndex = 21, Parent = overlay, StrokeSize = 5 })
	local num = label({ Text = "1", Size = UDim2.fromOffset(700, 130), Position = UDim2.fromScale(0.5, 0.47), AnchorPoint = Vector2.new(0.5, 0.5), TextColor3 = color, ZIndex = 21, Parent = overlay, StrokeSize = 8 })
	local sc = make("UIScale", { Scale = 0.6, Parent = num })
	local grad = odds >= 10000 and make("UIGradient", { Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 80, 90)), ColorSequenceKeypoint.new(0.33, Color3.fromRGB(255, 230, 70)),
		ColorSequenceKeypoint.new(0.66, Color3.fromRGB(80, 230, 255)), ColorSequenceKeypoint.new(1, Color3.fromRGB(220, 90, 255)) }), Parent = num })
	bounce(top)
	local countT, t0, lastTick = 1.3, os.clock(), 0
	while os.clock() - t0 < Config.OneInSeconds do
		local k = math.min((os.clock() - t0) / countT, 1)
		local eased = 1 - (1 - k) ^ 3
		num.Text = commas(math.max(1, math.floor(odds ^ eased))) -- grows through the orders of magnitude
		sc.Scale = 0.6 + 0.35 * eased
		if k < 1 and os.clock() - lastTick > 0.07 then
			lastTick = os.clock()
			play("Tick", 0.8 + eased * 1.2, 0.6)
		end
		if k >= 1 and num:GetAttribute("Done") == nil then
			num:SetAttribute("Done", true)
			num.Text = commas(odds)
			sc.Scale = 1.45
			TweenService:Create(sc, TweenInfo.new(0.35, Enum.EasingStyle.Back), { Scale = 1 }):Play()
			screenFlash(color, 0.6)
			shake(odds >= 10000 and 2 or 1.2)
			play(odds >= 1000 and "Legendary" or "Rare")
		end
		if grad then
			grad.Rotation = (os.clock() * 120) % 360
		end
		onFrame()
		RunService.RenderStepped:Wait()
	end
	for _, g in { top, num } do
		TweenService:Create(g, TweenInfo.new(0.25), { TextTransparency = 1 }):Play()
		TweenService:Create(g.UIStroke, TweenInfo.new(0.25), { Transparency = 1 }):Play()
	end
	TweenService:Create(dim, TweenInfo.new(0.25), { BackgroundTransparency = 1 }):Play()
	task.delay(0.3, function()
		dim:Destroy()
		top:Destroy()
		num:Destroy()
	end)
end

local function runThrow(r)
	local char = player.Character
	local hrp = char and char:FindFirstChild("HumanoidRootPart") :: BasePart
	if not hrp then
		busy = false
		return
	end
	hud.Visible = false
	if openPanel then
		openPanel.Visible = false
		openPanel = nil
	end
	local rating = Config.Find(Config.Ratings, r.Rating) or Config.Ratings[#Config.Ratings]
	play("Perfect", r.Perfect and 1 or 0.8, r.Perfect and nil or 0.4)
	popText(rating.Name, rating.Color, 0.2) -- high on screen so the throw itself stays visible
	task.delay(0.25, popText, "+" .. Util.Format(r.PowerGain) .. " POWER", Color3.fromRGB(110, 210, 255), 0.28)
	-- cinematic side dolly across the whole throw so it reads clearly, like a replay cam
	camera.CameraType = Enum.CameraType.Scriptable
	local holdPos = hrp.Position + Vector3.new(8.5, 2.4, 1.5)
	local focus = hrp.Position + Vector3.new(0, 1.6, -2)
	TweenService:Create(camera, TweenInfo.new(ThrowAnim.Release, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), {
		CFrame = CFrame.lookAt(holdPos, focus),
	}):Play()
	throwArm()
	play("Throw")
	local start = heldToy and heldToy:GetPivot().Position or (hrp.Position + Vector3.new(0, 2.5, -2))
	setHeld(false)
	local landing: Vector3 = r.Landing
	local toyInfo = Config.ToyInfo[r.Toy]
	local toyColor = Config.Rarities[Config.RarityIndex[toyInfo.Rarity]].Color
	local toy = cloneModel(r.Toy, 1.6)
	local root = toy and toy.PrimaryPart
	if root then
		local a0 = make("Attachment", { Position = Vector3.new(0, 0.7, 0), Parent = root })
		local a1 = make("Attachment", { Position = Vector3.new(0, -0.7, 0), Parent = root })
		make("Trail", { Attachment0 = a0, Attachment1 = a1, Lifetime = 0.45, LightEmission = 1, FaceCamera = true,
			Color = ColorSequence.new(C.White, toyColor), Transparency = NumberSequence.new(0, 1), Parent = root })
		make("ParticleEmitter", { Texture = "rbxasset://textures/particles/sparkles_main.dds", Rate = 40, Lifetime = NumberRange.new(0.4, 0.8),
			Speed = NumberRange.new(1, 3), Color = ColorSequence.new(toyColor), LightEmission = 1, Size = NumberSequence.new(0.8, 0), Parent = root })
	end
	camera.CameraType = Enum.CameraType.Scriptable
	TweenService:Create(camera, TweenInfo.new(0.5), { FieldOfView = 80 }):Play()
	banner.Visible = true
	shake(0.4)

	local dist = r.Distance
	local dur = Config.FlightTime(dist)
	local height = 22 + dist * 0.12
	local zoneShown = 0
	local t0 = os.clock()
	local camPos = camera.CFrame.Position
	local lastWhole = 1
	while true do
		local a = math.clamp((os.clock() - t0) / dur, 0, 1)
		local e = 1 - (1 - a) ^ 1.6 -- fast launch, gentle landing
		local pos = start:Lerp(landing, e) + Vector3.new(0, height * 4 * e * (1 - e), 0)
		if toy then
			toy:PivotTo(CFrame.new(pos) * CFrame.Angles(a * 25, a * 14, 0))
		end
		local travelled = math.max(0, (Config.Map.CorridorStartZ - pos.Z))
		local luck = Config.LuckAt(travelled) * toyInfo.Luck * (r.Boosted and Config.LuckBoost or 1)
		luckLabel.Text = string.format("%.2fX", luck)
		luckLabel.TextColor3 = C.Gold:Lerp(C.Pink, math.clamp(travelled / (Config.Map.ZoneLength * #Config.Zones), 0, 1))
		if math.floor(luck) > lastWhole then
			lastWhole = math.floor(luck)
			bounce(luckLabel)
		end
		local zone = Config.ZoneAt(travelled)
		if travelled > 1 and zone ~= zoneShown then
			zoneShown = zone
			local z = Config.Zones[zone]
			zoneLabel.Text = z.Name .. " " .. z.Icon
			zoneLabel.TextColor3 = z.Top:Lerp(C.White, 0.3)
			bounce(zoneBanner)
			play("Zone", 0.9 + zone * 0.05)
			zoneLighting(zone)
		end
		local held = os.clock() - t0
		if held < 0.55 then
			-- watch the toy leave the hand from the side cam (follow-through still playing), then chase it
			camPos = holdPos
			camera.CFrame = CFrame.lookAt(holdPos, focus:Lerp(pos, (held / 0.55) ^ 2))
		else
			local want = pos + Vector3.new(0, 10 + height * 0.15, 24)
			camPos = camPos:Lerp(want, 0.12)
			camera.CFrame = CFrame.lookAt(camPos, pos)
		end
		if a >= 1 then
			break
		end
		RunService.RenderStepped:Wait()
	end

	-- impact (the original dims the screen as the camera cuts to ground level)
	local rc = Config.Rarities[Config.RarityIndex[r.Rarity]].Color
	screenFlash(Color3.new(0, 0, 0), 0.55)
	play("Land")
	shake(1)
	shockwave(landing, toyColor)
	burst(landing, Color3.fromRGB(240, 230, 210), 30, 25)
	TweenService:Create(camera, TweenInfo.new(0.6), { FieldOfView = 65 }):Play()

	-- the animal runs in from further down the corridor
	local a = r.Animal
	local size = Config.Find(Config.Sizes, a.Size) or Config.Sizes[1]
	local animal = cloneModel(a.Name, size.Scale)
	local shimmer = {}
	if animal then
		Mutations.Apply(animal, a.Mutation)
		shimmer = Mutations.RainbowParts(animal)
	end
	local rig = animal and buildRig(animal)
	local from = landing + Vector3.new(0, 0, -34)
	local to = landing + Vector3.new(0, 0, -4.5)
	local walkT = 1.5
	local tw = os.clock()
	local camGoal = landing + Vector3.new(14, 7, 10)
	play("Footsteps")
	while os.clock() - tw < walkT do
		local k = (os.clock() - tw) / walkT
		local p = from:Lerp(to, 1 - (1 - k) ^ 2)
		if rig then
			-- models face -Z; turn to face +Z (toward the toy and camera)
			pose(rig, CFrame.new(p + Vector3.new(0, math.abs(math.sin(k * 22)) * 0.25, 0)) * CFrame.Angles(0, math.pi, 0), os.clock(), true)
		end
		camPos = camPos:Lerp(camGoal, 0.08)
		camera.CFrame = CFrame.lookAt(camPos, p:Lerp(landing, 0.5) + Vector3.new(0, 2, 0))
		RunService.RenderStepped:Wait()
	end
	local restCF = CFrame.new(to) * CFrame.Angles(0, math.pi, 0)
	if rig then
		pose(rig, restCF, os.clock(), false)
	end
	if toy then
		toy:Destroy()
	end
	burst(to, C.Gold, 18, 18)
	play("Munch")
	if r.OneIn then
		oneInReveal(r.Odds, rc, function()
			if rig then
				pose(rig, restCF * CFrame.new(0, math.abs(math.sin(os.clock() * 7)) * 0.5, 0), os.clock(), false)
			end
			Mutations.Shimmer(shimmer, os.clock())
		end)
	end

	letterReveal(a.Name, rc)
	local ri = Config.RarityIndex[r.Rarity]
	if ri >= 5 then
		play("Legendary")
		screenFlash(rc, 0.8)
		lightPillar(to, rc)
		confetti(to, 120)
		shake(1.5)
	elseif ri >= 3 then
		play("Rare")
		screenFlash(rc, 0.45)
		confetti(to, 60)
	else
		play("Catch")
		burst(to, rc, 30, 30)
	end
	if a.Mutation ~= "None" then
		local mc = Config.Find(Config.Mutations, a.Mutation).Color
		task.delay(0.3, popText, a.Mutation:upper() .. "!", mc, 0.62)
		burst(to, mc, 50, 35)
	end
	local card = resultCard(r)
	play("Cash", 1.1, 0.5)
	-- slow orbit around the animal while the card is up
	local orbitStart = os.clock()
	local orbitTime = Config.RevealSeconds - walkT - 1.9
	while os.clock() - orbitStart < orbitTime do
		local k = (os.clock() - orbitStart) * 0.35
		if rig then -- happy hop + idle while the camera orbits
			pose(rig, restCF * CFrame.new(0, math.abs(math.sin(os.clock() * 7)) * 0.5, 0), os.clock(), false)
		end
		Mutations.Shimmer(shimmer, os.clock())
		local center = to + Vector3.new(0, 2.2 * size.Scale, 0)
		local want = center + Vector3.new(math.sin(k + 0.9) * 13, 4 + size.Scale * 2, math.cos(k + 0.9) * 13)
		camPos = camPos:Lerp(want, 0.08)
		camera.CFrame = CFrame.lookAt(camPos, center)
		RunService.RenderStepped:Wait()
	end
	-- wrap up
	local sc = card:FindFirstChildOfClass("UIScale")
	if sc then
		TweenService:Create(sc, TweenInfo.new(0.25), { Scale = 0 }):Play()
	end
	task.delay(0.3, card.Destroy, card)
	revealLabel.Visible = false
	banner.Visible = false
	if animal then
		animal:Destroy()
	end
	zoneLighting(nil)
	camera.CameraType = Enum.CameraType.Custom
	camera.FieldOfView = 70
	hud.Visible = true
	lockOnPad(false)
	task.wait(Config.ThrowCooldown)
	busy = false
end

UIS.InputBegan:Connect(function(input, processed)
	if processed or not onPad or busy then
		return
	end
	local t = input.UserInputType
	if t == Enum.UserInputType.MouseButton1 or t == Enum.UserInputType.Touch or input.KeyCode == Enum.KeyCode.Space or input.KeyCode == Enum.KeyCode.ButtonA then
		busy = true
		meter.Visible = false
		onPad = false
		local sent = throwCount
		Remotes.Throw:FireServer(meterValue)
		-- failsafe if the server refused the throw: no result arrived, so hand the camera back
		task.delay(3, function()
			if busy and throwCount == sent then
				busy = false
				camera.CameraType = Enum.CameraType.Custom
				lockOnPad(false)
			end
		end)
	end
end)

Remotes.ThrowFX.OnClientEvent:Connect(function(thrower: Player)
	if thrower ~= player and thrower.Character then
		ThrowAnim.Play(thrower.Character)
	end
end)

Remotes.ThrowResult.OnClientEvent:Connect(function(r)
	throwCount += 1
	busy = true
	runThrow(r)
end)

-- camera shake
RunService:BindToRenderStep("TATShake", Enum.RenderPriority.Camera.Value + 1, function(dt)
	if shakeAmount > 0.01 then
		local s = shakeAmount
		camera.CFrame = camera.CFrame * CFrame.new((math.random() - 0.5) * s, (math.random() - 0.5) * s, 0)
		shakeAmount = math.max(0, shakeAmount - dt * 3)
	end
end)

-- ===================== THROW PAD + PLOT PET IDLE =====================
do
	local bb = make("BillboardGui", { Size = UDim2.fromOffset(240, 60), StudsOffset = Vector3.new(0, 6, 0), LightInfluence = 0, AlwaysOnTop = true, Parent = ThrowPad })
	local t = label({ Text = "🎯 THROW HERE", Size = UDim2.fromScale(1, 1), TextColor3 = C.Gold, Parent = bb, StrokeSize = 3 })
	task.spawn(function()
		while true do
			TweenService:Create(bb, TweenInfo.new(0.8, Enum.EasingStyle.Sine), { StudsOffset = Vector3.new(0, 7, 0) }):Play()
			task.wait(0.8)
			TweenService:Create(bb, TweenInfo.new(0.8, Enum.EasingStyle.Sine), { StudsOffset = Vector3.new(0, 6, 0) }):Play()
			task.wait(0.8)
		end
	end)
	t.Visible = true
end

local pets: { [Model]: { Base: CFrame, Rig: Rig?, Shimmer: { BasePart }, NextHop: number } } = {}
local function addPet(m: Instance)
	if not m:IsA("Model") then
		return
	end
	local entry = { Base = m:GetPivot(), Rig = buildRig(m), Shimmer = Mutations.RainbowParts(m), NextHop = os.clock() + math.random() * 8 }
	pets[m] = entry
end
CollectionService:GetInstanceAddedSignal("PlotPet"):Connect(addPet)
CollectionService:GetInstanceRemovedSignal("PlotPet"):Connect(function(m)
	pets[m :: Model] = nil
end)
for _, m in CollectionService:GetTagged("PlotPet") do
	addPet(m)
end
local acc = 0
RunService.Heartbeat:Connect(function(dt)
	acc += dt
	if acc < 1 / 30 then
		return
	end
	acc = 0
	local now = os.clock()
	local camP = camera.CFrame.Position
	for m, e in pets do
		if not m.Parent then
			pets[m] = nil
			continue
		end
		if not e.Rig or (e.Base.Position - camP).Magnitude > 140 then
			continue
		end
		-- occasional happy hop, otherwise a gentle breathing bob
		local hopT = now - e.NextHop
		local y = math.sin(now * 2.4 + e.Rig.Phase) * 0.04
		if hopT > 0 then
			y = math.sin(math.min(hopT / 0.45, 1) * math.pi) * 0.9
			if hopT > 0.45 then
				e.NextHop = now + 4 + math.random() * 8
			end
		end
		pose(e.Rig, e.Base * CFrame.new(0, y, 0), now, false)
		Mutations.Shimmer(e.Shimmer, now + e.Rig.Phase)
	end
end)

-- ===================== SHOP VENDOR =====================
task.spawn(function()
	local vendor = Map:WaitForChild("ShopVendor", 15)
	local arm = vendor and vendor:FindFirstChild("Right Arm") :: BasePart?
	if arm then
		local shoulder = arm.CFrame * CFrame.new(0, 1, 0)
		RunService.Heartbeat:Connect(function()
			local a = math.rad(150) + math.sin(os.clock() * 6) * 0.35
			arm.CFrame = shoulder * CFrame.Angles(0, 0, a) * CFrame.new(0, -1, 0)
		end)
	end
end)
game:GetService("ProximityPromptService").PromptTriggered:Connect(function(prompt)
	if prompt.Name == "ShopPrompt" and not shopFrame.Visible then
		toggle(shopFrame, refreshShop)
	end
end)

updateStats()
