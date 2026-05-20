# ─────────────────────────────────────────────────────────────────────────────
# Ignition Script: Gateway Startup Script
# Location in Ignition: Gateway > Gateway Event Scripts > Gateway > Startup
#
# HOW TO CONFIGURE:
#   1. Ignition Designer > Gateway Event Scripts > Gateway tab.
#   2. Paste this script in the "Startup" section.
#
# WHAT IT DOES:
#   1. Verifies connectivity to Odoo.
#   2. Reads all registered tag paths from Odoo.
#   3. Writes them to a memory tag so other scripts can read the list.
#   4. Sets an "OdooConnected" status tag that the HMI status bar can show.
# ─────────────────────────────────────────────────────────────────────────────

import OdooClient
import system.tag


# Memory tags this script writes to — create these in the [default] provider
STATUS_TAG     = "[default]_Odoo/Connected"           # Boolean
TAG_COUNT_TAG  = "[default]_Odoo/RegisteredTagCount"  # Integer
LAST_SYNC_TAG  = "[default]_Odoo/LastSyncTime"        # DateTime
ERROR_MSG_TAG  = "[default]_Odoo/LastError"           # String


def on_startup():
    logger = system.util.getLogger("OdooScadaStartup")
    logger.info("Odoo SCADA integration starting…")

    # 1. Health check
    connected = OdooClient.health_check()
    system.tag.writeBlocking([STATUS_TAG], [connected])

    if not connected:
        msg = "Odoo unreachable on startup. Batch sync will retry every 60s."
        logger.warn(msg)
        system.tag.writeBlocking([ERROR_MSG_TAG], [msg])
        return

    # 2. Load registered tags
    try:
        tags = OdooClient.get_registered_tags()
        count = len(tags)
        system.tag.writeBlocking([TAG_COUNT_TAG], [count])
        system.tag.writeBlocking([ERROR_MSG_TAG], [""])
        logger.infof("Connected to Odoo. %d SCADA tags registered.", count)

        # Log each tag for operator awareness
        for t in tags:
            logger.infof("  Tag: %-45s → %s.%s (equip: %s)",
                         t.get("tag_path", ""),
                         t.get("odoo_model", ""),
                         t.get("odoo_field", "—"),
                         t.get("equipment_name", "—"))

    except Exception as e:
        logger.errorf("Failed to load tag registry: %s", str(e))
        system.tag.writeBlocking([ERROR_MSG_TAG], [str(e)])

    # 3. Update last sync time
    system.tag.writeBlocking([LAST_SYNC_TAG], [system.date.now()])
