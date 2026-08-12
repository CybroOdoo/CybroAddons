/** @odoo-module **/

/**
 * Warehouse Toolbar — OWL component for the top toolbar with layout
 * selection, view mode toggle, zoom controls, floor switcher, product
 * search, and admin actions (save, export, import).
 */

import { Component, useState } from "@odoo/owl";

export class WarehouseToolbar extends Component {
    static template = "warehouse_3d_designer.WarehouseToolbar";
    static props = {
        layouts: { type: Array },
        selectedLayoutId: { type: [Number, { value: null }], optional: true },
        gridEnabled: { type: Boolean },
        heatmapEnabled: { type: Boolean },
        zoomLevel: { type: Number },
        isDirty: { type: Boolean },
        viewMode: { type: String },
        isAdmin: { type: Boolean },
        productSearchQuery: { type: String },
        onSelectLayout: { type: Function },
        onToggleGrid: { type: Function },
        onToggleHeatmap: { type: Function },
        onToggleViewMode: { type: Function },
        onZoomIn: { type: Function },
        onZoomOut: { type: Function },
        onSaveLayout: { type: Function },
        onSearchProduct: { type: Function },
        onClearSearch: { type: Function },
        siblingFloors: { type: Array },
        onSelectFloor: { type: Function },
        onRefreshHeatmap: { type: Function },
        onExportLayout: { type: Function },
        onImportLayout: { type: Function },
        focusMode: { type: Boolean },
        onToggleFocusMode: { type: Function },
        showShortcuts: { type: Boolean },
        onToggleShortcuts: { type: Function },
    };

    setup() {
        this.searchState = useState({ query: '' });
        this._searchTimer = null;
    }

    get zoomPercent() {
        return Math.round(this.props.zoomLevel * 100);
    }

    onLayoutChange(ev) {
        const layoutId = parseInt(ev.target.value, 10);
        if (layoutId) {
            this.props.onSelectLayout(layoutId);
        }
    }

    onFloorClick(floorId) {
        if (floorId !== this.props.selectedLayoutId) {
            this.props.onSelectFloor(floorId);
        }
    }

    getFloorLabel(floorLevel) {
        if (floorLevel === 0) return 'GF';
        if (floorLevel < 0) return `B${Math.abs(floorLevel)}`;
        return `F${floorLevel}`;
    }

    onSearchInput(ev) {
        this.searchState.query = ev.target.value;
        // Debounce: wait 300ms after last keystroke before searching
        clearTimeout(this._searchTimer);
        this._searchTimer = setTimeout(() => {
            this.props.onSearchProduct(this.searchState.query);
        }, 300);
    }

    onSearchClear() {
        this.searchState.query = '';
        clearTimeout(this._searchTimer);
        this.props.onClearSearch();
    }

    onSearchKeydown(ev) {
        if (ev.key === 'Escape') {
            this.onSearchClear();
        }
    }

    onExportClick(format) {
        this.props.onExportLayout(format);
    }

    onImportClick() {
        // Create a hidden file input, trigger it, and pass the file to the parent
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.xml,text/xml,application/xml';
        input.style.display = 'none';
        input.addEventListener('change', (ev) => {
            const file = ev.target.files[0];
            if (file) {
                this.props.onImportLayout(file);
            }
            input.remove();
        });
        document.body.appendChild(input);
        input.click();
    }
}

