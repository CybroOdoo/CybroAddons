# ─────────────────────────────────────────────────────────────────────────────
# Ignition Script: Tag Change Event Handler
# Location in Ignition: Project > Tags > right-click any tag > Tag Events > Value Changed
#
# HOW TO ATTACH:
#   1. In Ignition Designer, open the Tag Browser.
#   2. Right-click the tag (e.g. [default]Well1/Pressure/PSI).
#   3. Edit Tag > Tag Events > Value Changed > tick "Script".
#   4. Paste this script (or call the function from here).
#
# The `currentValue` and `previousValue` objects are injected by Ignition.
# ─────────────────────────────────────────────────────────────────────────────

# Import the shared Odoo client library
import OdooClient

# ── Deadband: minimum change required before we bother pushing ───────────────
# Prevents flooding Odoo with insignificant fluctuations.
PRESSURE_DEADBAND    = 5.0    # PSI  — only push if value changed by >= 5
TEMPERATURE_DEADBAND = 0.5    # °F   — only push if value changed by >= 0.5
DEFAULT_DEADBAND     = 0.01   # generic tags

DEADBAND_MAP = {
    "pressure":    PRESSURE_DEADBAND,
    "temperature": TEMPERATURE_DEADBAND,
    "flow_rate":   1.0,
    "gas_ppm":     0.5,
}


def on_value_changed(tagPath, previousValue, currentValue, initialChange, missedEvents):
    """
    Called by Ignition whenever a subscribed tag's value changes.

    Parameters (injected by Ignition runtime)
    -----------------------------------------
    tagPath      : str   – full tag path, e.g. "[default]Well1/Pressure/PSI"
    previousValue: QualifiedValue
    currentValue : QualifiedValue  (.value, .quality, .timestamp)
    initialChange: bool  – True on first scan after gateway start
    missedEvents : int   – number of missed change events (0 = none missed)
    """
    # Skip the very first scan after a gateway restart
    if initialChange:
        return

    new_val  = currentValue.value
    prev_val = previousValue.value if previousValue else None

    # Map Ignition quality codes → OPC-UA quality string
    quality = _map_quality(currentValue.quality)

    # Deadband check — skip if change is below threshold
    if prev_val is not None and quality == "good":
        deadband = _get_deadband(tagPath)
        if abs(new_val - prev_val) < deadband:
            return

    # Format timestamp as ISO-8601 string
    ts = _format_ts(currentValue.timestamp)

    # Push to Odoo
    try:
        result = OdooClient.push_readings([{
            "tag_path": tagPath,
            "value":    new_val,
            "quality":  quality,
            "timestamp": ts,
        }])
        if result.get("skipped", 0) > 0:
            system.util.getLogger("OdooScada").warnf(
                "Tag not registered in Odoo: %s", tagPath)
    except Exception as e:
        system.util.getLogger("OdooScada").errorf(
            "Failed to push reading for %s: %s", tagPath, str(e))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _map_quality(ignition_quality):
    """Convert Ignition QualityCode to OPC-UA quality string."""
    code = str(ignition_quality).lower()
    if "good" in code:
        return "good"
    elif "bad" in code or "error" in code or "not_connected" in code:
        return "bad"
    else:
        return "uncertain"


def _get_deadband(tag_path):
    """Infer deadband from tag path keywords."""
    path_lower = tag_path.lower()
    for key, band in DEADBAND_MAP.items():
        if key in path_lower:
            return band
    return DEFAULT_DEADBAND


def _format_ts(java_date):
    """Convert a Java Date object (from Ignition) to ISO-8601 string."""
    try:
        from java.text import SimpleDateFormat
        from java.util import TimeZone
        fmt = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss")
        fmt.setTimeZone(TimeZone.getTimeZone("UTC"))
        return fmt.format(java_date)
    except Exception:
        return None
