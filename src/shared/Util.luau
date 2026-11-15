-- Shared helpers: number formatting and weighted rolls.
local Util = {}

local SUFFIX = { "", "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No", "Dc" }

function Util.Format(n: number): string
	if n ~= n then
		return "0"
	end
	local neg = n < 0
	n = math.abs(n)
	local i = 1
	while n >= 1000 and i < #SUFFIX do
		n /= 1000
		i += 1
	end
	local s
	if i == 1 then
		s = tostring(math.floor(n))
	elseif n >= 100 then
		s = string.format("%d", math.floor(n)) .. SUFFIX[i]
	elseif n >= 10 then
		s = string.format("%.1f", math.floor(n * 10) / 10) .. SUFFIX[i]
	else
		s = string.format("%.2f", math.floor(n * 100) / 100) .. SUFFIX[i]
	end
	-- trim trailing decimal zeros only ("1.50K" -> "1.5K", "2.00M" -> "2M", "100K" untouched)
	s = s:gsub("(%.%d-)0+([A-Za-z]+)$", "%1%2")
	s = s:gsub("%.([A-Za-z]+)$", "%1")
	return (neg and "-" or "") .. s
end

-- items: array; weightOf(item) -> number. rng: Random.
-- Weighted pick; also returns the chance (0..1) of what was picked, for the "1 in X" reveal.
function Util.Pick<T>(items: { T }, weightOf: (T) -> number, rng: Random): (T, number)
	local total = 0
	for _, it in items do
		total += weightOf(it)
	end
	local r = rng:NextNumber() * total
	for _, it in items do
		local w = weightOf(it)
		r -= w
		if r <= 0 then
			return it, w / total
		end
	end
	return items[#items], weightOf(items[#items]) / total
end

function Util.Time(seconds: number): string
	seconds = math.max(0, math.floor(seconds))
	return string.format("%d:%02d", seconds // 60, seconds % 60)
end

return Util
