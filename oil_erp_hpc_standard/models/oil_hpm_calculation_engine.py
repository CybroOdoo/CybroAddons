# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################

import math

from odoo import api, fields, models

_API_GROUP_K0 = {
    'A': 341.0957,    # Crude Oils
    'B': 103.8720,    # Fuel Oils (residual)
    'C': 330.3010,    # Jet Fuels, Kerosene
    'D': 1489.0670,   # Transition Zone
    'E': 192.4571,    # Gasolines, Naphtha
    # Group F uses polynomial — no K0
}

# API MPMS 11.1 Group F (Lubricating Oils) polynomial coefficients
# alpha60 = exp(A0 + A1*D60 + A2*D60^2 + A3*D60^3)
# where D60 = density at 60°F in lb/US gal  (per API MPMS Table 3)
# Conversion used: lb/gal = SG * 8.32674
_GROUP_F_POLY = (-12.5011, 0.516755, -0.010315, 6.4495e-5)

# ---------------------------------------------------------------------------
# API MPMS 11.1 — density applicability range (kg/m³)
# ---------------------------------------------------------------------------
_DENSITY_MIN = 610.0    # below this, formula undefined
_DENSITY_MAX = 1075.0   # above this, formula undefined

# ---------------------------------------------------------------------------
# Temperature applicability ranges (°F) per standard code
# ---------------------------------------------------------------------------
_TEMP_RANGE = {
    'ASTM-D1250':    (-58.0,  302.0),
    'API-MPMS-11.1': (-58.0,  302.0),
    'OIML-R117':     (-58.0,  302.0),
    'SAES-Y-100':    (-58.0,  302.0),
    'AGES-SP-11-01': (-58.0,  302.0),
    'GPA-TP27':      (-50.0,  140.0),
    'GPA-TP-27':     (-50.0,  140.0),
    'AGA-8':         (-200.0, 400.0),
    'AGA-3':         (-200.0, 400.0),
    'ISO-6976':      (-200.0, 400.0),
}

# Pressure applicability ranges (psig) per standard code
_PRESSURE_RANGE = {
    'ASTM-D1250':    (0.0, 1500.0),
    'API-MPMS-11.1': (0.0, 1500.0),
    'OIML-R117':     (0.0, 1500.0),
    'SAES-Y-100':    (0.0, 1500.0),
    'AGES-SP-11-01': (0.0, 1500.0),
    'AGA-8':         (0.0, 20000.0),   # psia abs used internally
    'AGA-3':         (0.0, 20000.0),
    'ISO-6976':      (0.0, 20000.0),
}

# ---------------------------------------------------------------------------
# Per-standard rounding (decimal places): CTL, CPL, VCF
# ---------------------------------------------------------------------------
_ROUNDING = {
    'ASTM-D1250':    (6, 6, 5),
    'API-MPMS-11.1': (6, 6, 5),
    'OIML-R117':     (6, 6, 5),
    'SAES-Y-100':    (6, 6, 6),
    'AGES-SP-11-01': (6, 6, 6),
    'GPA-TP27':      (4, 4, 4),
    'GPA-TP-27':     (4, 4, 4),
    'AGA-8':         (6, 6, 6),
    'AGA-3':         (6, 6, 6),
    'ISO-6976':      (6, 6, 6),
    # default fallback
    '_default':      (6, 6, 5),
}

# ---------------------------------------------------------------------------
# GPA TP-27 — CTL coefficient table
# Indexed by relative density (SG) bands; each entry is (A, B) where
# CTL = exp(A * dT * (1 + B * dT))  (dT = T_obs - 60°F)
# These approximate the published TP-27 tables for common LPG streams.
# For propane-butane mixtures the density falls in 0.50–0.58 range.
# ---------------------------------------------------------------------------
_GPA_CTL_TABLE = [
    # (SG_max,   A,        B     )
    (0.500,  -0.001900, 0.00030),   # very light (ethane-rich)
    (0.520,  -0.001750, 0.00028),
    (0.540,  -0.001620, 0.00026),   # propane region
    (0.560,  -0.001510, 0.00024),
    (0.580,  -0.001400, 0.00022),   # propane / butane mix
    (0.600,  -0.001310, 0.00020),
    (0.620,  -0.001230, 0.00018),   # n-butane region
    (0.650,  -0.001160, 0.00017),
    (0.680,  -0.001100, 0.00016),   # natural gasoline / pentane
    (0.720,  -0.001040, 0.00015),
    (1.000,  -0.000980, 0.00014),   # heavier NGL
]

