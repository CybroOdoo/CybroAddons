/** @odoo-module **/
import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";
import { browser } from "@web/core/browser/browser";
import { onMounted, onPatched, onWillUnmount } from "@odoo/owl";

patch(ListRenderer.prototype, {
    setup() {
        super.setup(...arguments);

        this.keyColumnOrder = this._buildStorageKey();

        // Listen for reset signal from controller
        const resetHandler = () => {
            const defaultCols = super.getActiveColumns(this.props.list);
            this.state.columns = defaultCols;
        };

        onMounted(() => {
            window.addEventListener("column-order-reset", resetHandler);
            this._setupDraggableHeaders();
        });
        onPatched(() => {
            this._setupDraggableHeaders();
        });
        onWillUnmount(() => window.removeEventListener("column-order-reset", resetHandler));
    },

    _buildStorageKey() {
        const model =
            this.props.list?.resModel ||
            this.props.resModel ||
            "unknown";
        const viewId =
            this.props.archInfo?.viewId ||
            this.env?.config?.viewId ||
            0;
        const fieldName = this.props.name || (this.props.list && this.props.list.field && this.props.list.field.name) || "";
        return `column_order,${model},${viewId}${fieldName ? ',' + fieldName : ''}`;
    },

    _isReorderableColumn(col) {
        return !!(col && col.type === "field" && col.widget !== "handle" && col.name);
    },

    _getColumnKey(col) {
        return col.name || String(col.id);
    },

    getActiveColumns() {
        const columns = super.getActiveColumns(...arguments);
        this.keyColumnOrder = this._buildStorageKey();
        const stored = browser.localStorage.getItem(this.keyColumnOrder);
        if (!stored) return columns;

        try {
            const order = JSON.parse(stored);
            if (Array.isArray(order) && order.length) {
                return this._applyOrder(columns, order);
            }
        } catch (e) {
            // Ignore JSON parse errors
        }
        return columns;
    },

    _applyOrder(columns, order) {
        const leadingFixed = [];
        const reorderable = [];
        const trailingFixed = [];

        let inLeading = true;
        for (const col of columns) {
            if (this._isReorderableColumn(col)) {
                reorderable.push(col);
                inLeading = false;
            } else {
                if (inLeading) {
                    leadingFixed.push(col);
                } else {
                    trailingFixed.push(col);
                }
            }
        }

        const remaining = [...reorderable];
        const reordered = [];

        for (const key of order) {
            const idx = remaining.findIndex(
                (c) => this._getColumnKey(c) === String(key)
            );
            if (idx !== -1) {
                reordered.push(remaining.splice(idx, 1)[0]);
            }
        }

        return [...leadingFixed, ...reordered, ...remaining, ...trailingFixed];
    },

    _saveColumnOrder(columns) {
        const reorderableCols = columns.filter((c) => this._isReorderableColumn(c));
        const newOrder = reorderableCols.map((c) => this._getColumnKey(c));
        this.keyColumnOrder = this._buildStorageKey();
        browser.localStorage.setItem(this.keyColumnOrder, JSON.stringify(newOrder));
        window.dispatchEvent(new CustomEvent("column-order-changed"));
    },

    _setupDraggableHeaders() {
        const el = this.tableRef?.el || this.rootRef?.el;
        if (!el) return;

        const thList = el.querySelectorAll("thead th[data-name]");
        thList.forEach((th) => {
            const colName = th.dataset.name;
            const col = this.state.columns.find((c) => c.name === colName);
            if (col && this._isReorderableColumn(col)) {
                th.setAttribute("draggable", "true");
                th.setAttribute("data-col-id", col.id);

                if (!th.dataset.columnDragBound) {
                    th.dataset.columnDragBound = "true";
                    th.addEventListener("dragstart", (ev) => this.onColumnDragStart(ev));
                    th.addEventListener("dragover", (ev) => this.onColumnDragOver(ev));
                    th.addEventListener("dragleave", (ev) => this.onColumnDragLeave(ev));
                    th.addEventListener("drop", (ev) => this.onColumnDrop(ev));
                    th.addEventListener("dragend", (ev) => this.onColumnDragEnd(ev));
                }
            }
        });
    },

    onColumnDragStart(ev) {
        if (ev.target.closest(".o_resize")) {
            ev.preventDefault();
            return;
        }
        const th = ev.currentTarget.closest("th");
        if (!th) return;

        const colName = th.dataset.name;
        const col = this.state.columns.find((c) => c.name === colName);
        if (!col || !this._isReorderableColumn(col)) {
            ev.preventDefault();
            return;
        }

        const key = this._getColumnKey(col);
        this.draggedColKey = key;
        ev.dataTransfer.effectAllowed = "move";
        ev.dataTransfer.setData("text/plain", key);
        th.classList.add("o_col_dragging");
    },

    onColumnDragOver(ev) {
        const targetTh = ev.currentTarget.closest("th");
        if (!targetTh) return;

        const targetName = targetTh.dataset.name;
        const col = this.state.columns.find((c) => c.name === targetName);
        if (!col || !this._isReorderableColumn(col)) {
            return;
        }

        ev.preventDefault();
        ev.dataTransfer.dropEffect = "move";

        const table = targetTh.closest("table");
        if (table) {
            table.querySelectorAll("th.o_col_drag_over").forEach((el) => {
                if (el !== targetTh) el.classList.remove("o_col_drag_over");
            });
        }
        targetTh.classList.add("o_col_drag_over");
    },

    onColumnDragLeave(ev) {
        const targetTh = ev.currentTarget.closest("th");
        if (targetTh && !targetTh.contains(ev.relatedTarget)) {
            targetTh.classList.remove("o_col_drag_over");
        }
    },

    onColumnDrop(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        const targetTh = ev.currentTarget.closest("th");
        if (!targetTh) return;

        const targetName = targetTh.dataset.name;
        const draggedKey = this.draggedColKey || ev.dataTransfer.getData("text/plain");

        this._cleanupDragStyles();

        if (!draggedKey || !targetName || draggedKey === targetName) {
            this.draggedColKey = null;
            return;
        }

        const reorderableCols = this.state.columns.filter((c) => this._isReorderableColumn(c));
        const fromIndex = reorderableCols.findIndex((c) => this._getColumnKey(c) === String(draggedKey));
        const toIndex = reorderableCols.findIndex((c) => this._getColumnKey(c) === String(targetName));

        if (fromIndex !== -1 && toIndex !== -1) {
            const [movedCol] = reorderableCols.splice(fromIndex, 1);
            reorderableCols.splice(toIndex, 0, movedCol);
            const newOrderKeys = reorderableCols.map((c) => this._getColumnKey(c));
            const newColumns = this._applyOrder(this.state.columns, newOrderKeys);
            this.state.columns = newColumns;
            this._saveColumnOrder(newColumns);
        }

        this.draggedColKey = null;
    },

    onColumnDragEnd(ev) {
        this._cleanupDragStyles();
        this.draggedColKey = null;
    },

    _cleanupDragStyles() {
        const el = this.tableRef?.el || this.rootRef?.el;
        if (el) {
            el.querySelectorAll("th.o_col_dragging, th.o_col_drag_over").forEach((el) => {
                el.classList.remove("o_col_dragging", "o_col_drag_over");
            });
        }
    },
});