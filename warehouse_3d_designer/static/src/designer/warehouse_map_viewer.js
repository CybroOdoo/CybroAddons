/** @odoo-module **/

import { registry } from "@web/core/registry";
import { WarehouseDesigner } from "./warehouse_designer";

/**
 * Read-only Warehouse Map Viewer.
 *
 * Reuses the full WarehouseDesigner component but forces isAdmin = false,
 * which hides all editing controls (save, export/import, drag-drop placement,
 * shape/rotation editing, decorations panel, keyboard shortcuts, etc.).
 */
export class WarehouseMapViewer extends WarehouseDesigner {
    async _checkPermissions() {
        this.state.isAdmin = false;
    }
}

registry.category("actions").add("warehouse_map_viewer", WarehouseMapViewer);
