-- Applies only to the onboard keyboard; external keyboards retain their layout.
hl.device({
  name = "clockworkpi-uconsole-keyboard",
  kb_file = os.getenv("HOME") .. "/.config/hypr/uconsole.xkb",
})
-- The speaker key is a separate HID consumer-control interface on this board.
hl.device({
  name = "clockworkpi-uconsole-consumer-control",
  -- Match the remapped Hyper_L symbol, not the original volume-down keycode.
  resolve_binds_by_sym = true,
  kb_file = os.getenv("HOME") .. "/.config/hypr/uconsole.xkb",
})

local function replace(key, description, action, options)
  hl.unbind(key)
  o.bind(key, description, action, options)
end

replace("SUPER + B", "uConsole: browser", { omarchy = "browser" })
replace("SUPER + E", "uConsole: files", { omarchy = "nautilus" })
replace("SUPER + A", "uConsole: apps", "omarchy-menu toggle apps")
replace("SUPER + H", "uConsole: keyboard guide", "uconsole-keyboard-help")
replace("SUPER + K", "uConsole: physical keyboard guide", "uconsole-keyboard-help")
replace("SUPER + SHIFT + K", "Omarchy: complete keybindings list", "uconsole-keybindings-all")
replace("PAUSE", "uConsole: keyboard guide (Fn + Start)", "uconsole-keyboard-help")
replace("SUPER + L", "uConsole: lock", "omarchy-system-lock")
replace("SUPER + SHIFT + L", "uConsole: change window layout", "omarchy-hyprland-workspace-layout-toggle")
replace("SUPER + Z", "uConsole: toggle magnifier", function()
  local zoom = hl.get_config("cursor.zoom_factor") or 1
  hl.config({ cursor = { zoom_factor = zoom > 1 and 1 or 2 } })
end)
replace("XF86MonBrightnessUp", "uConsole: brightness up one level", "uconsole-brightness up", { locked = true, repeating = true })
replace("XF86MonBrightnessDown", "uConsole: brightness down one level", "uconsole-brightness down", { locked = true, repeating = true })
replace("MOD3 + UP", "uConsole: Speaker + D-pad Up, volume up", "omarchy-audio-output-volume raise", { locked = true, repeating = true })
replace("MOD3 + DOWN", "uConsole: Speaker + D-pad Down, volume down", "omarchy-audio-output-volume lower", { locked = true, repeating = true })

-- Left Alt alternatives let the opposite thumb hold the modifier. Keep Alt+Tab
-- as app switching; Right Alt+Tab continues to change workspaces.
replace("ALT + SPACE", "uConsole: menu (left Alt)", "omarchy-menu toggle")
replace("ALT + T", "uConsole: Activity / btop", "uconsole-activity")
o.window("org.uconsole.activity", { fullscreen = true })
if o.cmd_present("voxtype") then
  replace("ALT + D", "uConsole: toggle dictation", "voxtype record toggle")
end
replace("ALT + RETURN", "uConsole: terminal (left Alt)", { omarchy = "terminal" })
replace("ALT + B", "uConsole: browser (left Alt)", { omarchy = "browser" })
replace("ALT + E", "uConsole: files (left Alt)", { omarchy = "nautilus" })
replace("ALT + A", "uConsole: apps (left Alt)", "omarchy-menu toggle apps")
replace("ALT + H", "uConsole: guide (left Alt)", "uconsole-keyboard-help")
replace("ALT + K", "uConsole: guide (left Alt)", "uconsole-keyboard-help")
replace("ALT + SHIFT + K", "uConsole: all bindings (left Alt)", "uconsole-keybindings-all")
replace("ALT + L", "uConsole: lock (left Alt)", "omarchy-system-lock")
replace("ALT + SHIFT + L", "uConsole: window layout (left Alt)", "omarchy-hyprland-workspace-layout-toggle")
replace("ALT + ESCAPE", "uConsole: system menu (left Alt)", "omarchy-menu toggle system")
replace("ALT + F", "uConsole: fullscreen (left Alt)", hl.dsp.window.fullscreen({ mode = "fullscreen" }))
replace("ALT + Q", "uConsole: close app (left Alt)", hl.dsp.window.close())
replace("ALT + LEFT", "uConsole: previous app column (left Alt)", hl.dsp.focus({ direction = "l" }))
replace("ALT + RIGHT", "uConsole: next app column (left Alt)", hl.dsp.focus({ direction = "r" }))
replace("ALT + Z", "uConsole: magnifier (left Alt)", function()
  local zoom = hl.get_config("cursor.zoom_factor") or 1
  hl.config({ cursor = { zoom_factor = zoom > 1 and 1 or 2 } })
end)
for n = 1, 5 do
  replace("ALT + code:" .. tostring(n + 9), "uConsole: workspace " .. n .. " (left Alt)", hl.dsp.focus({ workspace = tostring(n) }))
  replace("ALT + SHIFT + code:" .. tostring(n + 9), "uConsole: move to workspace " .. n .. " (left Alt)", hl.dsp.window.move({ workspace = tostring(n) }))
end
