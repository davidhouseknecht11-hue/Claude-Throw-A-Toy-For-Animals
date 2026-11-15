-- Full-body overhand throw for R15 (R6 falls back to the shoulder only), authored as keyframes and played with
-- Catmull-Rom splines every frame so it moves like a hand-keyed animation without needing an uploaded asset.
-- Joints are posed through Motor6D.C0, or Attachment0.CFrame on upgraded (AnimationConstraint) avatars; both rotate
-- the child about the joint the same way. Values per joint: {pitch, yaw, roll, x, y, z} (degrees / studs, from rest).
-- +pitch swings a hanging limb forward and tips the torso back; +yaw turns the body to its left; +roll raises the right
-- arm out to the side (and, on an elbow, folds the forearm up); Root x/y/z move the hips (right / up / back).
-- The cocked arm is roll-driven (elbow out at shoulder height, forearm up) because pitching an R15 arm back folds it
-- in front of the face; verified on a Studio dummy.
local RunService = game:GetService("RunService")

local ThrowAnim = {}
ThrowAnim.Release = 0.62 -- seconds in: the toy leaves the hand
ThrowAnim.Length = 1.5

local KEYS = {
	{ t = 0.0, pose = {} },
	{ -- anticipation: small dip, weight rocks back, arm starts to lift, eyes lock on target
		t = 0.18, pose = {
			Root = { 0, -12, 0, 0, -0.15, 0.12 }, Waist = { 4, -10, 0 }, Neck = { 0, 18, 0 },
			RightShoulder = { 0, -8, 45 }, RightElbow = { 0, 0, 35 },
			LeftShoulder = { 25, 0, 0 }, LeftElbow = { 20, 0, 0 },
			RightHip = { 4, 0, 0 }, RightKnee = { -14, 0, 0 }, LeftHip = { 8, 0, 0 }, LeftKnee = { -12, 0, 0 },
		} },
	{ -- full coil: body loaded on the back leg, throwing arm cocked high behind the head, glove arm aims, front knee lifts
		t = 0.42, pose = {
			Root = { 0, -28, 0, 0, -0.28, 0.3 }, Waist = { 12, -28, 0 }, Neck = { -4, 50, 0 },
			RightShoulder = { 0, -28, 96 }, RightElbow = { 0, 0, 100 }, RightWrist = { -30, 0, 0 },
			LeftShoulder = { 88, -12, 0 }, LeftElbow = { 10, 0, 0 },
			RightHip = { -4, 0, 0 }, RightKnee = { -28, 0, 0 }, RightAnkle = { 10, 0, 0 },
			LeftHip = { 48, 0, 0 }, LeftKnee = { -58, 0, 0 }, LeftAnkle = { -15, 0, 0 },
		} },
	{ -- stride plant: front foot lands, hips start to open, arm still cocked (the "lag" that sells power)
		t = 0.53, pose = {
			Root = { 0, -10, 0, 0, -0.36, 0.05 }, Waist = { 8, -32, 0 }, Neck = { -2, 40, 0 },
			RightShoulder = { -10, -40, 100 }, RightElbow = { 0, 0, 115 }, RightWrist = { -40, 0, 0 },
			LeftShoulder = { 70, -8, 0 }, LeftElbow = { 25, 0, 0 },
			RightHip = { -18, 0, 0 }, RightKnee = { -35, 0, 0 }, RightAnkle = { 20, 0, 0 },
			LeftHip = { 34, 0, 0 }, LeftKnee = { -18, 0, 0 }, LeftAnkle = { -6, 0, 0 },
		} },
	{ -- release: hips and chest whip through, arm fires forward, wrist snaps, glove arm tucks, back leg drives
		t = 0.62, pose = {
			Root = { -6, 22, 0, 0, -0.34, -0.32 }, Waist = { -22, 34, 0 }, Neck = { 8, -30, 0 },
			RightShoulder = { 100, 0, 10 }, RightElbow = { 12, 0, 0 }, RightWrist = { 35, 0, 0 },
			LeftShoulder = { 18, 0, 0 }, LeftElbow = { 75, 0, 0 },
			RightHip = { -38, 0, 0 }, RightKnee = { -48, 0, 0 }, RightAnkle = { 35, 0, 0 },
			LeftHip = { 36, 0, 0 }, LeftKnee = { -24, 0, 0 }, LeftAnkle = { -4, 0, 0 },
		} },
	{ -- follow-through: chest over the front knee, arm finishes low across the body, back heel kicks up
		t = 0.8, pose = {
			Root = { -10, 32, 0, 0, -0.42, -0.45 }, Waist = { -30, 44, 0 }, Neck = { 12, -36, 0 },
			RightShoulder = { 52, 30, -34 }, RightElbow = { 42, 0, 0 }, RightWrist = { 20, 0, 0 },
			LeftShoulder = { -18, 0, 0 }, LeftElbow = { 85, 0, 0 },
			RightHip = { -46, 0, 0 }, RightKnee = { -78, 0, 0 }, RightAnkle = { 30, 0, 0 },
			LeftHip = { 40, 0, 0 }, LeftKnee = { -32, 0, 0 },
		} },
	{ -- recovery step: back leg swings through, body rises and squares up
		t = 1.08, pose = {
			Root = { -4, 12, 0, 0, -0.14, -0.2 }, Waist = { -8, 14, 0 }, Neck = { 4, -10, 0 },
			RightShoulder = { 20, 10, -10 }, RightElbow = { 30, 0, 0 },
			LeftShoulder = { 5, 0, 0 }, LeftElbow = { 35, 0, 0 },
			RightHip = { 14, 0, 0 }, RightKnee = { -22, 0, 0 }, LeftHip = { 10, 0, 0 }, LeftKnee = { -10, 0, 0 },
		} },
	{ t = 1.5, pose = {} }, -- settle to rest
}

