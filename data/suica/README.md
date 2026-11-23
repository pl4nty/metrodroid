# Japan IC (Suica) station and bus stop data

This builds `suica_rail.mdst` and `suica_bus.mdst`, which replace the old
`data/felica_stations.db3` sqlite database.

Run `make` to fetch the pinned upstream files (checked against `sha512sums`),
merge them and build both MdSTs, then `make copy` to copy them into `mdst/`.

## Sources

* `legacy_rail.csv` and `legacy_bus.csv` are the contents of the old
  `felica_stations.db3`, exported as-is. That database came from Farebot (2011),
  which built it from [IC SFCard Fan][sfcardfan] data. It is the only source of
  English names and coordinates.

* [suicanfc-kd][] (GPLv3) provides newer Japanese-only station and bus stop
  lists, fetched at a pinned commit:
  * `StationCode.csv`, `StationCodeExtra.csv`: rail stations
  * `BusCode.csv`, `BusCodeExtra.csv`: bus operators and stops

## Merge rules (`extra/mdst/suica2csv.py`)

* The newer Japanese names win.
* English names and coordinates from the legacy data are kept only when the
  Japanese name still matches (after normalising variants like ヶ/ケ), either at
  the same code or at a unique station of the same name on the same line.
* Nothing is machine translated. Stations without a known English name only
  have a Japanese name, which Metrodroid shows instead.
* Placeholder rows (仮称, 未定) and bus codes wider than 16 bits are skipped.
* suicanfc-kd's `StationCode.csv` has abbreviated line names (eg: `K`), so the
  legacy line name for that line code is used where there is one.

## Station IDs

* Rail: `(area << 16) | (line << 8) | station`
* Bus: `(operator << 16) | stop`, using the full 16-bit codes from the card.
  Stop `0` of each operator is its "common" (共通) entry, which is used when a
  stop is not known.

[sfcardfan]: http://www.denno.net/SFCardFan/
[suicanfc-kd]: https://github.com/Kdroidwin/suicanfc-kd