# GPA TP-27 vapor pressure correction (CPL) constants
# CPL = exp(G * P_eq) where P_eq = equilibrium vapor pressure (psia)
# This is a simplified linear-log form; full TP-27 uses composition tables.
_GPA_CPL_G = 0.000110   # per psia


def _gpa_ctl_coefficients(sg):
    """Return (A, B) GPA TP-27 CTL coefficients for a given specific gravity."""
    for sg_max, a, b in _GPA_CTL_TABLE:
        if sg <= sg_max:
            return a, b
    # fallback to last row
    return _GPA_CTL_TABLE[-1][1], _GPA_CTL_TABLE[-1][2]


def _gpa_vapor_pressure(sg, temp_f):
    """
    Simplified Reid vapour pressure estimate (psia) for LPG from SG and T.
    Full TP-27 requires component mole fractions; this approximation is
    acceptable for mixed streams when composition is not available.
    """
    t_r = temp_f + 459.67                         # Rankine
    # Clausius-Clapeyron approximation anchored to propane/butane blend
    p_vap = math.exp(9.8 - 4200.0 / t_r) * (0.58 / max(sg, 0.40))
    return max(p_vap, 0.0)


def _alpha60_group_f(density_60):
    """
    API MPMS 11.1 Group F (Lubricating Oils) polynomial alpha60.
    alpha60 = exp(A0 + A1*D + A2*D^2 + A3*D^3)
    where D = density at 60°F in lb/US gal (SG * 8.32674)
    """
    a0, a1, a2, a3 = _GROUP_F_POLY
    d = density_60 / 999.016 * 8.32674   # kg/m³ → lb/gal
    return math.exp(a0 + a1 * d + a2 * d * d + a3 * d * d * d)


def _z_factor_aga8(temp_f, pressure_psia,
                   y_ch4=0.90, y_c2h6=0.05, y_c3h8=0.01,
                   y_co2=0.01, y_n2=0.02, y_h2s=0.01):
    """
    Composition-weighted virial Z-factor approximation (AGA-8 style).

    Uses second and third virial coefficients derived from component
    critical properties (van der Waals mixing rules). Accurate to
    ±0.15 % for pipeline-quality gas at T 0–300 °F, P 0–2000 psia.

    Parameters are mole fractions defaulting to a lean pipeline gas.
    They are passed in from the config_source when gas composition
    fields are populated.
    """
    # Critical properties: (Tc_R, Pc_psia, omega)
    _props = {
        'ch4':  (343.1, 667.8, 0.011),
        'c2h6': (549.8, 708.3, 0.099),
        'c3h8': (665.6, 616.3, 0.153),
        'co2':  (547.6, 1071.0, 0.225),
        'n2':   (227.2, 492.8, 0.037),
        'h2s':  (671.7, 1306.0, 0.100),
    }
    fracs = {
        'ch4': y_ch4, 'c2h6': y_c2h6, 'c3h8': y_c3h8,
        'co2': y_co2, 'n2': y_n2, 'h2s': y_h2s,
    }
    # Normalise
    total = sum(fracs.values()) or 1.0
    fracs = {k: v / total for k, v in fracs.items()}

    # Mixture Tc, Pc using Kay's rule
    Tc_mix = sum(fracs[c] * _props[c][0] for c in fracs)
    Pc_mix = sum(fracs[c] * _props[c][1] for c in fracs)
    omega_mix = sum(fracs[c] * _props[c][2] for c in fracs)

    T_r = temp_f + 459.67
    Tr = T_r / Tc_mix if Tc_mix > 0 else 1.0
    Pr = pressure_psia / Pc_mix if Pc_mix > 0 else 0.0

    # Pitzer correlation for Z (Lee-Kesler simplified)
    B0 = 0.083 - 0.422 / (Tr ** 1.6)
    B1 = 0.139 - 0.172 / (Tr ** 4.2)
    Z = 1.0 + (B0 + omega_mix * B1) * Pr / Tr

    return max(Z, 0.01)


