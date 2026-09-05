# uConsole Clear

A readable, near-black Omarchy theme and keyboard toolkit for the ClockworkPi uConsole. Large text, solid contrast, a physical keyboard guide, and an accent editor that works without the trackball.

Verified on a CM5 uConsole running the ARM64 Omarchy 4 Pi RC1 build, Omarchy 4.0.2, Hyprland 0.56.1 and Quickshell 0.3.1. This uses Omarchy's **Lua / Quickshell generation**, not the older Hyprland `.conf` / Waybar setup. CM4 and other releases have not been hardware-tested here.

![Theme editor](screenshots/editor.png)

## Install

Already running the supported Omarchy desktop:

```bash
git clone https://github.com/cosmindolha/omarchy-uconsole-clear-theme.git
cd omarchy-uconsole-clear-theme
./install.sh --check
./install.sh
```

Run as the desktop user, including over SSH after the graphical session has started. Dependencies include Python 3.11+, librsvg (`rsvg-convert`), libxkbcommon tools, brightnessctl, and the standard Omarchy desktop commands. The user must belong to `video`.

The installer applies monitor rotation/scale, readable fonts, full-width scrolling columns, the text bar, keyboard bindings, and the editor. It saves the previous Hyprland/theme configuration under `~/.local/state/uconsole-before-clear` and keyboard configuration under `~/.local/state/uconsole-before-keyboard`. It installs one root udev rule for backlight access. It replaces the user shell/bar and monitor layout; review the scripts if you have existing customizations. A rerun retains an already-selected Clear accent.

For the **base yellow theme alone**, use Omarchy's Install → Style → Theme with this repository URL. That does not install the keyboard utilities or change display scaling. For the OS installation itself, see [the CM5 SSH installation guide](https://github.com/cosmindolha/omarchy-uconsole-cm5).

## Controls

- **Either Alt + Space:** Omarchy menu. Style → Theme colors opens the editor.
- **Left Alt + Enter:** terminal. **Left Alt + K:** physical keyboard guide.
- **Either Alt + Shift + K:** complete searchable shortcut list.
- **Left Alt + Tab:** next app. **Right Alt + Tab:** next workspace.
- **Hold speaker + D-pad Up / Down:** volume changes in 5% steps; holding repeats. **Fn + speaker:** mute.
- **Fn + comma / period:** one actual backlight level down/up. **Fn + Space:** keyboard lighting.
- **Either Alt + L:** manual lock. Automatic locking is delayed to one hour; display blanking follows the lock.

Right Alt becomes Super on the onboard keyboard. The speaker key becomes a held modifier on its separate consumer-control interface. The other keyboards retain their mappings. Left Alt alternatives can override an application's own Alt shortcuts. Stock game-button behavior is retained.

![Physical keyboard guide](screenshots/keyboard.png)

The guide lists commands on the left and highlights the physical keys on the right. Normal keys are square. It prefers a modifier on the opposite side of the action key where possible, including Ctrl. Search a command or click a key to filter; use Up/Down to browse.

## Accent editor

| Key | Action |
| --- | --- |
| 1–4 | Yellow, Green, Blue, White |
| C, then D-pad | Saturation left/right, brightness up/down |
| H, then D-pad | Hue |
| Shift + D-pad | Larger adjustment steps |
| X | Type a hex color; Enter previews it |
| Ctrl + S | Save, including while editing hex |
| S | Save outside the hex field |
| Esc / R | Revert; R applies outside the hex field |
| Tab / Shift + Tab | Move focus |

Preview changes the shell and active window border. Save invokes native Omarchy theme application for supported apps. Custom accents are raised to at least 4.5:1 contrast against the background. The local editor listens on **127.0.0.1:8768**; its API is not exposed to the LAN.

All four presets and the custom variant have dedicated `preview.png` files. Saving regenerates the custom preview and invalidates the native picker index. The wallpaper remains nearly black. Dark pixels do not materially reduce an IPS LCD's backlight power; lowering brightness does.

![Native theme previews](screenshots/theme-menu.png)

## Battery readings

The bar shows measured voltage. Clicking it opens voltage, current, computed battery power, and the PMIC's reported percentage. On the tested unit, the PMIC kept reporting 100% while discharging near 3.6 V; its charge counter exceeded the configured full capacity. The panel flags this as unreliable rather than presenting a full battery.

This is a reporting fix, **not a completed fuel-gauge calibration**. See [battery diagnosis and calibration](docs/BATTERY.md). Other applications may still display the kernel's uncalibrated percentage.

## Display and implementation

Designed for the 5-inch 1280×720 display at scale 1.25 (1024×576 logical). Shell text is 20 px, terminal text 15 pt, cursor size 30. Browser utilities compensate for the inherited GTK text scale so controls fit without shrinking their usable text.

User-owned files live in `~/.config/hypr`, `~/.config/omarchy`, `~/.local/bin` and `~/.local/share/uconsole`. Vendor Omarchy files are not overwritten. The full keybindings helper is generated from the installed upstream script with a compatibility correction for this release's Lua scanner.

Validation: real desktop screenshots, user-confirmed physical shortcuts/readability, input events through the real consumer and keyboard devices (volume 0→5→0%), editor keyboard flows, and a normal reboot preserving theme, rotation and idle settings. The public toolkit installer was also run on the real device, retaining the saved custom purple accent and one-hour idle delay with no Hyprland configuration errors or failed user services. Run `python3 -m unittest discover -s tests` for the palette checks. This project is an experimental community adaptation, not an official Omarchy or ClockworkPi release.

MIT licensed. See [NOTICE](NOTICE) for upstream attribution. [Omarchy theme docs](https://omarchy.org/manual/making-your-own-theme/) · [ClockworkPi keyboard firmware](https://github.com/clockworkpi/uConsole/blob/master/Code/uconsole_keyboard/keymaps.ino).
