# Packs the current build into TATUpdate.rbxmx so an existing (published) place can be updated in Studio:
# right-click Workspace > Insert from File > TATUpdate.rbxmx, then run the command-bar line printed below.
# It holds everything build_place.py generates except Terrain/Camera; the place's own extras (e.g. StarterGui) are untouched.
# Studio moves inserted models to the camera, so after swapping put the map back where the scripts expect it:
#   local m=workspace.Map m:PivotTo(m:GetPivot()+Vector3.new(0,0.15,-66.5)-m.ThrowLine.Position)
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import build_place as b  # builds the place as a side effect; we reuse its Items

pack = b.Item("Folder", "TATUpdate")
for svc, dest in ((b.workspace, "Workspace"), (b.rs, "ReplicatedStorage"), (b.sss, "ServerScriptService"),
                  (b.sps, "StarterPlayerScripts"), (b.lighting, "Lighting"), (b.matsvc, "MaterialService")):
    f = pack.add(b.Item("Folder", dest))
    f.children.extend(c for c in svc.children if c.cls not in ("Terrain", "Camera"))
# Lighting's own properties (Brightness, ClockTime, ...) can't ride in a Folder: the Studio command line sets them.

out = ['<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
       'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">']
pack.xml(out)
out.append("</roblox>")
path = b.P("TATUpdate.rbxmx")
open(path, "w", encoding="utf-8").write("\n".join(out))
print("wrote", path)
