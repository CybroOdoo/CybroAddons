# ─────────────────────────────────────────────────────────────────────────────
# Ignition Project Library: OdooClient  (v2 — SAP IS-Oil flow edition)
# Path: Project > Scripting > Project Library > OdooClient
#
# Complete HTTP client for the Oil ERP SCADA integration.
# ALL other Ignition scripts import from here.
# Only edit ODOO_BASE_URL and SCADA_API_KEY when your server changes.
# ─────────────────────────────────────────────────────────────────────────────

import system.net
import json

# ── Configuration ── ONLY EDIT THESE 3 LINES ─────────────────────────────────
ODOO_BASE_URL = "http://localhost:****"
SCADA_API_KEY = "api_key"
ODOO_DB       = "db_name"
# ─────────────────────────────────────────────────────────────────────────────

TIMEOUT_MS = 10000

def _headers():
    return {
        "X-SCADA-API-Key": SCADA_API_KEY,
        "X-Odoo-Database": ODOO_DB
    }

def _post(path, payload):
    url  = ODOO_BASE_URL + path
    body = json.dumps(payload)
    try:
        raw = system.net.httpPost(
            url=url,
            contentType="application/json",
            postData=body,
            timeout=TIMEOUT_MS,
            headerValues=_headers()
        )
    except Exception as e:
        raise RuntimeError("POST %s failed: %s" % (url, e))
    data = json.loads(raw)
    if isinstance(data, dict) and data.get("status") == "error":
        raise RuntimeError("Odoo error: %s" % data.get("message", ""))
    return data

def _get(path):
    url = ODOO_BASE_URL + path
    try:
        raw = system.net.httpGet(
            url=url,
            timeout=TIMEOUT_MS,
            headerValues=_headers()
        )
    except Exception as e:
        raise RuntimeError("GET %s failed: %s" % (url, e))
    return json.loads(raw)

# ── Health ────────────────────────────────────────────────────────────────────

def health_check():
    try:
        return _get("/api/scada/health").get("status") == "ok"
    except Exception:
        return False

# ── Push readings ─────────────────────────────────────────────────────────────

def push_readings(readings):
    """
    Push sensor readings to Odoo in one batch call.

    readings: list of dicts with keys:
        tag_path         (str)   – Ignition path registered in Odoo tag registry
        value            (float) – sensor value
        quality          (str)   – 'good'|'bad'|'uncertain'  (optional, default 'good')
        timestamp        (str)   – ISO-8601 UTC string        (optional)
        measurement_type (str)   – REQUIRED for Multi-M easurement Device tags.
                                   One of: 'pressure', 'temperature', 'flow_rate',
                                   'level', 'gas_ppm', 'vibration', 'valve_position',
                                   'cumulative', 'other'.
                                   Ignored for single-measurement tags.

    Returns: { status, processed, skipped, errors }

    Server-side routing (scada_tag._dispatch):
      - level       → project.storage_location_id.receive_level() (when target is project)
      - cumulative  → oil.meter.receive_scada_volume(delta)
      - pressure    → equipment/reservoir live_pressure
      - temperature → equipment live_temperature (or project storage_location current_temperature_f)
      - gas_ppm     → threshold evaluation (auto HSE incident)
    """
    return _post("/api/scada/push", {
        "api_key":  SCADA_API_KEY,
        "readings": readings
    })


def push_multi_readings(tag_path, measurements, quality="good", timestamp=None):
    """
    Push multiple measurements for ONE Multi-Measurement Device tag in one call.

    Use this when you have a tag registered in Odoo with multiple measurement toggles
    (one tag per physical device) and want to send several sensor values at once.

    :param str tag_path:      Device tag path registered in Odoo.
                              e.g. "[AlphaField]Wells/A1"
    :param dict measurements: Mapping of measurement_type → float value.
                              e.g. {"pressure": 2450.0, "temperature": 185.3,
                                    "gas_ppm": 5.2, "flow_rate": 120.5}
    :param str quality:       OPC-UA quality applied to ALL measurements.
                              'good' | 'bad' | 'uncertain'  (default 'good')
    :param str timestamp:     Optional ISO-8601 UTC string applied to ALL readings.

    Returns: { status, processed, skipped, errors }

    Example:
        result = OdooClient.push_multi_readings(
            "[AlphaField]Wells/A1",
            {
                "pressure":    2450.0,
                "temperature":  185.3,
                "flow_rate":    120.5,
                "gas_ppm":        5.2,
            }
        )
        if result.get("errors"):
            system.util.getLogger("OdooScada").errorf("Errors: %s", str(result["errors"]))
    """
    readings = []
    for mtype, val in measurements.items():
        item = {
            "tag_path":         tag_path,
            "measurement_type": mtype,
            "value":            float(val),
            "quality":          quality,
        }
        if timestamp:
            item["timestamp"] = timestamp
        readings.append(item)
    return push_readings(readings)


