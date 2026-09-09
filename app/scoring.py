"""
Two things live here:

1. opportunity_index() - the actual scoring formula from the brief (§14.3):
       OI = w1*U + w2*deltaS + w3*M - w4*R
   This is what positions each opportunity on the map. Weights are always
   passed in explicitly, never hardcoded silently - the brief scores you on
   "weights explicit and adjustable, no black boxes".

2. Unit sanity-check helpers (§4.4/§4.5) - NOT a feature, a guardrail. Run any
   sensitivity/concentration number the agent extracts through these before
   trusting it, since unit slips (aM vs fM vs pg/mL) are the single most
   common error the brief warns about.
"""
from dataclasses import dataclass

AVOGADRO = 6.022e23


def opportunity_index(
    unmet_need: float,
    sensitivity_gain: float,
    market_size: float,
    regulatory_burden: float,
    w_unmet_need: float,
    w_sensitivity_gain: float,
    w_market: float,
    w_regulatory_burden: float,
) -> float:
    weight_sum = w_unmet_need + w_sensitivity_gain + w_market + w_regulatory_burden
    if abs(weight_sum - 1.0) > 1e-6:
        raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")

    return (
        w_unmet_need * unmet_need
        + w_sensitivity_gain * sensitivity_gain
        + w_market * market_size
        - w_regulatory_burden * regulatory_burden
    )


@dataclass
class ConcentrationCheck:
    molar: float          # mol/L
    molecules_per_ml: float
    molecules_in_sample: float  # for a given sample volume


def molarity_to_molecules(molar: float, sample_volume_ml: float = 0.1) -> ConcentrationCheck:
    """
    Convert a molar concentration to molecules/mL and molecules-in-sample.
    Use this to sanity-check any sensitivity claim an agent pulls off the web -
    e.g. brief's own example: 1 aM = 1e-18 mol/L -> ~602 molecules/mL.
    """
    molecules_per_l = molar * AVOGADRO
    molecules_per_ml = molecules_per_l / 1000
    molecules_in_sample = molecules_per_ml * sample_volume_ml
    return ConcentrationCheck(molar, molecules_per_ml, molecules_in_sample)


def mass_conc_to_molar(pg_per_ml: float, molecular_weight_da: float) -> float:
    """
    Convert pg/mL -> mol/L, given the analyte's molecular weight in Daltons (g/mol).
    Brief's worked example: 0.5 pg/mL p-tau217 at 45 kDa =~ 11 fM (1.1e-14 mol/L).
    Look up molecular weights on UniProt (see brief §16) rather than guessing.
    """
    grams_per_ml = pg_per_ml * 1e-12
    grams_per_l = grams_per_ml * 1000
    return grams_per_l / molecular_weight_da
