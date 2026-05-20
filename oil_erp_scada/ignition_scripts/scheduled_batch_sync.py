# ─────────────────────────────────────────────────────────────────────────────
# Ignition Script: Scheduled Batch Sync (Gateway Timer Event)
# Location in Ignition: Gateway > Gateway Event Scripts > Timer > Add Script
#
# HOW TO CONFIGURE:
#   1. Ignition Designer > Gateway Event Scripts > Timer tab > New Script.
#   2. Set execution rate: Fixed Delay, 60 seconds.
#   3. Paste this entire script (or call batch_sync() from the timer body).
#
# PURPOSE:
#   The tag_change_handler fires per individual tag change — great for
#   real-time push.  This script runs every 60 seconds as a safety net:
#   it reads ALL registered tags at once and pushes them in a single
#   HTTP request.  Catches any readings that were missed due to deadband
#   filtering, gateway restarts, or network blips.
# ─────────────────────────────────────────────────────────────────────────────

import OdooClient
import system.tag
import system.date

# ── Which tags to include in the batch ───────────────────────────────────────
# Option A (recommended): fetch the list dynamically from Odoo at startup.
# Option B: hard-code the paths below for simpler setups.

# Cache of registered tag paths fetched from Odoo on first run
_TAG_CACHE = []
_CACHE_TS  = None
CACHE_TTL_MINUTES = 15   # refresh the tag list every 15 minutes


def batch_sync():
    """
    Main entry point — called by the Ignition Gateway Timer every 60 seconds.
    Reads current values for all registered tags, then pushes in one batch.
    """
    logger = system.util.getLogger("OdooScadaBatch")

    # 1. Refresh tag list from Odoo if cache is stale
    tag_paths = _get_tag_paths(logger)
    if not tag_paths:
        logger.warn("No tag paths to sync — check Odoo tag registry.")
        return

    # 2. Read all tag values from Ignition in one call
    qualified_values = system.tag.readBlocking(tag_paths)

    # 3. Build payload
    readings = []
    ts_str = _now_iso()
    for path, qv in zip(tag_paths, qualified_values):
        quality = _map_quality(qv.quality)
        try:
            value = float(qv.value) if qv.value is not None else 0.0
        except (TypeError, ValueError):
            value = 0.0
        readings.append({
            "tag_path": path,
            "value":    value,
            "quality":  quality,
            "timestamp": ts_str,
        })

    if not readings:
        return

    # 4. Push to Odoo
    try:
        result = OdooClient.push_readings(readings)
        logger.infof(
            "Batch sync: pushed=%d  skipped=%d  errors=%s",
            result.get("processed", 0),
            result.get("skipped", 0),
            str(result.get("errors", [])),
        )
    except Exception as e:
        logger.errorf("Batch sync failed: %s", str(e))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_tag_paths(logger):
    """
    Return list of Ignition tag paths, refreshing from Odoo every CACHE_TTL_MINUTES.
    Falls back to stale cache on network error.
    """
    global _TAG_CACHE, _CACHE_TS

    now = system.date.now()
    cache_expired = (
        _CACHE_TS is None or
        system.date.minutesBetween(_CACHE_TS, now) >= CACHE_TTL_MINUTES
    )

    if cache_expired:
        try:
            tags = OdooClient.get_registered_tags()
            _TAG_CACHE = [t["tag_path"] for t in tags if t.get("tag_path")]
            _CACHE_TS  = now
            logger.infof("Refreshed tag registry: %d tags loaded.", len(_TAG_CACHE))
        except Exception as e:
            logger.warnf("Could not refresh tag registry from Odoo (%s). Using cache.", str(e))

    return _TAG_CACHE


def _map_quality(ignition_quality):
    code = str(ignition_quality).lower()
    if "good" in code:
        return "good"
    elif "bad" in code or "error" in code:
        return "bad"
    return "uncertain"


def _now_iso():
    """Return current UTC time as ISO-8601 string."""
    try:
        from java.text import SimpleDateFormat
        from java.util import TimeZone
        fmt = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss")
        fmt.setTimeZone(TimeZone.getTimeZone("UTC"))
        return fmt.format(system.date.now())
    except Exception:
        return None