local JOINTS = { "Root", "Waist", "Neck", "RightShoulder", "RightElbow", "RightWrist", "LeftShoulder", "LeftElbow",
	"RightHip", "RightKnee", "RightAnkle", "LeftHip", "LeftKnee", "LeftAnkle" }

local function value(key, joint: string, i: number): number
	local p = key.pose[joint]
	return p and p[i] or 0
end

-- Catmull-Rom through the keyframes; returns {pitch, yaw, roll, x, y, z} for a joint at time t
local function sample(joint: string, t: number): { number }
	t = math.clamp(t, 0, ThrowAnim.Length)
	local i = 1
	while i < #KEYS - 1 and KEYS[i + 1].t <= t do
		i += 1
	end
	local k0, k1, k2, k3 = KEYS[math.max(i - 1, 1)], KEYS[i], KEYS[i + 1], KEYS[math.min(i + 2, #KEYS)]
	local u = (t - k1.t) / (k2.t - k1.t)
	local u2, u3 = u * u, u * u * u
	local out = table.create(6, 0)
	for c = 1, 6 do
		local p0, p1, p2, p3 = value(k0, joint, c), value(k1, joint, c), value(k2, joint, c), value(k3, joint, c)
		out[c] = 0.5 * (2 * p1 + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u3)
	end
	return out
end

type Rig = { [string]: { T: Instance, Prop: string, Base: CFrame } }

local function findJoint(char: Model, name: string): (Instance?, string?)
	local j = char:FindFirstChild(name, true)
	if j and j:IsA("Motor6D") then
		return j, "C0"
	elseif j and j:IsA("AnimationConstraint") and j.Attachment0 then
		return j.Attachment0, "CFrame"
	end
	return nil, nil
end

function ThrowAnim.Rig(char: Model): (Rig, boolean)
	local r15 = char:FindFirstChild("UpperTorso") ~= nil
	local rig = {}
	for _, name in JOINTS do
		local target, prop = findJoint(char, r15 and name or (name == "RightShoulder" and "Right Shoulder" or "\0"))
		if target then
			rig[name] = { T = target, Prop = prop, Base = (target :: any)[prop] }
		end
	end
	return rig, r15
end

-- Pose every rigged joint at time t (also used by the Studio preview to inspect single frames).
function ThrowAnim.Pose(rig: Rig, r15: boolean, t: number)
	for name, j in rig do
		local v = sample(name, t)
		local rot = r15 and CFrame.Angles(math.rad(v[1]), math.rad(v[2]), math.rad(v[3])) or CFrame.Angles(0, 0, math.rad(v[1]))
		local target: any = j.T -- (no line may start with "(" here: Luau would read it as a call)
		target[j.Prop] = j.Base * CFrame.new(v[4], v[5], v[6]) * rot
	end
end

function ThrowAnim.Restore(rig: Rig)
	for _, j in rig do
		local target: any = j.T
		if target.Parent then
			target[j.Prop] = j.Base
		end
	end
end

-- Play on a character; onRelease fires at the release frame. timeScale < 1 slows it (for previews).
function ThrowAnim.Play(char: Model, onRelease: (() -> ())?, timeScale: number?)
	local rig, r15 = ThrowAnim.Rig(char)
	local t, released = 0, false
	local conn
	conn = RunService.Heartbeat:Connect(function(dt)
		t += dt * (timeScale or 1)
		if not char.Parent or t >= ThrowAnim.Length then
			conn:Disconnect()
			ThrowAnim.Restore(rig)
			return
		end
		ThrowAnim.Pose(rig, r15, t)
		if not released and t >= ThrowAnim.Release then
			released = true
			if onRelease then
				task.spawn(onRelease)
			end
		end
	end)
end

-- self-check: the spline hits each authored key exactly and starts/ends at rest
assert(math.abs(sample("RightShoulder", 0.42)[3] - 96) < 1e-6 and sample("Waist", 0)[2] == 0 and sample("Waist", 1.5)[2] == 0,
	"ThrowAnim spline self-check failed")

return ThrowAnim