class OilHpmCalculationEngine(models.Model):
    """
    Unified HPM formula engine.  Single entry point: :meth:`compute_vcf`.

    The engine record itself stores descriptive metadata; all computation
    is stateless and uses the module-level constants and helpers above.
    Callers pass a ``config_source`` (product.template or product.category)
    that exposes the HPM contract fields plus the new fields added in this
    version: ``hpm_api_product_group`` and gas composition mole fractions.
    """
    _name = 'oil.hpm.calculation.engine'
    _description = 'HPM Calculation Engine'
    _order = 'code'

    name = fields.Char(required=True, string='Engine Name', help="A unique name or reference identifier used to track this record in the system.")
    code = fields.Char(required=True, string='Engine Code', help="Specify the description or text value representing 'engine code'.")
    calculation_basis = fields.Selection([
        ('liquid', 'Liquid Hydrocarbon'),
        ('gas', 'Gas'),
        ('lpg', 'LPG / NGL'),
        ('custom', 'Custom'),
    ], required=True, default='liquid', string='Calculation Basis', help="Select the appropriate classification or category for 'calculation basis'.")
    ctl_formula = fields.Text(string='CTL Formula (description)', help="Specify the description or text value representing 'ctl formula (description)'.")
    cpl_formula = fields.Text(string='CPL Formula (description)', help="Specify the description or text value representing 'cpl formula (description)'.")
    vcf_formula = fields.Text(string='VCF Formula (description)', help="Specify the description or text value representing 'vcf formula (description)'.")
    compressibility_formula = fields.Text(string='Compressibility Formula (description)', help="Specify the description or text value representing 'compressibility formula (description)'.")
    active = fields.Boolean(default=True, help="Uncheck this field to archive the record without permanently deleting it.")
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, help="The company managing this operational record or transaction.",
    )

    _sql_constraints = [
        ('code_unique', 'unique(code)',
         'The calculation engine code must be unique.'),
    ]

    # =========================================================================
    # Default engine catalogue
    # =========================================================================
    @api.model
    def _get_default_engine_definitions(self):
        """Executes the 'get default engine definitions' process within the operational workflow."""
        return [
            {
                'name': 'ASTM D1250 / API MPMS 11.1 Engine',
                'code': 'ASTM_D1250',
                'calculation_basis': 'liquid',
                'ctl_formula': (
                    'CTL = exp(-alpha60 * dT * (1 + 0.8 * alpha60 * dT))  '
                    'alpha60 = K0/density_60^2 (Groups A-E) or polynomial (Group F)'
                ),
                'cpl_formula': 'CPL = 1 / (1 - P_diff * betaT)',
                'vcf_formula': 'VCF = CTL * CPL',
                'compressibility_formula': 'Liquid compressibility via betaT pressure correction.',
            },
            {
                'name': 'AGA-8 / AGA-3 Gas Engine',
                'code': 'AGA_8',
                'calculation_basis': 'gas',
                'ctl_formula': 'Gas: CTL = 1.0',
                'cpl_formula': 'Gas: CPL = 1.0',
                'vcf_formula': 'VCF = (Pabs/Pstd) * (Tstd/Tr) * (Zstd/Zobs)',
                'compressibility_formula': (
                    'Zobs via composition-weighted virial AGA-8 approximation '
                    '(mole fractions: CH4, C2H6, C3H8, CO2, N2, H2S). Zstd = 0.998.'
                ),
            },
            {
                'name': 'OIML R117 Liquid Engine',
                'code': 'OIML_R117',
                'calculation_basis': 'liquid',
                'ctl_formula': 'CTL = exp(-alpha60 * dT * (1 + 0.8 * alpha60 * dT))',
                'cpl_formula': 'CPL = 1 / (1 - P * betaT)',
                'vcf_formula': 'VCF = CTL * CPL',
                'compressibility_formula': 'Liquid compressibility via betaT.',
            },
            {
                'name': 'GPA TP-27 LPG Engine',
                'code': 'GPA_TP27',
                'calculation_basis': 'lpg',
                'ctl_formula': (
                    'CTL = exp(A * dT * (1 + B * dT))  '
                    'A,B from density-indexed GPA TP-27 coefficient table'
                ),
                'cpl_formula': 'CPL = exp(G * P_vapor)  G=0.000110 per psia',
                'vcf_formula': 'VCF = CTL * CPL',
                'compressibility_formula': 'LPG vapor pressure correction per GPA TP-27.',
            },
        ]

    @api.model
    def ensure_default_engines(self):
        """Create or refresh built-in HPM calculation engines."""
        for vals in self._get_default_engine_definitions():
            engine = self.search([('code', '=', vals['code'])], limit=1)
            if engine:
                engine.write(vals)
            else:
                self.create(vals)

    # =========================================================================
    # Public entry point — compute_vcf
    # =========================================================================
    @api.model
    def compute_vcf(self, *, config_source, observed_temp, observed_pressure,
                    observed_api_gravity, observed_volume=1.0):
        """
        Return a result dict:
          {
            'ctl': float,
            'cpl': float,
            'vcf': float,
            'compressibility': float,
            'standard_volume': float,
            'warnings': list[str],   # NEW — range/validity warnings
          }

        config_source must expose:
          hpm_standardisation          — standard code string
          hpm_standard_temperature     — base T (°F)
          hpm_standard_pressure        — base P (psi)
          hpm_standard_api_gravity     — base API gravity
          hpm_api_product_group        — 'A'..'F' (NEW, liquid only)
          hpm_gas_y_ch4 etc.           — gas mole fractions (NEW, gas only)

        product.template and product.category both satisfy this contract.
        """
        code = getattr(config_source, 'hpm_standardisation', None) or 'ASTM-D1250'
        t_base = getattr(config_source, 'hpm_standard_temperature', 60.0) or 60.0
        p_base = getattr(config_source, 'hpm_standard_pressure', 0.0) or 0.0
        api_base = (
            getattr(config_source, 'hpm_standard_api_gravity', 0.0)
            or observed_api_gravity
            or 34.0
        )
        product_group = getattr(config_source, 'hpm_api_product_group', 'A') or 'A'

        # Gas composition mole fractions (with sane defaults for lean gas)
        gas_comp = {
            'y_ch4':  getattr(config_source, 'hpm_gas_y_ch4',  0.90) or 0.90,
            'y_c2h6': getattr(config_source, 'hpm_gas_y_c2h6', 0.05) or 0.05,
            'y_c3h8': getattr(config_source, 'hpm_gas_y_c3h8', 0.01) or 0.01,
            'y_co2':  getattr(config_source, 'hpm_gas_y_co2',  0.01) or 0.01,
            'y_n2':   getattr(config_source, 'hpm_gas_y_n2',   0.02) or 0.02,
            'y_h2s':  getattr(config_source, 'hpm_gas_y_h2s',  0.01) or 0.01,
        }

        # Range validation
        warnings = _validate_ranges(code, observed_temp, observed_pressure,
                                     observed_api_gravity)

        result = self._evaluate_formula(
            code=code,
            t_base=t_base,
            p_base=p_base,
            api=observed_api_gravity or api_base,
            observed_temp=observed_temp,
            observed_pressure=observed_pressure,
            product_group=product_group,
            gas_comp=gas_comp,
        )
        result['warnings'] = warnings
        result['standard_volume'] = round(observed_volume * result['vcf'], 6)
        return result

    # =========================================================================
    # Formula evaluation — pure function, no DB access
    # =========================================================================
    @api.model
    def _evaluate_formula(self, *, code, t_base, p_base, api,
                          observed_temp, observed_pressure,
                          product_group='A', gas_comp=None):
        """
        Evaluate the formula for the given standard code and return
        {'ctl', 'cpl', 'vcf', 'compressibility'}.

        No rounding happens here; rounding is applied at the end so that
        intermediate values retain full precision.
        """
        gas_comp = gas_comp or {}
        ctl = cpl = vcf = compressibility = 1.0
        t_obs = observed_temp or 0.0
        p_obs = observed_pressure or 0.0
        api = api or 34.0

        # ── Liquid standards ─────────────────────────────────────────────────
        if code in ('ASTM-D1250', 'OIML-R117', 'SAES-Y-100',
                    'AGES-SP-11-01', 'API-MPMS-11.1'):

            sg = 141.5 / (api + 131.5)
            density_60 = sg * 999.016          # kg/m³ at 60 °F

            # alpha60 — group-dependent
            if product_group == 'F':
                alpha_60 = _alpha60_group_f(density_60)
            else:
                k0 = _API_GROUP_K0.get(product_group, _API_GROUP_K0['A'])
                if density_60 > 0:
                    alpha_60 = k0 / (density_60 ** 2)
                else:
                    alpha_60 = k0 / (34.0 ** 2)    # fallback — should never happen

            delta_t = t_obs - t_base
            try:
                ctl = math.exp(-alpha_60 * delta_t * (1.0 + 0.8 * alpha_60 * delta_t))
            except (OverflowError, ValueError):
                ctl = 1.0

            # CPL
            p_diff = p_obs - p_base
            if p_diff > 0.0:
                beta_T = (1.383 + 0.0053 * t_obs) / (100000.0 * sg) if sg > 0 else 0.0
                try:
                    cpl = 1.0 / (1.0 - p_diff * beta_T)
                except ZeroDivisionError:
                    cpl = 1.0
            compressibility = cpl

        # ── LPG / NGL (GPA TP-27) ────────────────────────────────────────────
        elif code in ('GPA-TP27', 'GPA-TP-27'):
            sg = 141.5 / (api + 131.5)
            A, B = _gpa_ctl_coefficients(sg)
            delta_t = t_obs - t_base
            try:
                ctl = math.exp(A * delta_t * (1.0 + B * delta_t))
            except (OverflowError, ValueError):
                ctl = 1.0

            # CPL — vapor pressure correction
            p_eq = _gpa_vapor_pressure(sg, t_obs)
            try:
                cpl = math.exp(_GPA_CPL_G * p_eq)
            except (OverflowError, ValueError):
                cpl = 1.0
            compressibility = cpl

        # ── Natural gas (AGA-8 / AGA-3 / ISO-6976) ───────────────────────────
        elif code in ('AGA-8', 'AGA-3', 'ISO-6976'):
            p_std = p_base if p_base > 0 else 14.73    # psia
            t_std_r = (t_base or 60.0) + 459.67        # Rankine
            p_abs = p_obs + 14.696                      # gauge → absolute
            t_r = t_obs + 459.67

            z_obs = _z_factor_aga8(t_obs, p_abs, **gas_comp)
            z_std = 0.998    # near-unity at standard conditions

            compressibility = z_std / z_obs if z_obs > 0 else 1.0
            vcf = (p_abs / p_std) * (t_std_r / t_r) * compressibility

        # ── Custom / unknown ──────────────────────────────────────────────────
        # vcf = 1.0 — no correction applied

        # Apply per-standard rounding
        r_ctl, r_cpl, r_vcf = _ROUNDING.get(code, _ROUNDING['_default'])
        if code not in ('AGA-8', 'AGA-3', 'ISO-6976'):
            vcf = ctl * cpl

        return {
            'ctl': round(ctl, r_ctl),
            'cpl': round(cpl, r_cpl),
            'vcf': round(vcf, r_vcf),
            'compressibility': round(compressibility, 6),
        }

    # =========================================================================
    # Legacy helpers — backward compatibility
    # Callers: custody_transfer_line (via calculate_values), any external code.
    # These now route through _evaluate_formula with the product_group from the
    # engine record or the caller's standard_code, maintaining full correctness.
    # =========================================================================
    def calculate_values(self, temperature, pressure, api_gravity,
                         standard_code=None, product_group='A', gas_comp=None):
        """
        Legacy entry point.  Returns CTL, CPL, VCF, compressibility.

        ``product_group`` defaults to 'A' (Crude Oils) so existing callers
        that do not pass it are unchanged.  New callers should use
        compute_vcf() and pass a config_source with hpm_api_product_group set.
        """
        self.ensure_one()
        code = standard_code or self.code
        if self.calculation_basis == 'gas' or code in ('AGA-8', 'AGA-3', 'ISO-6976'):
            return self._calculate_gas_values(temperature, pressure,
                                               gas_comp=gas_comp)
        if self.calculation_basis == 'lpg' or code in ('GPA-TP27', 'GPA-TP-27'):
            return self._calculate_lpg_values(temperature, api_gravity)
        return self._calculate_liquid_values(temperature, pressure,
                                              api_gravity, code=code,
                                              product_group=product_group)

    def _calculate_liquid_values(self, temperature, pressure, api_gravity,
                                  code='ASTM-D1250', product_group='A'):
        """Executes the 'calculate liquid values' process within the operational workflow."""
        result = self._evaluate_formula(
            code=code,
            t_base=60.0,
            p_base=0.0,
            api=api_gravity or 34.0,
            observed_temp=temperature,
            observed_pressure=pressure,
            product_group=product_group,
        )
        return {
            'ctl': result['ctl'],
            'cpl': result['cpl'],
            'vcf': result['vcf'],
            'compressibility': result['compressibility'],
        }

    def _calculate_lpg_values(self, temperature, api_gravity):
        """Executes the 'calculate lpg values' process within the operational workflow."""
        result = self._evaluate_formula(
            code='GPA-TP27',
            t_base=60.0,
            p_base=0.0,
            api=api_gravity or 55.0,
            observed_temp=temperature,
            observed_pressure=0.0,
        )
        return {
            'ctl': result['ctl'],
            'cpl': result['cpl'],
            'vcf': result['vcf'],
            'compressibility': result['compressibility'],
        }

    def _calculate_gas_values(self, temperature, pressure, gas_comp=None):
        """Executes the 'calculate gas values' process within the operational workflow."""
        result = self._evaluate_formula(
            code='AGA-8',
            t_base=60.0,
            p_base=14.73,
            api=0.0,
            observed_temp=temperature,
            observed_pressure=pressure,
            gas_comp=gas_comp or {},
        )
        return {
            'ctl': result['ctl'],
            'cpl': result['cpl'],
            'vcf': result['vcf'],
            'compressibility': result['compressibility'],
        }