def push_readings_with_logging(readings, logger=None):
    if logger is None:
        import system.util
        logger = system.util.getLogger("OdooScada")
    try:
        result = push_readings(readings)
        logger.infof("SCADA push: processed=%d skipped=%d",
                     result.get("processed", 0),
                     result.get("skipped", 0))
        for err in result.get("errors", []):
            if isinstance(err, dict) and err.get("reason") == "not_registered":
                logger.warnf("NOT REGISTERED: %s", err.get("tag_path", ""))
            else:
                logger.errorf("ERROR: %s", str(err))
        return result
    except Exception as e:
        logger.errorf("push_readings failed: %s", str(e))
        return {"status": "error", "message": str(e),
                "processed": 0, "skipped": len(readings)}


def push_multi_readings_with_logging(tag_path, measurements, quality="good",
                                     timestamp=None, logger=None):
    """
    Same as push_multi_readings() but logs results automatically.
    Convenience wrapper for use in tag-change handlers.
    """
    if logger is None:
        import system.util
        logger = system.util.getLogger("OdooScada")
    try:
        result = push_multi_readings(tag_path, measurements, quality=quality,
                                     timestamp=timestamp)
        logger.infof("Multi-push [%s]: processed=%d skipped=%d",
                     tag_path,
                     result.get("processed", 0),
                     result.get("skipped", 0))
        for err in result.get("errors", []):
            logger.errorf("ERROR [%s]: %s", tag_path, str(err))
        return result
    except Exception as e:
        logger.errorf("push_multi_readings failed [%s]: %s", tag_path, str(e))
        return {"status": "error", "message": str(e),
                "processed": 0, "skipped": len(measurements)}

# ── Live-enabled guard ────────────────────────────────────────────────────────

def check_live_enabled():
    try:
        result = _rpc(
            "ir.config_parameter",
            "get_param",
            ["oil_erp_scada.live_enabled"],
            {"default": "1"}
        )
        return str(result).strip() == "1"
    except Exception:
        return True

# ── GET endpoints (HMI display data) ─────────────────────────────────────────

def get_registered_tags():
    try:
        return _get("/api/scada/tags").get("tags", [])
    except Exception:
        return []

def get_equipment_list():
    try:
        return _get("/api/scada/equipment").get("equipment", [])
    except Exception:
        return []

def get_tank_levels():
    try:
        return _get("/api/scada/tanks").get("tanks", [])
    except Exception:
        return []



def get_daily_production(limit=50):
    try:
        return _get("/api/scada/production/daily").get("reports", [])
    except Exception:
        return []

# ── Odoo JSON-RPC (direct model access) ──────────────────────────────────────

def _rpc(model, method, args, kwargs=None):
    if kwargs is None:
        kwargs = {}
    payload = {
        "jsonrpc": "2.0", "method": "call", "id": 1,
        "params": {
            "model":  model,
            "method": method,
            "args":   args,
            "kwargs": kwargs
        }
    }
    raw = system.net.httpPost(
        url=ODOO_BASE_URL + "/web/dataset/call_kw",
        contentType="application/json",
        postData=json.dumps(payload),
        timeout=TIMEOUT_MS,
        headerValues=_headers()
    )
    data = json.loads(raw)
    if "error" in data:
        raise RuntimeError("Odoo RPC error: %s" % data["error"])
    return data.get("result")

def search_read(model, domain, fields, limit=100):
    return _rpc(model, "search_read", [domain],
                {"fields": fields, "limit": limit})

def write_record(model, record_id, values):
    return _rpc(model, "write", [[record_id], values])

def create_record(model, values):
    return _rpc(model, "create", [values])

# ── Pipeline transfer helpers ─────────────────────────────────────────────────

def record_pipeline_start(picking_id):
    write_record("stock.picking", picking_id,
                 {"pipeline_delivery_start": _now_odoo()})

def record_pipeline_end(picking_id):
    write_record("stock.picking", picking_id,
                 {"pipeline_delivery_end": _now_odoo()})



# ── Internal time helpers ─────────────────────────────────────────────────────

def _now_odoo():
    from java.text import SimpleDateFormat
    from java.util import TimeZone
    fmt = SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
    fmt.setTimeZone(TimeZone.getTimeZone("UTC"))
    return fmt.format(system.date.now())

def _now_iso():
    from java.text import SimpleDateFormat
    from java.util import TimeZone
    fmt = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss")
    fmt.setTimeZone(TimeZone.getTimeZone("UTC"))
    return fmt.format(system.date.now())
