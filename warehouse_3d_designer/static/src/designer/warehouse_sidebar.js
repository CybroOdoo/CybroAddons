/** @odoo-module **/

/**
 * Warehouse Sidebar — OWL component for the location detail panel,
 * unplaced locations list, shape/rotation editing, search results,
 * and measurement unit configuration.
 */

import { Component, useState } from "@odoo/owl";

export class WarehouseSidebar extends Component {
    static template = "warehouse_3d_designer.WarehouseSidebar";
    static props = {
        selectedLocationId: { type: [Number, { value: null }], optional: true },
        selectedLocationData: { type: [Object, { value: null }], optional: true },
        locations: { type: Array },
        unplacedLocations: { type: Array },
        heatmapData: { type: Object },
        heatmapEnabled: { type: Boolean },
        isAdmin: { type: Boolean },
        productSearchResults: { type: Array },
        highlightedLocationId: { type: [Number, { value: null }], optional: true },
        measurementUnit: { type: String },
        cellSizeCm: { type: Number },
        onLocationSelected: { type: Function },
        onLocationDropped: { type: Function },
        onLocationRemoved: { type: Function },
        onOpenLocation: { type: Function },
        onShapeChanged: { type: Function },
        onRotationChanged: { type: Function, optional: true },
        onRowsChanged: { type: Function, optional: true },
        onHighlightLocation: { type: Function },
        onUnitChanged: { type: Function },
    };

    setup() {
        this.filterState = useState({ query: '' });
    }

    get selectedLoc() {
        return this.props.selectedLocationData;
    }

    get shapeOptions() {
        return [
            { value: 'rack', label: 'Rack', icon: '📦' },
            { value: 'shelf', label: 'Shelf', icon: '🗄️' },
            { value: 'bin', label: 'Bin', icon: '📥' },
            { value: 'zone', label: 'Zone', icon: '🔲' },
            { value: 'dock', label: 'Dock', icon: '🚛' },
            { value: 'floor', label: 'Floor', icon: '⬜' },
            { value: 'packing', label: 'Packing Area', icon: '📋' },
            { value: 'refrigerator', label: 'Refrigerator', icon: '❄️' },
            { value: 'qc_area', label: 'QC Area', icon: '✅' },
        ];
    }

    /** Shape icon lookup */
    _shapeIcon(shape) {
        const map = {
            rack: '📦', shelf: '🗄️', bin: '📥', zone: '🔲',
            dock: '🚛', floor: '⬜', packing: '📋',
            refrigerator: '❄️', qc_area: '✅'
        };
        return map[shape] || '📍';
    }

    get mapObjectOptions() {
        return [
            { value: 'wall', label: 'Wall', icon: '🧱' },
            { value: 'room', label: 'Room/Office', icon: '🚪' },
        ];
    }

    /** Placed locations filtered by sidebar search */
    get filteredLocations() {
        const q = (this.filterState.query || '').toLowerCase().trim();
        if (!q) return this.props.locations;
        return this.props.locations.filter(loc => {
            const name = (loc.name || '').toLowerCase();
            const path = (loc.complete_name || '').toLowerCase();
            return name.includes(q) || path.includes(q);
        });
    }

    convertSize(gridCells) {
        const cm = gridCells * this.props.cellSizeCm;
        switch (this.props.measurementUnit) {
            case 'cm': return `${cm} cm`;
            case 'inch': return `${(cm / 2.54).toFixed(1)}″`;
            default: return `${(cm / 100).toFixed(2)} m`;
        }
    }

    getArea() {
        const loc = this.selectedLoc;
        if (!loc) return '';
        const w = (loc.size_x || 2) * this.props.cellSizeCm;
        const h = (loc.size_y || 1) * this.props.cellSizeCm;
        switch (this.props.measurementUnit) {
            case 'cm': return `${(w * h).toFixed(0)} cm²`;
            case 'inch': return `${((w / 2.54) * (h / 2.54)).toFixed(1)} sq.in`;
            default: return `${((w / 100) * (h / 100)).toFixed(2)} m²`;
        }
    }

    onDragStart(ev) {
        const locId = ev.target.dataset.locId;
        const objType = ev.target.dataset.objType;
        if (locId) {
            ev.dataTransfer.setData("text/plain", locId);
            ev.dataTransfer.setData("application/x-warehouse-location", locId);
        } else if (objType) {
            ev.dataTransfer.setData("application/x-warehouse-map-object", objType);
        }
    }

    onShapeChange(ev) {
        this.props.onShapeChanged(this.props.selectedLocationId, ev.target.value);
    }

    onRotationChange(ev) {
        const rot = parseInt(ev.target.value, 10);
        if (!isNaN(rot) && this.props.onRotationChanged) {
            this.props.onRotationChanged(this.props.selectedLocationId, rot);
        }
    }

    onRowsChange(ev) {
        const rows = parseInt(ev.target.value, 10);
        if (!isNaN(rows) && rows >= 1) {
            // Need to pass this event up. Using the same pattern as shape change
            if (this.props.onRowsChanged) {
                this.props.onRowsChanged(this.props.selectedLocationId, rows);
            }
        }
    }

    onClickResult(ev) {
        const locId = parseInt(ev.currentTarget.dataset.locId, 10);
        if (locId) this.props.onHighlightLocation(locId);
    }

    /** Select a placed location from the sidebar list */
    onSelectPlacedLocation(ev) {
        const locId = parseInt(ev.currentTarget.dataset.locId, 10);
        if (locId) this.props.onLocationSelected(locId);
    }

    onFilterInput(ev) {
        this.filterState.query = ev.target.value;
    }

    onFilterClear() {
        this.filterState.query = '';
    }

    onFilterKeydown(ev) {
        if (ev.key === 'Escape') {
            this.filterState.query = '';
        }
    }

    onUnitChange(ev) {
        this.props.onUnitChanged(ev.target.value);
    }
}
