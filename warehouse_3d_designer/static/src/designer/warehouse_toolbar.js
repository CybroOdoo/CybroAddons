/**
 * Warehouse Toolbar — OWL component for the top toolbar with layout
 * selection, view mode toggle, zoom controls, floor switcher, product
 * search, and admin actions (save, export, import).
 */

import { Component, proxy, t, useProps } from "@odoo/owl";

export class WarehouseToolbar extends Component {
    static template = "warehouse_3d_designer.WarehouseToolbar";
    props = useProps({
        layouts: t.array(),
        selectedLayoutId: t.or([t.number(), t.literal(null)]).optional(),
        gridEnabled: t.boolean(),
        heatmapEnabled: t.boolean(),
        zoomLevel: t.number(),
        isDirty: t.boolean(),
        viewMode: t.string(),
        isAdmin: t.boolean(),
        productSearchQuery: t.string(),
        onSelectLayout: t.function(),
        onToggleGrid: t.function(),
        onToggleHeatmap: t.function(),
        onToggleViewMode: t.function(),
        onZoomIn: t.function(),
        onZoomOut: t.function(),
        onSaveLayout: t.function(),
        onSearchProduct: t.function(),
        onClearSearch: t.function(),
        siblingFloors: t.array(),
        onSelectFloor: t.function(),
        onRefreshHeatmap: t.function(),
        onExportLayout: t.function(),
        onImportLayout: t.function(),
        focusMode: t.boolean(),
        onToggleFocusMode: t.function(),
        showShortcuts: t.boolean(),
        onToggleShortcuts: t.function(),
    });

    setup() {
        this.searchState = proxy({ query: '' });
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

    onExportClick() {
        this.props.onExportLayout();
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

