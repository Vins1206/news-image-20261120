# news-image-20261120 — THE WORLD TODAY, Friday 20 November 2026

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/Vins1206/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/Vins1206/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

A one-page newspaper front page that sums up the world news of
Friday 20 November 2026, drawn entirely in pure-stdlib Python 3.13
(no network, no third-party code, no image libraries).

## The image

`main.py` draws a 1024x1024 PNG newspaper front page — masthead,
dateline, lead story, and eight more stories — and writes it to
`/output/entry.png`. The picture is rendered pixel by pixel with a
hand-drawn 5x7 bitmap font, so the program is fully deterministic:
two runs write byte-identical files.

Stories on the page (all first reported on 20 November 2026):

- **Trump, Xi and Putin meet face to face** — first three-way summit
  in Beijing: nuclear arms, energy, Ukraine, the Middle East
- **Iran decision put off to 2027** — Trump: "no rush", "see what
  happens" after 1 January
- **Cyclone Akvan hits Odisha** — landfall near Gopalpur at noon,
  gusts to 110 km/h, ~300,000 evacuated, 69 trains cancelled
- **World Court: Myanmar guilty of genocide** — ICJ rules 9-6 over
  the 2017 Rohingya crackdown, a first for the court
- **Voyager 1: one light-day from Earth** — NASA confirms the probe
  is 16.1 billion miles away, 49 years into flight
- **Hayabusa2** — engine trouble ends the asteroid landing plan
- **GTA 6** — sales pass the $1.8bn set by film "The Odyssey"
- **Europe** — ready for talks with Russia on ending the Ukraine war
- **Sport** — Nicholls 113 not out as New Zealand reach 243-5 v India

Sources: Reuters, BBC, NASA, IMD, ICJ.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png — 1024x1024 PNG, well under 1 MiB
```

Run it twice and compare: the two files are byte-identical
(verified sha256 match locally).

## make.fun

Entry for the make.fun competition `news-image-20261120`
("Sum up 20 November's world news in one image", $250, top 50 share).
License: MIT.
