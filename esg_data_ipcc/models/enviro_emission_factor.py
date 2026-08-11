# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
##############################################################################
from __future__ import annotations

import logging
from io import BytesIO
from typing import Optional

import re

import requests
import openpyxl

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Raw EFDB column header → internal key
COLUMN_MAP = {
    "EF ID":                            "ef_id",
    "IPCC 1996 Source/Sink Category":   "category_1996",
    "IPCC 2006 Source/Sink Category":   "category_2006",
    "Gas":                              "gas",
    "Fuel 1996":                        "fuel_1996",
    "Fuel 2006":                        "fuel_2006",
    "Description":                      "description",
    "Technologies / Pracices":          "technologies",   # EFDB typo preserved
    "Technologies / Practices":         "technologies",
    "Parameters / Conditions":          "parameters",
    "Region / Regional Conditions":     "region",
    "Other properties":                 "other_properties",
    "Value":                            "value",
    "Unit":                             "unit",
    "Data provider":                    "data_provider",
    "Source of data":                   "source_of_data",
}

GAS_CODE_MAP = {
    "CARBON DIOXIDE":       "co2",
    "CO2":                  "co2",
    "METHANE":              "ch4",
    "CH4":                  "ch4",
    "NITROUS OXIDE":        "n2o",
    "N2O":                  "n2o",
    "SULFUR HEXAFLUORIDE":  "sf6",
    "SF6":                  "sf6",
    "NITROGEN TRIFLUORIDE": "nf3",
    "NF3":                  "nf3",
}

# IPCC category prefix → (odoo scope, odoo category)
CATEGORY_MAP = [
    ("1A3B", "scope1", "fleet"),
    ("1A3",  "scope1", "travel"),
    ("1A",   "scope1", "energy"),
    ("1B",   "scope1", "energy"),
    ("2",    "scope1", "other"),
    ("3A",   "scope1", "other"),
    ("3B",   "scope1", "other"),
    ("3C",   "scope1", "other"),
    ("4",    "scope1", "waste"),
]

EFDB_BASE = "https://www.ipcc-nggip.iges.or.jp/EFDB"

# Exact unit strings that represent non-physical or ratio measurements — skip these rows
_SKIP_UNIT_EXACT = frozenset([
    "per year", "months", "parts per billion by volume",
    "asse", "installe", "equipment",
])

# Ton-denominated special compound units that should resolve to the tonne UoM
_TONNE_COMPOUND_UNITS = frozenset([
    "(kg PFC/tAl)/(AE-Minutes/cellday)",
    "(kg PFC/tAl)/(mV/day)",
    "kg SF6/tonnes magnesium produced or smelted",
])


