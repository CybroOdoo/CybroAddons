/** @odoo-module **/

/**
 * Warehouse Designer — Main OWL component for the interactive warehouse
 * layout designer. Manages layout loading, location placement, heatmap
 * toggling, product search, import/export, and multi-floor navigation.
 */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { Component, onWillStart, useState, useEffect } from "@odoo/owl";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { jsonrpc } from "@web/core/network/rpc_service";

import { WarehouseCanvas } from "./warehouse_canvas";
import { WarehouseToolbar } from "./warehouse_toolbar";
import { WarehouseSidebar } from "./warehouse_sidebar";
import { Warehouse3DView } from "./warehouse_3d_view";

export class WarehouseDesigner extends Component {
    static template = "warehouse_3d_designer.WarehouseDesigner";
    static components = { ControlPanel, WarehouseCanvas, WarehouseToolbar, WarehouseSidebar, Warehouse3DView };
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.user = useService("user");

        // Fast O(1) location lookup by ID
        this._locIndex = new Map();

        this.state = useState({
            layouts: [],
            selectedLayoutId: null,
            layoutData: null,
            locations: [],
            unplacedLocations: [],
            selectedLocationId: null,
            selectedLocationData: null,
            heatmapEnabled: false,
            heatmapData: {},
            gridEnabled: true,
            zoomLevel: 1.0,
            isDirty: false,
            isLoading: true,
            viewMode: '2d',
            isAdmin: false,
            productSearchQuery: '',
            productSearchResults: [],
            highlightedLocationId: null,
            mapObjects: [],
            selectedMapObjectId: null,
            removedMapObjectIds: [],
            removedLocationIds: [],
            measurementUnit: 'm',
            cellSizeCm: 100,
            siblingFloors: [],
            showAllFloors3D: false,
            allFloorData: null,
            focusMode: false,
            hideOverlays: false,
            showShortcuts: false,
        });

        onWillStart(async () => {
            await this._checkPermissions();
            await this._loadLayouts();
        });

