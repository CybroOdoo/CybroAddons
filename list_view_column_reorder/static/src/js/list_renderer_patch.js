/** @odoo-module **/
import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";
import { browser } from "@web/core/browser/browser";
import { useState, onMounted, onWillUnmount } from "@odoo/owl";
import { useSortable } from "@web/core/utils/sortable_owl";

patch(ListRenderer.prototype, {
    setup() {
        super.setup(...arguments);

        this.keyColumnOrder = this._buildStorageKey();

        let initialOrder = null;
        try {
            const stored = browser.localStorage.getItem(this.keyColumnOrder);
            if (stored) initialOrder = JSON.parse(stored);
        } catch (e) {
        }

        this.columnReorderState = useState({ order: initialOrder });

        // When "Set Default" is clicked, the controller dispatches this event
        // so we wipe the in-memory order and OWL re-renders the default layout.
        const resetHandler = () => {
            this.columnReorderState.order = null;
        };
        onMounted(() => window.addEventListener("column-order-reset", resetHandler));
        onWillUnmount(() => window.removeEventListener("column-order-reset", resetHandler));

        let draggedColName = null;

        useSortable({
            enable: () => true,
            ref: this.tableRef,
            elements: "thead th[data-name]",
            cursor: "grabbing",
            placeholderClasses: ["o_col_dragging"],
            onDragStart: (params) => {
                const { element } = params;
                draggedColName = element.dataset.name;
                
                const thead = this.tableRef.el.querySelector("thead");
                if (thead && !thead._reorderClickBlocker) {
                    thead._reorderClickBlocker = true;
                    thead.addEventListener("click", (ev) => {
                        if (thead.dataset.preventClick === "true") {
                            ev.stopImmediatePropagation();
                            ev.preventDefault();
                        }
                    }, true);
                }
                return params;
            },
            onDragEnd: (params) => {
                const thead = this.tableRef.el.querySelector("thead");
                if (thead) {
                    thead.dataset.preventClick = "true";
                    setTimeout(() => {
                        if (thead) thead.dataset.preventClick = "false";
                    }, 100);
                }
                return params;
            },
            onDrop: (params) => {
                const { previous, next } = params;
                if (!draggedColName) return;

                if (previous && previous.dataset.name) {
                    this._reorderColumnsInsertAfter(draggedColName, previous.dataset.name);
                } else if (next && next.dataset.name) {
                    this._reorderColumnsInsertBefore(draggedColName, next.dataset.name);
                }
                
                draggedColName = null;
            },
        });
    },

    _buildStorageKey() {
        const model = this.props.list?.resModel || "unknown";
        const viewId =
            this.props.archInfo?.viewId ||
            this.env?.config?.viewId ||
            0;
        return `column_order,${model},${viewId}`;
    },

    _reorderColumnsInsertAfter(fromName, afterName) {
        if (fromName === afterName) return;
        const columns = [...this.columns];
        
        const fromIndex = columns.findIndex((c) => String(c.name) === String(fromName));
        if (fromIndex === -1) return;
        const [moved] = columns.splice(fromIndex, 1);
        
        const afterIndex = columns.findIndex((c) => String(c.name) === String(afterName));
        if (afterIndex === -1) {
            columns.push(moved);
        } else {
            columns.splice(afterIndex + 1, 0, moved);
        }
        this._saveColumnOrder(columns);
    },

    _reorderColumnsInsertBefore(fromName, beforeName) {
        if (fromName === beforeName) return;
        const columns = [...this.columns];
        
        const fromIndex = columns.findIndex((c) => String(c.name) === String(fromName));
        if (fromIndex === -1) return;
        const [moved] = columns.splice(fromIndex, 1);
        
        const beforeIndex = columns.findIndex((c) => String(c.name) === String(beforeName));
        if (beforeIndex === -1) {
            columns.unshift(moved);
        } else {
            columns.splice(beforeIndex, 0, moved);
        }
        this._saveColumnOrder(columns);
    },

    _saveColumnOrder(columns) {
        const newOrder = columns.map((c) => c.name || String(c.id));
        this.columnReorderState.order = newOrder;
        browser.localStorage.setItem(this.keyColumnOrder, JSON.stringify(newOrder));
        // Notify the controller so its reactive "Set Default" button appears at once
        window.dispatchEvent(new CustomEvent("column-order-changed"));
    },

    // ── OWL render hook — applies persisted order ───

    /**
     * Overrides the base getActiveColumns().
     * Called on every OWL render cycle (onWillRender sets this.columns).
     * Returning columns in the stored order causes both <thead> and <tbody>
     * to be rendered in that order — full table sync.
     */
    getActiveColumns() {
        const columns = super.getActiveColumns(...arguments);
        const { order } = this.columnReorderState;
        if (!order || !order.length) return columns;
        return this._applyOrder(columns, order);
    },

    _applyOrder(columns, order) {
        const remaining = [...columns];
        const result = [];

        for (const key of order) {
            const idx = remaining.findIndex(
                (c) => c.name === key || String(c.id) === String(key)
            );
            if (idx !== -1) result.push(remaining.splice(idx, 1)[0]);
        }
        // Append any NEW columns not yet in the stored order
        return [...result, ...remaining];
    },
});