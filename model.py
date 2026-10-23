"""What does one 'hop' of a compressed-air Roadster really cost, and how far should people stand?
Inputs reported at Tesla's 15 Oct 2026 reveal: 600 L of tank volume holding about 250 kg of air, ten
cold-gas thrusters, more than 80 kN of thrust from the four rear thrusters. Everything else is an
assumption, listed here and varied in the sensitivity runs. Real-gas air properties from CoolProp."""
import json, math
import numpy as np
import CoolProp.CoolProp as CP
from scipy.optimize import brentq

V_TANK, M_AIR, T_AMB, P_AMB = 0.600, 250.0, 300.0, 101325.0
G = 9.81
A = dict(
    car_mass=1900.0,          # kg. Not published; reports describe a car of over 4,000 lb (~1,815 kg+). Range 1,800-2,100 tested.
    compressor_eff=0.58,      # fraction of the theoretical minimum (isothermal) work; IEEE Spectrum's air-car figure. 0.40-0.70 tested.
    ev_kwh_per_km=0.19,       # a typical efficient EV (~30 kWh per 100 miles); assumption.
    nozzle_eff=0.90,          # share of ideal jet kinetic energy actually achieved.
    hop_height=2.5,           # m, apex height of one hop (clears a car)
    boost_g=2.0,              # thrust during take-off and landing burns, in multiples of the car's weight
    p_min=20e5,               # Pa, tank pressure below which the jets are considered too weak to hop
    price_per_kwh=0.18,       # USD, rough US household electricity price; assumption
)

def tank_pressure():
    rho = M_AIR / V_TANK
    return brentq(lambda p: CP.PropsSI("D", "T", T_AMB, "P", p, "Air") - rho, 1e6, 2e8)

def min_fill_energy(p, T=T_AMB):
    """Exergy of the stored air relative to the atmosphere: the least electricity any compressor could use."""
    h, s = CP.PropsSI("H", "T", T, "P", p, "Air"), CP.PropsSI("S", "T", T, "P", p, "Air")
    h0, s0 = CP.PropsSI("H", "T", T_AMB, "P", P_AMB, "Air"), CP.PropsSI("S", "T", T_AMB, "P", P_AMB, "Air")
    rho = CP.PropsSI("D", "T", T, "P", p, "Air")
    return ((h - h0) - T_AMB * (s - s0)) * rho * V_TANK      # J for the whole tank

def exhaust_velocity(rho, T):
    """Ideal expansion from the tank state to ambient pressure (isentropic), times nozzle efficiency.
    Falls back to the ideal-gas formula when the expanded gas would be colder than CoolProp's air model allows."""
    try:
        h0 = CP.PropsSI("H", "D", rho, "T", T, "Air"); s0 = CP.PropsSI("S", "D", rho, "T", T, "Air")
        he = CP.PropsSI("H", "P", P_AMB, "S", s0, "Air")
        return math.sqrt(max(0.0, 2 * A["nozzle_eff"] * (h0 - he)))
    except ValueError:
        p = CP.PropsSI("P", "D", rho, "T", T, "Air")
        return math.sqrt(max(0.0, 2 * A["nozzle_eff"] * 1005 * T * (1 - (P_AMB / p) ** 0.2857)))

def hops(car_mass=None, n_poly=1.0, dt=0.01):
    """Blow the tank down hop after hop until its pressure falls below p_min.
    n_poly = 1.0: the tank stays at room temperature (slow hops, heat flows in: best case).
    n_poly = 1.3: the gas cools as it expands (fast back-to-back hops: closer to reality, worse case)."""
    m = car_mass or A["car_mass"]
    rho0 = M_AIR / V_TANK; rho = rho0; T = T_AMB
    v_apex = math.sqrt(2 * G * A["hop_height"]); thrust = A["boost_g"] * m * G
    t_burn = v_apex / ((A["boost_g"] - 1) * G)               # each burn (up, then braking on the way down)
    out = []
    while True:
        p = CP.PropsSI("P", "D", rho, "T", T, "Air")
        if p < A["p_min"]: break
        used = 0.0; ue_sum = 0.0; n = 0; ok = True
        for _ in range(2):                                     # take-off burn, landing burn
            t = 0.0
            while t < t_burn:
                ue = exhaust_velocity(rho, T)
                dm = thrust / ue * dt if ue > 50 else 1e9
                rho_new = (rho * V_TANK - dm) / V_TANK
                if rho_new <= 0.5 or CP.PropsSI("P", "D", rho_new, "T", max(T * (rho_new / rho) ** (n_poly - 1), 60), "Air") < A["p_min"]:
                    ok = False; break
                T = T * (rho_new / rho) ** (n_poly - 1); rho = rho_new
                used += dm; ue_sum += ue; n += 1; t += dt
            if not ok: break
        if not ok: break
        p_after = CP.PropsSI("P", "D", rho, "T", T, "Air")
        out.append(dict(air_kg=used, ue_avg=ue_sum / n, p_after_bar=p_after / 1e5, T_after_K=T))
    return out

