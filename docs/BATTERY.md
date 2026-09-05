# Battery readings and the stuck-full gauge

The panel reports measured voltage/current separately from the PMIC's state-of-charge estimate. On the tested CM5, the kernel reported **100% while discharging at about 3.6 V**. This was present in the PMIC register itself, so refreshing the UI could not fix it.

## What was measured

| Reading | Observation |
| --- | --- |
| Battery sysfs | `/sys/class/power_supply/axp20x-battery` |
| External power | `/sys/class/power_supply/axp22x-ac/online` |
| Discharging | About 3.58–3.61 V, −1.33 to −1.63 A |
| Gauge percentage | 100% despite the above |
| Configured design capacity | 6700 mAh total; installed cell labels still need confirmation |
| PMIC charge counter | About 7280 mAh, exceeding its roughly 6700 mAh full-capacity setting |
| Voltage-based PMIC estimate | About 31% during the read-only inspection; not substituted as an accurate percentage |
| Charger connected | External power online, Charging, about 4.02 V and +1.98 A |

The charge counter was decreasing, so it was not entirely frozen. Its starting offset/full-capacity state was inconsistent. These readings support a fuel-gauge calibration problem; they do not establish remaining runtime or prove a battery capacity.

The installed driver's `power_now` returned zero. The panel therefore calculates `abs(voltage_now × current_now)` after converting micro-units. This is **battery-terminal power**, not wall power or total system consumption while charging.

## What the toolkit changes

The bar displays voltage. The panel shows charging state, voltage, current, computed power and the raw gauge percentage. Discharging at 98–100% below 3.95 V creates this persistent local warning marker:

```text
~/.local/state/uconsole/battery-gauge-unreliable
```

This is a conservative inconsistency detector, not a state-of-charge model. The warning remains across charging/reboots until the gauge has been verified. Other programs using UPower or kernel capacity may still say 100%.

The helper **never writes PMIC registers, charge-current limits, capacity settings or the `calibrate` control**. It refreshes measurements and reports the limitation.

## Calibration is a separate physical test

First confirm the capacity printed on both installed cells and the configured total capacity. Charge to a real completed charge, judged from the controller's status/current behavior rather than the faulty 100% value. Calibration on this vendor driver requires a controlled battery learning cycle; it cannot be completed by refreshing the bar or plugging in for a moment.

The installed 6.12 driver's calibration control affects both full-capacity relearning and calibration state. Driver variants differ, so use instructions matched to the exact installed kernel. Do not copy register writes from another AXP model or kernel branch. The published toolkit does not automate the cycle, and **a completed calibration has not yet been verified on this unit**.

After a successful learning cycle, verify that percentage falls plausibly during discharge, the coulomb counter no longer exceeds full capacity, and reported charging/full states agree with current and voltage. Only then clear the marker:

```bash
rm -- "$HOME/.local/state/uconsole/battery-gauge-unreliable"
```

If the contradiction returns, the helper recreates it. No expected battery runtime is claimed without a timed discharge measurement.

Source inspection: [the tested kernel branch's battery driver](https://github.com/ak-rex/ClockworkPi-linux/blob/874351b52621220e99c9a2d3849219fcce39c37f/drivers/power/supply/axp20x_battery.c), [AXP223 register documentation](https://linux-sunxi.org/images/e/e5/AXP223_Datasheet_V1.0_en.pdf), [vendor author's calibration discussion](https://forum.clockworkpi.com/t/bookworm-6-6-y-for-the-uconsole-and-devterm/13235/164).