        useEffect(() => {
            const handleKeyDown = (e) => this._onKeyDown(e);
            document.addEventListener("keydown", handleKeyDown);
            return () => document.removeEventListener("keydown", handleKeyDown);
        });
    }

    _onKeyDown(e) {
        // Don't intercept if user is typing in an input
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        // Escape exits focus mode (works for all users)
        if (e.key === 'Escape' && this.state.focusMode) {
            this.state.focusMode = false;
            this.state.hideOverlays = false;
            e.preventDefault();
            return;
        }

        // H key toggles overlay visibility in focus mode
        if ((e.key === 'h' || e.key === 'H') && this.state.focusMode) {
            this.state.hideOverlays = !this.state.hideOverlays;
            e.preventDefault();
            return;
        }

        // ? key toggles shortcuts help
        if (e.key === '?') {
            this.state.showShortcuts = !this.state.showShortcuts;
            e.preventDefault();
            return;
        }

        // F key toggles focus mode (when no wall is selected for flipping)
        if ((e.key === 'f' || e.key === 'F') && !this.state.selectedMapObjectId) {
            if (this.state.focusMode || this.state.viewMode === '3d') {
                this.toggleFocusMode();
                e.preventDefault();
                return;
            }
        }

        if (!this.state.isAdmin) return;

        if (e.key === 'Delete' || e.key === 'Backspace') {
            if (this.state.selectedMapObjectId) {
                this.deleteMapObject(this.state.selectedMapObjectId);
                e.preventDefault();
            } else if (this.state.selectedLocationId && !this.state.selectedLocationData?.isEditing) {
                this.onLocationRemoved(this.state.selectedLocationId);
                e.preventDefault();
            }
        }

        // 'F' key: Flip selected wall to opposite edge
        if (e.key === 'f' || e.key === 'F') {
            if (this.state.selectedMapObjectId) {
                const obj = this.state.mapObjects.find(o => o.id === this.state.selectedMapObjectId);
                if (obj && obj.object_type === 'wall') {
                    obj.is_flipped = !obj.is_flipped;
                    // Force reactivity by replacing the array
                    this.state.mapObjects = [...this.state.mapObjects];
                    e.preventDefault();
                }
            }
        }
    }

    // =============================================
    // Index helpers
    // =============================================

    _rebuildIndex() {
        this._locIndex.clear();
        for (const loc of this.state.locations) {
            this._locIndex.set(loc.id, loc);
        }
    }

    _getLocation(id) {
        return this._locIndex.get(id) || null;
    }

    // =============================================
    // Data loading
    // =============================================

    async _checkPermissions() {
        this.state.isAdmin = await this.user.hasGroup("stock.group_stock_manager");
    }

    async _loadLayouts() {
        this.state.isLoading = true;
        this.state.layouts = await this.orm.searchRead(
            "warehouse.layout",
            [["active", "=", true]],
            ["id", "name", "warehouse_id", "canvas_width", "canvas_height", "grid_size"]
        );

        const ctxLayoutId = this.props.action.context?.default_layout_id;
        if (ctxLayoutId) {
            await this.selectLayout(ctxLayoutId);
        } else if (this.state.layouts.length > 0) {
            await this.selectLayout(this.state.layouts[0].id);
        }
        this.state.isLoading = false;
    }

    async selectLayout(layoutId) {
        this.state.selectedLayoutId = layoutId;
        this.state.selectedLocationId = null;
        this.state.selectedLocationData = null;
        this.state.heatmapData = {};
        this.state.highlightedLocationId = null;

        try {
            const data = await this.orm.call("warehouse.layout", "get_layout_data", [layoutId]);
            this.state.layoutData = data.layout;
            this.state.locations = data.locations;
            this.state.unplacedLocations = data.unplaced_locations;
            this.state.mapObjects = data.map_objects || [];
            this.state.selectedMapObjectId = null;
            this.state.removedMapObjectIds = [];
            this.state.removedLocationIds = [];
            this.state.measurementUnit = data.layout.measurement_unit || 'm';
            this.state.cellSizeCm = data.layout.cell_size_cm || 100;
            this.state.siblingFloors = data.sibling_floors || [];
            this.state.showAllFloors3D = false;
            this.state.allFloorData = null;
            this.state.isDirty = false;
            this._rebuildIndex();
        } catch (e) {
            console.error(e);
            throw e;
        }
    }

    // =============================================
    // Save
    // =============================================

    async saveLayout() {
        if (!this.state.isDirty || !this.state.selectedLayoutId) return;

        const positions = this.state.locations.map((loc) => ({
            id: loc.id,
            pos_x: loc.pos_x,
            pos_y: loc.pos_y,
            size_x: loc.size_x,
            size_y: loc.size_y,
            location_color: loc.location_color,
            location_shape: loc.location_shape,
            location_rotation: loc.location_rotation || 0,
            shelf_rows: loc.shelf_rows || 1,
            children: (loc.children || []).map((c) => ({
                id: c.id,
                pos_x: c.pos_x,
                pos_y: c.pos_y,
                size_x: c.size_x,
                size_y: c.size_y,
                location_rotation: c.location_rotation || 0,
            })),
        }));

        try {
            const result = await jsonrpc("/warehouse_3d/save_positions", {
                layout_id: this.state.selectedLayoutId,
                positions,
                removed_ids: this.state.removedLocationIds,
            });

            await jsonrpc("/warehouse_3d/save_map_objects", {
                layout_id: this.state.selectedLayoutId,
                objects: this.state.mapObjects,
                removed_ids: this.state.removedMapObjectIds,
            });
            this.state.removedLocationIds = [];
            this.state.removedMapObjectIds = [];

            if (result.success) {
                this.state.isDirty = false;
                this.notification.add(
                    _t("Layout saved — %s locations updated", result.updated_count),
                    { type: "success" }
                );
                await this.selectLayout(this.state.selectedLayoutId);
            }
        } catch (e) {
            this.notification.add(_t("Failed to save layout"), { type: "danger" });
        }
    }

    // =============================================
    // Toggle actions
    // =============================================

    async toggleHeatmap() {
        this.state.heatmapEnabled = !this.state.heatmapEnabled;
        if (this.state.heatmapEnabled && this.state.selectedLayoutId) {
            try {
                this.state.heatmapData = await this.orm.call(
                    "warehouse.layout",
                    "get_heatmap_data",
                    [this.state.selectedLayoutId]
                );
            } catch (e) {
                this.notification.add(_t("Failed to load heatmap data"), { type: "warning" });
                this.state.heatmapEnabled = false;
            }
        }
    }

    async refreshHeatmap() {
        if (!this.state.heatmapEnabled || !this.state.selectedLayoutId) return;
        try {
            this.state.heatmapData = await this.orm.call(
                "warehouse.layout",
                "get_heatmap_data",
                [this.state.selectedLayoutId]
            );
            this.notification.add(_t("Heatmap data refreshed"), { type: "success" });
        } catch (e) {
            this.notification.add(_t("Failed to refresh heatmap data"), { type: "warning" });
        }
    }

    toggleGrid() {
        this.state.gridEnabled = !this.state.gridEnabled;
    }

    toggleViewMode() {
        this.state.viewMode = this.state.viewMode === '2d' ? '3d' : '2d';
        // Reset all-floors 3D when switching views
        if (this.state.viewMode === '2d') {
            this.state.showAllFloors3D = false;
            this.state.allFloorData = null;
        }
    }

    toggleFocusMode() {
        this.state.focusMode = !this.state.focusMode;
        this.state.showShortcuts = false;
        if (this.state.focusMode) {
            this.state.viewMode = '3d';
        } else {
            this.state.hideOverlays = false;
        }
    }

    onFocusLayoutChange(ev) {
        const layoutId = parseInt(ev.target.value, 10);
        if (layoutId) {
            this.selectLayout(layoutId);
        }
    }

    async toggleAllFloors3D() {
        this.state.showAllFloors3D = !this.state.showAllFloors3D;
        if (this.state.showAllFloors3D) {
            await this._loadAllFloorData();
        } else {
            this.state.allFloorData = null;
        }
    }

    async _loadAllFloorData() {
        if (!this.state.siblingFloors || this.state.siblingFloors.length < 2) {
            this.state.allFloorData = null;
            return;
        }
        try {
            const floors = [];
            for (const sf of this.state.siblingFloors) {
                if (sf.id === this.state.selectedLayoutId) {
                    // Use already-loaded data for current floor
                    floors.push({
                        layout_id: sf.id,
                        floor_level: sf.floor_level,
                        name: sf.name,
                        locations: this.state.locations,
                        mapObjects: this.state.mapObjects,
                        canvas_width: this.state.layoutData.canvas_width,
                        canvas_height: this.state.layoutData.canvas_height,
                    });
                } else {
                    const data = await this.orm.call("warehouse.layout", "get_layout_data", [sf.id]);
                    floors.push({
                        layout_id: sf.id,
                        floor_level: sf.floor_level,
                        name: sf.name,
                        locations: data.locations,
                        mapObjects: data.map_objects || [],
                        canvas_width: data.layout.canvas_width,
                        canvas_height: data.layout.canvas_height,
                    });
                }
            }
            this.state.allFloorData = floors;
        } catch (e) {
            this.notification.add(_t("Failed to load multi-floor data"), { type: "warning" });
            this.state.showAllFloors3D = false;
            this.state.allFloorData = null;
        }
    }

    zoomIn() {
        this.state.zoomLevel = Math.min(
            Math.round((this.state.zoomLevel + 0.1) * 10) / 10,
            3.0
        );
    }

    zoomOut() {
        this.state.zoomLevel = Math.max(
            Math.round((this.state.zoomLevel - 0.1) * 10) / 10,
            0.3
        );
    }

    // =============================================
    // Location interactions (O(1) via Map)
    // =============================================

    onLocationSelected(locationId) {
        this.state.selectedLocationId = locationId;
        this.state.selectedLocationData = locationId ? (this._getLocation(locationId) || null) : null;
    }

    onLocationMoved(locationId, newX, newY) {
        if (!this.state.isAdmin) return;
        const loc = this._getLocation(locationId);
        if (loc) {
            loc.pos_x = newX;
            loc.pos_y = newY;
            this.state.isDirty = true;
        }
    }

    onLocationResized(locationId, newSizeX, newSizeY) {
        if (!this.state.isAdmin) return;
        const loc = this._getLocation(locationId);
        if (loc) {
            loc.size_x = Math.max(1, newSizeX);
            loc.size_y = Math.max(1, newSizeY);
            this.state.isDirty = true;
            if (this.state.selectedLocationId === locationId) {
                this.state.selectedLocationData = { ...loc };
            }
        }
    }

    onMapObjectDropped(objType, x, y) {
        if (!this.state.isAdmin) return;

        // Give a temporary local ID. Negative to represent unsaved in backend.
        // We use a value within 32-bit signed integer limits to prevent PostgreSQL overflow.
        const tempId = -Math.floor(Math.random() * 10000000) - 1;

        let icon = '🧱', color = '#555555', sx = 1, sy = 1, name = 'Wall';
        switch (objType) {
            case 'wall': icon = '🧱'; color = '#555555'; sx = 1; sy = 1; name = 'Wall'; break;
            case 'room': icon = '🚪'; color = '#7F8C8D'; sx = 4; sy = 3; name = 'Room'; break;
        }

        const newObj = {
            id: tempId,
            object_type: objType,
            pos_x: x,
            pos_y: y,
            size_x: sx,
            size_y: sy,
            is_flipped: false,
            icon: icon,
            color: color,
            name: name,
        };

        this.state.mapObjects.push(newObj);
        this.state.selectedMapObjectId = tempId;
        this.state.selectedLocationId = null;
        this.state.selectedLocationData = null;
        this.state.isDirty = true;
    }

    onMapObjectSelected(objId) {
        this.state.selectedMapObjectId = objId;
        if (objId) {
            this.state.selectedLocationId = null;
            this.state.selectedLocationData = null;
        }
    }

    onMapObjectMoved(objId, newX, newY) {
        if (!this.state.isAdmin) return;
        const obj = this.state.mapObjects.find(o => o.id === objId);
        if (obj) {
            obj.pos_x = newX;
            obj.pos_y = newY;
            this.state.isDirty = true;
        }
    }

    onMapObjectResized(objId, newSizeX, newSizeY) {
        if (!this.state.isAdmin) return;
        const obj = this.state.mapObjects.find(o => o.id === objId);
        if (obj) {
            obj.size_x = Math.max(1, newSizeX);
            obj.size_y = Math.max(1, newSizeY);
            this.state.isDirty = true;
        }
    }

    deleteMapObject(objId) {
        if (!this.state.isAdmin) return;
        const idx = this.state.mapObjects.findIndex((o) => o.id === objId);
        if (idx !== -1) {
            const obj = this.state.mapObjects.splice(idx, 1)[0];
            if (obj.id > 0) {
                this.state.removedMapObjectIds.push(obj.id);
            }
            if (this.state.selectedMapObjectId === objId) {
                this.state.selectedMapObjectId = null;
            }
            this.state.isDirty = true;
        }
    }

    onChildMoved(parentId, childId, newX, newY) {
        if (!this.state.isAdmin) return;
        const parent = this._getLocation(parentId);
        if (!parent || !parent.children) return;
        const child = parent.children.find((c) => c.id === childId);
        if (child) {
            child.pos_x = Math.max(0, Math.min(newX, (parent.size_x || 2) - (child.size_x || 1)));
            child.pos_y = Math.max(0, Math.min(newY, (parent.size_y || 1) - (child.size_y || 1)));
            this.state.isDirty = true;
        }
    }

    onChildResized(parentId, childId, newSizeX, newSizeY) {
        if (!this.state.isAdmin) return;
        const parent = this._getLocation(parentId);
        if (!parent || !parent.children) return;
        const child = parent.children.find((c) => c.id === childId);
        if (child) {
            child.size_x = Math.max(1, Math.min(newSizeX, (parent.size_x || 2) - child.pos_x));
            child.size_y = Math.max(1, Math.min(newSizeY, (parent.size_y || 1) - child.pos_y));
            this.state.isDirty = true;
        }
    }

    onLocationShapeChanged(locationId, newShape) {
        if (!this.state.isAdmin) return;
        const loc = this._getLocation(locationId);
        if (loc) {
            const colorMap = {
                rack: "#4A90D9", shelf: "#50B86C", bin: "#E67E22",
                zone: "#95A5A6", dock: "#1ABC9C", floor: "#95A5A6",
                packing: "#E67E22", refrigerator: "#2980B9", qc_area: "#8E44AD",
                wall: "#34495E"
            };
            loc.location_shape = newShape;
            loc.location_color = colorMap[newShape] || "#4A90D9";
            this.state.isDirty = true;
            if (this.state.selectedLocationId === locationId) {
                this.state.selectedLocationData = { ...loc };
            }
        }
    }

    onLocationRotationChanged(locationId, customRotation) {
        if (!this.state.isAdmin) return;
        const loc = this._getLocation(locationId);
        if (loc) {
            loc.location_rotation = customRotation;
            this.state.isDirty = true;
            if (this.state.selectedLocationId === locationId) {
                this.state.selectedLocationData = { ...loc };
            }
        }
    }

    onLocationRowsChanged(locationId, newRows) {
        if (!this.state.isAdmin) return;
        const loc = this._getLocation(locationId);
        if (loc) {
            loc.shelf_rows = newRows;
            this.state.isDirty = true;
            if (this.state.selectedLocationId === locationId) {
                this.state.selectedLocationData = { ...loc };
            }
        }
    }

    onLocationDropped(locationId, x, y) {
        if (!this.state.isAdmin) return;

        // Guard: reject if this location is already a child of any placed parent
        for (const parent of this.state.locations) {
            if (parent.children && parent.children.some(c => c.id === locationId)) {
                this.notification.add(
                    _t("This location is already inside '%s'. Cannot place it separately.", parent.name),
                    { type: "warning" }
                );
                return;
            }
        }

        const idx = this.state.unplacedLocations.findIndex((l) => l.id === locationId);
        if (idx !== -1) {
            const loc = this.state.unplacedLocations.splice(idx, 1)[0];
            const newLoc = {
                ...loc,
                pos_x: x,
                pos_y: y,
                size_x: 2,
                size_y: 1,
                location_color: "#4A90D9",
                location_shape: "rack",
                location_rotation: 0,
                children: [],
            };
            this.state.locations.push(newLoc);
            this._locIndex.set(newLoc.id, newLoc);
            this.state.isDirty = true;
        }
    }

    onLocationRemoved(locationId) {
        if (!this.state.isAdmin) return;
        const idx = this.state.locations.findIndex((l) => l.id === locationId);
        if (idx !== -1) {
            const loc = this.state.locations.splice(idx, 1)[0];
            this._locIndex.delete(loc.id);
            this.state.removedLocationIds.push(loc.id);
            this.state.unplacedLocations.push({
                id: loc.id,
                name: loc.name,
                complete_name: loc.complete_name,
                usage: loc.usage,
                product_summary: loc.product_summary || [],
            });
            this.state.selectedLocationId = null;
            this.state.selectedLocationData = null;
            this.state.isDirty = true;
        }
    }

    openLocationForm(locationId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "stock.location",
            res_id: locationId,
            views: [[false, "form"]],
            view_mode: "form",
        });
    }

    // =============================================
    // Product search
    // =============================================

    async searchProduct(query) {
        this.state.productSearchQuery = query;
        if (!query || query.length < 2) {
            this.state.productSearchResults = [];
            this.state.highlightedLocationId = null;
            return;
        }
        try {
            this.state.productSearchResults = await this.orm.call(
                "warehouse.layout",
                "search_product_locations",
                [this.state.selectedLayoutId, query]
            );
        } catch (e) {
            this.state.productSearchResults = [];
        }
    }

    highlightLocation(locationId) {
        this.state.highlightedLocationId = locationId;
        this.state.selectedLocationId = locationId;
        this.state.selectedLocationData = this._getLocation(locationId) || null;
    }

    clearHighlight() {
        this.state.highlightedLocationId = null;
        this.state.productSearchQuery = '';
        this.state.productSearchResults = [];
    }

    changeUnit(unit) {
        this.state.measurementUnit = unit;
    }

    // =============================================
    // Export / Import
    // =============================================

    async exportLayout(format = 'xml') {
        if (!this.state.selectedLayoutId) return;
        try {
            const resp = await fetch(
                `/warehouse_3d/export_layout?layout_id=${this.state.selectedLayoutId}&format=${format}`
            );
            if (!resp.ok) {
                this.notification.add(_t("Export failed"), { type: "danger" });
                return;
            }
            const blob = await resp.blob();
            const disposition = resp.headers.get('Content-Disposition') || '';
            const match = disposition.match(/filename="?([^"]+)"?/);
            const defaultFilename = 'layout_export.xml';
            const filename = match ? match[1] : defaultFilename;

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);

            this.notification.add(_t("Layout exported"), { type: "success" });
        } catch (e) {
            this.notification.add(_t("Export failed — network error"), { type: "danger" });
        }
    }

    async importLayout(file) {
        if (!this.state.selectedLayoutId || !file) return;

        const formData = new FormData();
        formData.append('layout_id', this.state.selectedLayoutId);
        formData.append('file', file);

        try {
            const resp = await fetch('/warehouse_3d/import_layout', {
                method: 'POST',
                body: formData,
            });
            const result = await resp.json();

            if (!resp.ok || !result.success) {
                this.notification.add(
                    _t("Import failed: %s", result.error || 'Unknown error'),
                    { type: "danger" },
                );
                return;
            }

            let msg = _t(
                "Import complete — %s locations placed, %s map objects created",
                result.matched_locations,
                result.created_map_objects,
            );
            if (result.skipped_locations > 0) {
                msg += _t(". %s locations skipped (not found)", result.skipped_locations);
            }
            this.notification.add(msg, { type: "success" });

            // Reload layout to reflect imported data
            await this.selectLayout(this.state.selectedLayoutId);
        } catch (e) {
            this.notification.add(_t("Import failed — network error"), { type: "danger" });
        }
    }
}

registry.category("actions").add("warehouse_designer", WarehouseDesigner);
