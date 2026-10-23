# ai-flying-roadster-energy

Code and data behind the article **"Tesla's Flying Roadster Runs on "Free" Air. Its AI Will Have to Know When to Say No."**

A small, transparent physics model of the compressed-air ("cold-gas") thrusters on Tesla's 2026 Roadster Rocket.
It answers three questions from public numbers only (600 L of tank, ~250 kg of air, ten thrusters, >80 kN rear thrust):

1. **Fill:** how much electricity it takes to squeeze 250 kg of air into the tank (theoretical floor + real compressors).
2. **Hop:** how much air and electricity one 2.5 m hop uses, and how many hops a full tank gives.
3. **Blast and noise:** how far behind the car the wind stays at gale / hurricane force, and rough noise distances.

## Headline results (default assumptions)

| Quantity | Value |
|---|---|
| Estimated tank pressure | ~454 bar (6,580 psi) |
| Minimum fill energy (exergy) | 37 kWh |
| Fill electricity at 70 / 58 / 40 % compressor efficiency | 53 / 64 / 93 kWh |
| Equivalent EV driving per fill (0.19 kWh/km) | 280-490 km |
| Electricity per hop | 15-27 kWh (≈ 80-140 km of EV driving) |
| Work actually needed to lift the car 2.5 m | 0.013 kWh |
| Hops per full tank (2-4 g burns) | 2-4 |
| Hurricane-force wind (≥32.7 m/s), one 20 kN jet / merged 80 kN | ~28 m / ~55 m |
| Gale-force wind (≥17.2 m/s), one 20 kN jet / merged 80 kN | ~53 m / ~105 m |

All of these are estimates. Tesla has not published pressure, flow, hop count or refill energy.

## Run it

```bash
pip install -r requirements.txt
python model.py        # writes results/results.json
python make_charts.py  # writes charts/*.png
```

Or open `roadster_energy.ipynb` in Google Colab and run all cells.

## Files

- `model.py` – the model (tank state, fill energy, hop simulation, jet blast, noise).
- `make_charts.py` – the three article figures.
- `results/results.json` – every number quoted in the article.
- `charts/` – the figures.
- `roadster_energy.ipynb` – Colab notebook that runs everything.

## Main assumptions (edit the `A` dict in `model.py`)

Car mass 1,900 kg; hop apex 2.5 m; burns at 2 g (3 g and 4 g also run); nozzle efficiency 0.90; jets considered too weak below 20 bar;
EV use 0.19 kWh/km; electricity $0.18/kWh. Real-gas air properties from [CoolProp](https://github.com/CoolProp/CoolProp).
Jet decay uses the standard round-jet centre-line rule u = 7.0·√(F/ρ)/x. Noise uses acoustic efficiencies of 0.1-1 %; treat it as a rough warning only.

## Limits

Simplified vertical hop, no ground effect, no leaks or valve losses, textbook jet decay measured on lab jets, crude noise model
with no air absorption. Tank pressure is inferred from 250 kg in 600 L, not confirmed by Tesla.

## Licence

MIT. See `LICENSE`.
