# ─────────────────────────────────────────────────────────────────────────────
# Ignition Script: Perspective HMI Data Bindings  (v2 — full SAP IS-Oil flow)
# Location: Project > Scripting > Project Library > ScadaHMI
#
# All functions return plain Python lists/dicts suitable for Perspective
# Table, Chart, and Label component bindings (Script transform).
# ─────────────────────────────────────────────────────────────────────────────

import OdooClient


# ── 1. Tank farm overview ──────────────────────────────────────────────────────

def get_tank_farm():
    """
    Returns live tank inventory for a tank-farm overview dashboard.
    Bind to a Perspective Table or custom SVG tank-farm graphic.

    Each row: { id, name, product_type, fill_percent, gross_volume_bbl,
                net_standard_volume_bbl, ullage_bbl, last_scada_sync }
    """
    return OdooClient.get_tank_levels()


def get_tank_fill_percent(tank_id):
    """
    Returns a single float (0–100) for a Perspective circular gauge component.
    Bind to gauge value property with Script transform:
        return ScadaHMI.get_tank_fill_percent(42)
    """
    tanks = OdooClient.get_tank_levels()
    for t in tanks:
        if t["id"] == tank_id:
            return t["fill_percent"]
    return 0.0



# ── 3. Production trending ─────────────────────────────────────────────────────

def get_production_trend(days=14):
    """
    Returns daily oil/gas production for the last N days.
    Use as data source for a Perspective Chart (line/bar).

    Format: [{ date, well, oil_bbl, gas_mcf, water_bbl, gor, water_cut }, ...]
    """
    return OdooClient.get_daily_production(limit=days * 10)


def get_production_summary_today():
    """
    Returns summed production for today across all confirmed wells.
    Use in large-number dashboard widgets (digital display / stat card).
    """
    reports = OdooClient.get_daily_production(limit=50)
    from system.date import format as fmt_date
    today = fmt_date(system.date.now(), "yyyy-MM-dd")
    today_reports = [r for r in reports if r.get("report_date") == today]
    total_oil  = sum(r.get("oil_volume_bbl", 0)  for r in today_reports)
    total_gas  = sum(r.get("gas_volume_mcf", 0)  for r in today_reports)
    total_water = sum(r.get("water_volume_bbl", 0) for r in today_reports)
    return {
        "oil_bbl":   round(total_oil, 1),
        "gas_mcf":   round(total_gas, 1),
        "water_bbl": round(total_water, 1),
        "wells":     len(today_reports),
    }


# ── 4. HSE & safety ticker ─────────────────────────────────────────────────────

def get_recent_hse_incidents(limit=10):
    """Recent HSE incidents for a safety ticker on the control-room main screen."""
    records = OdooClient.search_read(
        model="oil.hse.incident",
        domain=[],
        fields=["name", "incident_type", "severity", "incident_date", "equipment_id", "state"],
        limit=limit,
    )
    return [{
        "id":        r["id"],
        "ref":       r["name"],
        "type":      r.get("incident_type", ""),
        "severity":  r.get("severity", ""),
        "date":      str(r.get("incident_date", "")),
        "equipment": r["equipment_id"][1] if r["equipment_id"] else "—",
        "state":     r.get("state", ""),
    } for r in records]


def get_open_permits():
    """Active permits to work — show on field HMI and safety board."""
    records = OdooClient.search_read(
        model="oil.hse.permit",
        domain=[["state", "in", ["approved", "in_progress"]]],
        fields=["name", "permit_type", "equipment_id", "valid_until", "responsible_id"],
        limit=20,
    )
    return [{
        "id":          r["id"],
        "permit":      r["name"],
        "type":        r.get("permit_type", ""),
        "equipment":   r["equipment_id"][1] if r["equipment_id"] else "—",
        "valid_until": str(r.get("valid_until", "")),
        "responsible": r["responsible_id"][1] if r["responsible_id"] else "—",
    } for r in records]



# ── 6. Maintenance & pipeline ──────────────────────────────────────────────────

def get_open_maintenance_requests(equipment_id=None):
    """Open maintenance requests for a maintenance-board display."""
    domain = [["state", "in", ["new", "in_progress", "under_repair"]]]
    if equipment_id:
        domain.append(["equipment_id", "=", equipment_id])
    records = OdooClient.search_read(
        model="maintenance.request",
        domain=domain,
        fields=["name", "equipment_id", "maintenance_type", "schedule_date", "stage_id"],
        limit=50,
    )
    return [{
        "id":        r["id"],
        "ref":       r["name"],
        "equipment": r["equipment_id"][1] if r["equipment_id"] else "—",
        "type":      r.get("maintenance_type", ""),
        "scheduled": str(r.get("schedule_date") or "—"),
        "stage":     r["stage_id"][1] if r["stage_id"] else "—",
    } for r in records]


def get_active_pipeline_transfers():
    """Active pipeline transfers for the pipeline schematic HMI."""
    records = OdooClient.search_read(
        model="stock.picking",
        domain=[["is_pipeline_transfer", "=", True],
                ["state", "in", ["confirmed", "assigned", "waiting"]]],
        fields=["name", "carrier_id", "pipeline_delivery_start",
                "pipeline_delivery_end", "state"],
        limit=20,
    )
    return [{
        "id":       r["id"],
        "transfer": r["name"],
        "pipeline": r["carrier_id"][1] if r["carrier_id"] else "—",
        "start":    str(r.get("pipeline_delivery_start") or "—"),
        "end":      str(r.get("pipeline_delivery_end") or "—"),
        "state":    r["state"],
    } for r in records]


# ── 7. Write-back helpers (called from Perspective buttons / valve events) ─────

def on_valve_open(picking_id):
    """Stamp pipeline_delivery_start when valve-open event fires."""
    OdooClient.record_pipeline_start(picking_id)

def on_valve_close(picking_id):
    """Stamp pipeline_delivery_end when valve-close event fires."""
    OdooClient.record_pipeline_end(picking_id)

