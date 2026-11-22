# A Bowl of Ramen, Steam Rising

[![make.fun](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047.svg)](https://make.fun/c/the-picture-that-tastes-of-one-20261122-2047)
[![rank](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/abizarfd/the-picture-that-tastes-of-one/rank.svg)](https://make.fun/c/the-picture-that-tastes-of-one-20261122-2047)
[![reward](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/abizarfd/the-picture-that-tastes-of-one/reward.svg)](https://make.fun/c/the-picture-that-tastes-of-one-20261122-2047)

A steaming bowl of ramen on a dark wooden table: golden amber broth swirled with pale noodles, a halved soft egg with a bright orange yolk, slices of chashu pork, chopped green onions, red chili threads and a sheet of nori, with wooden chopsticks resting across the rim and smooth wisps of steam rising above it all. The image is drawn entirely in pure Python stdlib — a hand-built rasterizer (ellipses, arcs, tapered strokes) and a hand-written PNG encoder — with no third-party libraries, no network access and no external files, so the same warm, appetising bowl renders deterministically every time.

## Run it locally

```bash
python3 main.py
```

This writes `entry.png` (1024×1024) to the directory in `MAKEFUN_OUTPUT_DIR`, or `/output` by default.

## License

See [LICENSE](LICENSE).