def blast_speed(x, thrust_N):
    """Centre-line speed of a round turbulent jet far from the nozzle: u = 7.0*sqrt(J/rho)/x (momentum flux J = thrust)."""
    return 7.0 * math.sqrt(thrust_N / 1.2) / x

def noise_spl(r, thrust_N, ue, eta):
    """Sound level at distance r (m) on hard ground: acoustic power = eta * jet power; hemispherical spreading."""
    Lw = 10 * math.log10(max(eta * 0.5 * thrust_N * ue, 1e-12) / 1e-12)
    return Lw - 20 * math.log10(r) - 8

if __name__ == "__main__":
    R = {}
    p = tank_pressure(); R["tank_pressure_bar"] = p / 1e5; R["tank_pressure_psi"] = p / 6894.76
    E = min_fill_energy(p); R["min_fill_kWh"] = E / 3.6e6
    R["fill_kWh"] = {f"{e:.2f}": E / 3.6e6 / e for e in (0.40, 0.58, 0.70)}
    R["fill_km"] = {k: v / A["ev_kwh_per_km"] for k, v in R["fill_kWh"].items()}
    R["fill_usd"] = {k: v * A["price_per_kwh"] for k, v in R["fill_kWh"].items()}
    R["refill_power_kW_for_30min"] = R["fill_kWh"]["0.58"] / 0.5
    # also the 10,000 psi figure from 2018 (would mean more air than 250 kg)
    R["min_fill_kWh_at_690bar"] = min_fill_energy(690e5) / 3.6e6
    # hops
    H = hops(n_poly=1.3); R["hops_backtoback"] = H
    Hw = hops(n_poly=1.0); R["hops_rewarmed"] = Hw
    R["hops_by_mass"] = {m: [len(hops(car_mass=m, n_poly=1.3)), len(hops(car_mass=m, n_poly=1.0))] for m in (1800, 1900, 2100)}
    sweep = {}
    for bg in (2.0, 3.0, 4.0):
        A["boost_g"] = bg
        hs = hops(n_poly=1.3); hw = hops(n_poly=1.0)
        sweep[bg] = dict(backtoback=[h["air_kg"] for h in hs], rewarmed=[h["air_kg"] for h in hw],
                         p_backtoback=[h["p_after_bar"] for h in hs], p_rewarmed=[h["p_after_bar"] for h in hw])
    A["boost_g"] = 2.0
    R["boost_sweep"] = sweep
    lift = A["car_mass"] * G * A["hop_height"] / 3.6e6
    fill = R["fill_kWh"]["0.58"]
    R["lift_work_kWh"] = lift
    R["first_hop_kWh"] = H[0]["air_kg"] / M_AIR * fill
    R["avg_hop_kWh_backtoback"] = fill / len(H); R["avg_hop_kWh_rewarmed"] = fill / len(Hw)
    R["avg_hop_km"] = R["avg_hop_kWh_backtoback"] / A["ev_kwh_per_km"]
    R["hop_efficiency"] = lift / R["avg_hop_kWh_backtoback"]
    # blast and noise (four rear thrusters, >80 kN total; one nozzle = 20 kN)
    xs = np.array([2, 5, 10, 20, 30, 50, 75, 100, 150, 200, 300, 500])
    ue0 = H[0]["ue_avg"]
    R["blast"] = {"x": xs.tolist(), "one_nozzle_20kN": [blast_speed(x, 20e3) for x in xs],
                  "merged_80kN": [blast_speed(x, 80e3) for x in xs]}
    for name, F in (("one_nozzle", 20e3), ("merged", 80e3)):
        R[f"dist_beaufort12_{name}"] = 7.0 * math.sqrt(F / 1.2) / 32.7
        R[f"dist_beaufort8_{name}"] = 7.0 * math.sqrt(F / 1.2) / 17.2
    R["noise"] = {f"{eta}": [noise_spl(x, 80e3, ue0, eta) for x in xs] for eta in (0.001, 0.003, 0.01)}
    def dist_for(level, eta): return 10 ** ((10 * math.log10(eta * 0.5 * 80e3 * ue0 / 1e-12) - 8 - level) / 20)
    R["noise_dist"] = {f"{lvl}dB": {f"{eta}": dist_for(lvl, eta) for eta in (0.001, 0.003, 0.01)} for lvl in (140, 120, 85)}
    R["jet_power_MW"] = 0.5 * 80e3 * ue0 / 1e6; R["ue0"] = ue0
    R["assumptions"] = A
    json.dump(R, open("results/results.json", "w"), indent=1)
    s = {k: v for k, v in R.items() if k not in ("hops_backtoback", "hops_rewarmed", "blast", "noise")}
    print(json.dumps(s, indent=1))
    print("hops back-to-back:", [(round(h["air_kg"], 1), round(h["ue_avg"]), round(h["p_after_bar"]), round(h["T_after_K"])) for h in H])
    print("hops rewarmed:", [(round(h["air_kg"], 1), round(h["ue_avg"]), round(h["p_after_bar"])) for h in Hw])