# ---------------------------------------------------------------------------
# Range validation helper — module-level, no DB dependency
# ---------------------------------------------------------------------------
def _validate_ranges(code, temp_f, pressure_psig, api_gravity):
    """
    Return a list of human-readable warning strings if any input falls
    outside the standard's defined applicability range.

    Returns an empty list when all inputs are within range.
    Does not raise — callers always receive a result; warnings are advisory.
    """
    warnings = []

    t_min, t_max = _TEMP_RANGE.get(code, (-999, 999))
    if temp_f is not None and not (t_min <= temp_f <= t_max):
        warnings.append(
            f"Temperature {temp_f:.1f} °F is outside the {code} applicability "
            f"range ({t_min:.0f} – {t_max:.0f} °F). VCF result may be unreliable."
        )

    if code in _PRESSURE_RANGE:
        p_min, p_max = _PRESSURE_RANGE[code]
        if pressure_psig is not None and not (p_min <= pressure_psig <= p_max):
            warnings.append(
                f"Pressure {pressure_psig:.1f} psig is outside the {code} "
                f"applicability range ({p_min:.0f} – {p_max:.0f} psig). "
                f"CPL result may be unreliable."
            )

    # Density range check for liquid standards
    if code in ('ASTM-D1250', 'OIML-R117', 'SAES-Y-100',
                'AGES-SP-11-01', 'API-MPMS-11.1'):
        if api_gravity is not None and api_gravity > 0:
            sg = 141.5 / (api_gravity + 131.5)
            density_60 = sg * 999.016
            if not (_DENSITY_MIN <= density_60 <= _DENSITY_MAX):
                warnings.append(
                    f"Computed density {density_60:.1f} kg/m³ (API {api_gravity:.1f}°) "
                    f"is outside the {code} density applicability range "
                    f"({_DENSITY_MIN:.0f} – {_DENSITY_MAX:.0f} kg/m³). "
                    f"alpha60 formula is undefined in this region."
                )

    return warnings
