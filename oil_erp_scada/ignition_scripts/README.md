# Oil ERP SCADA Integration — Setup Guide

## What this module does

`oil_erp_scada` is a new Odoo module inside your project that:

- Exposes three REST endpoints (`/api/scada/push`, `/api/scada/tags`, `/api/scada/equipment`) for Ignition to call
- Stores every incoming sensor reading in a time-series log (`scada.reading`)
- Automatically writes live values back to `maintenance.equipment`, `oil.reservoir` fields
- Evaluates configurable alert rules and auto-creates HSE incidents or maintenance requests when thresholds are breached
- Provides five ready-to-use Ignition Python scripts

---

## Step 1 — Install the Odoo module

1. Copy the `oil_erp_scada/` folder into your Odoo addons path alongside the other `oil_erp_*` modules.
2. Restart the Odoo service.
3. Go to **Settings > Activate Developer Mode**.
4. Go to **Apps > Update Apps List**, then search for "SCADA" and install **Oil & Gas SCADA Integration**.

---

## Step 2 — Set the API key in Odoo

1. Go to **Settings > Technical > Parameters > System Parameters**.
2. Create a new parameter:
   - Key: `oil_erp_scada.api_key`
   - Value: a strong random string, e.g. `oilscada-a8f3c921e74b6d05`
3. Save.

This same key goes into `OdooClient.py` in Ignition (see Step 4).

---

## Step 3 — Register your SCADA tags in Odoo

1. Go to **SCADA Integration > Tag Registry > New**.
2. For each sensor channel, fill in:

| Field | Example |
|-------|---------|
| Tag Name | Well-1 Wellhead Pressure |
| Ignition Tag Path | `[default]Well1/Pressure/PSI` |
| Tag Type | Pressure |
| Unit | PSI |
| Target Odoo Model | Equipment |
| Target Field | `operating_pressure` |
| Equipment | (select your equipment record) |

3. Add alert thresholds under the **Alert Thresholds** tab on each tag form.

### Typical tags to register

```
[default]Well1/Pressure/PSI      → maintenance.equipment  operating_pressure
[default]Well1/Temp/F            → maintenance.equipment  operating_temperature
[default]Well1/H2S/PPM           → none (log only — threshold creates HSE incident)
[default]Well1/FlowRate/BBLHR    → none (log only)
[default]Reservoir1/Pressure/PSI → oil.reservoir          live_reservoir_pressure
[default]Reservoir1/GOR          → oil.reservoir          live_gor
[default]Reservoir1/WaterCut     → oil.reservoir          live_water_cut
```

---

## Step 4 — Configure Ignition

### 4a. Copy the project library

1. In Ignition Designer, go to **Project > Scripting > Project Library**.
2. Create a new script module named `OdooClient`.
3. Paste the contents of `ignition_scripts/OdooClient.py`.
4. Update the two constants at the top:
   ```python
   ODOO_BASE_URL = "http://your-odoo-server:8069"
   SCADA_API_KEY  = "oilscada-a8f3c921e74b6d05"   # must match Step 2
   ```

### 4b. Tag Change Event (per sensor tag)

1. In the Tag Browser, right-click a tag → **Edit Tag > Tag Events > Value Changed**.
2. Enable the Script checkbox.
3. Paste the contents of `ignition_scripts/tag_change_handler.py`.
4. The tag path is automatically available as `tagPath`.

> **Tip**: For bulk setup, use Ignition's UDT (User Defined Type). Create one UDT with the tag change script, then instantiate it for each well/equipment.

### 4c. Scheduled Batch Sync (60-second timer)

1. Go to **Gateway Event Scripts > Timer > New Script**.
2. Set: Fixed Delay, 60 seconds, Enabled.
3. Paste `ignition_scripts/scheduled_batch_sync.py`.
4. In the timer body, call: `batch_sync()`

### 4d. Gateway Startup Script

1. Go to **Gateway Event Scripts > Gateway > Startup**.
2. Paste `ignition_scripts/gateway_startup.py`.
3. Create the following memory tags in the `[default]` provider:
   - `_Odoo/Connected` — Boolean
   - `_Odoo/RegisteredTagCount` — Integer
   - `_Odoo/LastSyncTime` — DateTime
   - `_Odoo/LastError` — String

### 4e. HMI Data Bindings (Perspective)

1. Go to **Project > Scripting > Project Library**.
2. Create a new module named `ScadaHMI`.
3. Paste `ignition_scripts/hmi_data_bindings.py`.
4. In any Perspective component binding, use Script transform:
   ```python
   return ScadaHMI.get_open_maintenance_requests()
   ```

---

## Step 5 — Test the integration

### Quick connectivity test (from Ignition Script Console)

```python
import OdooClient
print OdooClient.health_check()
# Expected: True
```

### Push a test reading

```python
import OdooClient
result = OdooClient.push_readings([{
    "tag_path": "[default]Well1/Pressure/PSI",
    "value": 2450.0,
    "quality": "good",
}])
print result
# Expected: {u'status': u'ok', u'processed': 1, u'skipped': 0, u'errors': []}
```

### Verify in Odoo

1. Go to **SCADA Integration > Readings Log**.
2. You should see the reading row with timestamp and value.
3. Go to the linked Equipment record — the **Live Pressure (PSI)** field should show `2450.0`.

---

## Data flow summary

```
Field Sensor
    │  (OPC-UA / Modbus)
    ▼
PLC / RTU
    │  (OPC-UA tags)
    ▼
Ignition Gateway
    ├─ tag_change_handler.py   ← fires immediately on value change
    └─ scheduled_batch_sync.py ← catches any missed readings every 60s
         │
         │  POST /api/scada/push  (JSON, API key)
         ▼
Odoo REST Controller (scada_api.py)
    │
    ├─ scada.tag.process_reading()
    │      ├─ Creates scada.reading (time-series log)
    │      ├─ Writes value to equipment/reservoir field
    │      └─ Evaluates thresholds
    │              ├─ Creates oil.hse.incident  (if gas/pressure alarm)
    │              └─ Creates maintenance.request (if equipment fault)
    │
    └─ Returns { status, processed, skipped, errors }
```

---

## Troubleshooting

| Problem | Check |
|---------|-------|
| `health_check()` returns False | Odoo service running? Firewall blocking port 8069? |
| `push_readings` returns `skipped: 1` | Tag path not registered in SCADA Integration > Tag Registry |
| `Unauthorized` error | API key in `OdooClient.py` doesn't match `oil_erp_scada.api_key` system parameter |
| Values not updating equipment record | Confirm `odoo_field` is set on the tag and equipment is linked |
| HSE incident not auto-created | Check threshold `active` flag and `cooldown_minutes` — may be in cooldown |
| View errors on equipment form | Confirm `oil_erp_equipment` view has `name="button_box"` — check `inherit_id` |