class EnviroEmissionFactor(models.Model):
    """Extend enviro.emission.factor with IPCC EFDB import/update actions and helpers."""
    _inherit = "enviro.emission.factor"

    is_ipcc_factor = fields.Boolean(
        string="Is IPCC Factor",
        compute="_compute_is_ipcc_factor",
        store=True,
    )

    @api.depends("code")
    def _compute_is_ipcc_factor(self):
        for rec in self:
            rec.is_ipcc_factor = bool(rec.code and rec.code.startswith("EFDB-"))

    # ── Public actions ────────────────────────────────────────────────────────

    def action_import_from_ipcc(self, source_id=None):
        """Download the IPCC EFDB and create new emission factor records.

        Rows whose code already exists in Odoo are skipped unchanged.
        """
        rows = self._parse_efdb_xls(self._get_ipcc_xls_file())

        source = self.env["enviro.data.source"].browse(source_id) if source_id else None
        filter_region = source.ipcc_region.lower() if source and source.ipcc_region else None
        filter_countries = [c.name.lower() for c in source.ipcc_country_ids] if source and source.ipcc_country_ids else []
        if filter_region or filter_countries:
            filtered_rows = []
            for row in rows:
                row_region = (row.get("region") or "").lower()
                match = False
                if filter_region and filter_region in row_region:
                    match = True
                if not match and filter_countries:
                    for c in filter_countries:
                        if c in row_region:
                            match = True
                            break
                if match:
                    filtered_rows.append(row)
            rows = filtered_rows

        uoms = self._load_ipcc_uoms()
        gas_map = {g.code: g.id for g in self.env["enviro.gas"].search([])}
        existing = {r["code"] for r in self.search_read([("code", "!=", False)], ["code"])}

        created = skipped_existing = errors = 0
        skip_units: dict[str, int] = {}
        for row in rows:
            code = f"EFDB-{row['ef_id']}"
            if code in existing:
                skipped_existing += 1
                continue
            vals = self._build_factor_vals(row, code, uoms, gas_map, source_id=source_id)
            if vals is None:
                unit = (row.get("unit") or "").strip()
                skip_units[unit] = skip_units.get(unit, 0) + 1
                continue
            try:
                self.create(vals)
                existing.add(code)
                created += 1
            except Exception as e:
                _logger.warning("EFDB create error row %s: %s", row["ef_id"], e)
                errors += 1

        return self._ipcc_notify(
            created=created,
            skipped_existing=skipped_existing,
            skip_units=skip_units,
            errors=errors,
        )

    def action_update_from_ipcc(self, source_id=None):
        """Download the IPCC EFDB and update existing IPCC emission factor records.

        - New EFDB rows are created.
        - Existing IPCC factors (code starts with 'EFDB-') are updated.
        - Factors no longer present in the EFDB are archived.

        Fields updated:  kg_co2e_per_unit, scope, category, uom_id, region,
                         source, notes, gas_line_ids (replaced wholesale).
        Never touched:   name, valid_from, valid_to, company_id.
        """
        rows = self._parse_efdb_xls(self._get_ipcc_xls_file())

        source = self.env["enviro.data.source"].browse(source_id) if source_id else None
        filter_region = source.ipcc_region.lower() if source and source.ipcc_region else None
        filter_countries = [c.name.lower() for c in source.ipcc_country_ids] if source and source.ipcc_country_ids else []
        if filter_region or filter_countries:
            filtered_rows = []
            for row in rows:
                row_region = (row.get("region") or "").lower()
                match = False
                if filter_region and filter_region in row_region:
                    match = True
                if not match and filter_countries:
                    for c in filter_countries:
                        if c in row_region:
                            match = True
                            break
                if match:
                    filtered_rows.append(row)
            rows = filtered_rows

        uoms = self._load_ipcc_uoms()
        gas_map = {g.code: g.id for g in self.env["enviro.gas"].search([])}

        efdb_by_code = {f"EFDB-{row['ef_id']}": row for row in rows}
        existing_factors = self.search([("code", "=like", "EFDB-%")])
        existing_by_code = {f.code: f for f in existing_factors}

        created = updated = archived = errors = 0
        skip_units: dict[str, int] = {}

        for code, row in efdb_by_code.items():
            vals = self._build_factor_vals(row, code, uoms, gas_map, source_id=source_id)
            if vals is None:
                unit = (row.get("unit") or "").strip()
                skip_units[unit] = skip_units.get(unit, 0) + 1
                continue
            try:
                if code in existing_by_code:
                    for protected in ("name", "valid_from", "valid_to", "company_id"):
                        vals.pop(protected, None)
                    if "gas_line_ids" in vals:
                        vals["gas_line_ids"] = [Command.clear()] + vals["gas_line_ids"]
                    existing_by_code[code].write(vals)
                    updated += 1
                else:
                    self.create(vals)
                    created += 1
            except Exception as e:
                _logger.warning("EFDB update error code %s: %s", code, e)
                errors += 1

        for code, factor in existing_by_code.items():
            if code not in efdb_by_code:
                factor.write({"active": False})
                archived += 1
                _logger.info("EFDB: archived %s (no longer in EFDB)", code)

        return self._ipcc_notify(
            created=created,
            updated=updated,
            skip_units=skip_units,
            archived=archived,
            errors=errors,
        )

    # ── Fetch ─────────────────────────────────────────────────────────────────

    def _get_ipcc_xls_file(self) -> BytesIO:
        """Download the complete EFDB as XLS bytes.

        The IPCC EFDB website requires a session-based workflow:
          1. Open a session and reset any previous server-side state
          2. Submit a filter form with no filters to load all records
          3. Extract the server-assigned tableName token from the HTML response
          4. Request the XLS export using that tableName token

        A single requests.Session is used throughout so cookies are carried
        automatically between steps.
        """
        session = requests.Session()
        session.headers.update({
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
        })

        try:
            # Step 1 — reset any existing server-side session state
            resp = session.get(
                f"{EFDB_BASE}/find_ef.php",
                params={"reset": ""},
                timeout=(30, 60),
            )
            resp.raise_for_status()

            # Step 2 — submit the search form with no filters to load all records
            resp = session.post(
                f"{EFDB_BASE}/find_ef.php",
                data={"action": "apply_filter", "source_data": "default"},
                timeout=(30, 60),
            )
            resp.raise_for_status()

            # Step 3 — extract the server-assigned tableName from the HTML response
            # The token appears as: <input type="hidden" name="tableName" value="tmp_...">
            match = re.search(
                r'<input[^>]+name=["\']tableName["\'][^>]+value=["\']([^"\']+)["\']',
                resp.text,
                re.IGNORECASE,
            )
            if not match:
                # Try alternate attribute order: value before name
                match = re.search(
                    r'<input[^>]+value=["\']([^"\']+)["\'][^>]+name=["\']tableName["\']',
                    resp.text,
                    re.IGNORECASE,
                )
            if not match:
                raise UserError(_(
                    "Could not retrieve the EFDB session token from the IPCC server. "
                    "The server may be temporarily unavailable — please try again later."
                ))
            table_name = match.group(1).strip()
            _logger.info("EFDB: retrieved session tableName=%s", table_name)

            # Step 4 — request the full XLS export
            resp = session.post(
                f"{EFDB_BASE}/find_ef_xls.php",
                data={
                    "lang_id": 1,
                    "tableName": table_name,
                    "mi_show_fuel": True,
                    "mi_show_cpool": True,
                },
                timeout=(30, 120),
            )
            resp.raise_for_status()

            if not resp.content:
                raise UserError(_(
                    "The IPCC server returned an empty file. "
                    "The database export may be temporarily unavailable — please try again later."
                ))
            return BytesIO(resp.content)
            
        except requests.exceptions.RequestException as e:
            _logger.error("IPCC EFDB connection error: %s", e)
            raise UserError(_(
                "Could not connect to the IPCC EFDB server. "
                "The server may be down, or your internet connection timed out. "
                "Please try again later.\n\n"
                "Technical Details:\n%s"
            ) % str(e))

    # ── Parse ─────────────────────────────────────────────────────────────────

    def _parse_efdb_xls(self, xls_file: BytesIO) -> list[dict]:
        """Read the EFDB XLS using openpyxl and return a list of clean row dicts.

        Rows with no numeric value or a negative value are dropped silently.
        """
        book = openpyxl.load_workbook(filename=xls_file, data_only=True)
        sheet = book.active

        rows_iter = sheet.iter_rows(values_only=True)
        try:
            first_row = next(rows_iter)
        except StopIteration:
            return []

        raw_headers = [(str(col).strip() if col is not None else "") for col in first_row]
        headers = [COLUMN_MAP.get(h, h) for h in raw_headers]

        rows = []
        for row_values in rows_iter:
            raw = {headers[col_idx]: value for col_idx, value in enumerate(row_values) if col_idx < len(headers)}

            row = {}
            for k, v in raw.items():
                if isinstance(v, float) and str(v) in ("nan", ""):
                    row[k] = None
                else:
                    cleaned = str(v).strip() if v is not None else ""
                    row[k] = None if cleaned.upper() in ("", "NAN", "NONE") else cleaned

            try:
                row["value"] = float(str(row.get("value") or "").replace(",", "."))
            except (ValueError, AttributeError):
                continue
            if row["value"] < 0:
                continue

            rows.append(row)

        _logger.info("EFDB: parsed %s valid rows from XLS", f"{len(rows):,}")
        return rows

    # ── Build vals ────────────────────────────────────────────────────────────

    def _build_factor_vals(
        self, row: dict, code: str, uoms: dict, gas_map: dict, source_id=None
    ) -> dict | None:
        """Map one EFDB row dict to enviro.emission.factor create/write vals.

        Returns None for rows that should be skipped (non-physical units).
        """
        unit_raw = (row.get("unit") or "").strip()
        adj_value, uom, conv_note, skip = self._resolve_ipcc_unit(unit_raw, row["value"], uoms)
        if skip:
            return None

        scope, category = self._detect_scope_category(
            row.get("category_2006"), row.get("category_1996")
        )
        gas_raw = (row.get("gas") or "").upper()
        gas_code = GAS_CODE_MAP.get(gas_raw)
        
        raw_region = (row.get("region") or "").strip()
        source = self.env["enviro.data.source"].browse(source_id) if source_id else None
        
        # Format region to ensure the parent continent is properly recorded
        final_region = raw_region
        if source and source.ipcc_region:
            if source.ipcc_region.lower() not in raw_region.lower():
                if raw_region:
                    final_region = f"{source.ipcc_region} - {raw_region}"
                else:
                    final_region = source.ipcc_region

        parts = [
            row.get("fuel_2006") or row.get("fuel_1996") or "",
            (row.get("gas") or "").title(),
        ]
        desc = row.get("description") or ""
        if desc and len(desc) < 60:
            parts.append(desc)
        if final_region:
            parts.append(f"[{final_region}]")
        name = " — ".join(p for p in parts if p) or f"EFDB {row.get('ef_id', '')}"

        note_parts = [
            f"IPCC 2006: {row['category_2006']}" if row.get("category_2006") else "",
            f"IPCC 1996: {row['category_1996']}" if row.get("category_1996") else "",
            f"Parameters: {row['parameters']}" if row.get("parameters") else "",
            f"Source: {row['source_of_data']}" if row.get("source_of_data") else "",
            conv_note,
        ]

        vals = {
            "name":             name[:200],
            "code":             code,
            "scope":            scope,
            "category":         category,
            "calculation_type": "quantity",
            "uom_id":           uom.id,
            "kg_co2e_per_unit": adj_value,
            "source":           f"IPCC EFDB | {row.get('source_of_data', '')}"[:100],
            "region":           final_region or False,
            "notes":            "\n".join(p for p in note_parts if p),
            "active":           True,
            "source_id":        source_id or False,
        }

        if gas_code and gas_map.get(gas_code):
            vals["use_gas_breakdown"] = True
            vals["gas_line_ids"] = [Command.create({
                "gas_id":          gas_map[gas_code],
                "gas_quantity_kg": adj_value,
            })]

        return vals

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _load_ipcc_uoms(self) -> dict:
        """Load all UoMs needed for IPCC unit resolution, creating custom ones if absent.

        In Odoo 19, uom.uom uses a tree structure (relative_uom_id / relative_factor)
        with no category_id or uom_type fields.
        """
        def get_or_create(name):
            uom = self.env["uom.uom"].search([("name", "=", name)], limit=1)
            if not uom:
                uom = self.env["uom.uom"].sudo().create({
                    "name": name,
                    "relative_factor": 1.0,
                })
            return uom

        return {
            "kg":    self.env.ref("uom.product_uom_kgm"),
            "unit":  self.env.ref("uom.product_uom_unit"),
            "m3":    self.env.ref("uom.product_uom_cubic_meter"),
            "tonne": self.env.ref("uom.product_uom_ton"),
            "litre": self.env.ref("uom.product_uom_litre"),
            "kwh":   self.env.ref("uom.product_uom_kwh"),
            "km":    self.env.ref("uom.product_uom_km"),
            "ha":    get_or_create("ha"),
            "lto":   get_or_create("LTO"),
        }

    def _resolve_ipcc_unit(
        self, unit_str: str, value: float, uoms: dict
    ) -> tuple[float, object, str, bool]:
        """Normalize an EFDB unit, converting the emission value to match the resolved UoM.

        Returns (adjusted_value, uom, conversion_note, skip).
        skip=True means the row should be discarded (non-physical unit).

        Conversion values are sourced from the 2006 IPCC Guidelines for National
        Greenhouse Gas Inventories (public domain).
        """
        if not unit_str:
            return value, uoms["kg"], "", False

        unit = unit_str.strip()

        # Non-physical / ratio units — discard the row
        if (unit.startswith("%") or
                unit.lower().startswith("fraction") or
                unit.lower().startswith("year") or
                unit in _SKIP_UNIT_EXACT):
            return value, None, "", True

        # Gram → convert to kg
        if unit.startswith("g"):
            return value / 1000, uoms["kg"], f"Unit converted to kg: {unit}", False

        # Kilogram variants → kg (no conversion needed)
        if unit.lower().startswith("kg"):
            return value, uoms["kg"], "", False

        # Terajoule → kg  (IPCC often expresses GHG per TJ of energy)
        if unit.startswith("TJ"):
            return value * 1.11e-5, uoms["kg"], f"Unit converted to kg: {unit}", False

        # Gigagram → kg
        if unit.lower().startswith("gg"):
            return value * (10 ** 9), uoms["kg"], f"Unit converted to kg: {unit}", False

        # Tonne / compound tonne units
        if unit.lower().startswith("ton") or unit in _TONNE_COMPOUND_UNITS:
            return value, uoms["tonne"], "", False

        # Special compound m3 units with density conversion
        if unit == "m3/m3 beer":
            return value * 1.020, uoms["m3"], f"Unit converted to m3: {unit}", False
        if unit == "m3/m3 ethanol":
            return value * 789, uoms["m3"], f"Unit converted to m3: {unit}", False

        # Livestock head count
        if unit == "kg CH4/head/yr":
            return value, uoms["unit"], "", False

        # Biomass per hectare
        if unit == "t dm/ha":
            return value * 1000, uoms["ha"], f"Unit converted to kg/ha: {unit}", False

        # Landing and takeoff cycle
        if unit == "kg/LTO":
            return value, uoms["lto"], "", False

        # Other well-known simple units
        if unit.lower() in ("l", "litre", "liter"):
            return value, uoms["litre"], "", False
        if unit.lower().startswith("kwh"):
            return value, uoms["kwh"], "", False
        if unit.lower().startswith("km"):
            return value, uoms["km"], "", False
        if unit.lower() in ("t",) or unit.lower().startswith("t/") or unit.lower().startswith("t "):
            return value, uoms["tonne"], "", False

        # Fallback: store in kg, note the original unit for traceability
        _logger.debug("EFDB: unrecognized unit '%s' — defaulting to kg", unit)
        return value, uoms["kg"], f"Original unit: {unit} (defaulted to kg)", False

    def _ipcc_notify(
        self,
        created: int = 0,
        updated: int = 0,
        archived: int = 0,
        skipped_existing: int = 0,
        skip_units: "dict[str, int] | None" = None,
        errors: int = 0,
    ) -> dict:
        skip_units = skip_units or {}
        skipped_unit = sum(skip_units.values())
        skipped_total = skipped_existing + skipped_unit

        parts = [_("Created: %(n)d", n=created)]
        if updated:
            parts.append(_("Updated: %(n)d", n=updated))
        if archived:
            parts.append(_("Archived: %(n)d", n=archived))
        if errors:
            parts.append(_("Errors: %(n)d", n=errors))
        message = "  |  ".join(parts)

        # Log a breakdown so operators can see why rows were skipped
        skip_lines = []
        if skipped_existing:
            skip_lines.append(f"  already in DB: {skipped_existing}")
        if skip_units:
            skip_lines.append(f"  non-physical unit ({skipped_unit} rows):")
            for unit, count in sorted(skip_units.items(), key=lambda x: -x[1]):
                skip_lines.append(f"    {count:>5}x  {unit!r}")
        if skip_lines:
            _logger.info("EFDB skipped rows breakdown:\n%s", "\n".join(skip_lines))

        _logger.info("EFDB sync complete: %s", message)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success" if not errors else "warning",
                "title": _("IPCC Sync Complete"),
                "message": message,
                "sticky": True,
            },
        }

    @staticmethod
    def _detect_scope_category(
        category_2006: Optional[str], category_1996: Optional[str]
    ) -> tuple[str, str]:
        text = str(category_2006 or category_1996 or "").strip().upper()
        for prefix, scope, category in sorted(CATEGORY_MAP, key=lambda x: len(x[0]), reverse=True):
            if text.startswith(prefix):
                return scope, category
        return "scope3", "other"
