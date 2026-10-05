import { Component, proxy, t, useProps } from "@odoo/owl";
import { BLOCK_CATEGORIES, BLOCK_TYPES } from "../block_catalog/block_catalog";

export const BLOCK_DRAG_TYPE = "application/x-odoo-dynamic-dashboard-block";

/**
 * Side panel of the dashboard builder listing the building blocks by category: they
 * are dragged onto the dashboard, or clicked to be appended at its end.
 */
export class BlockPalette extends Component {
    static template = "odoo_dynamic_dashboard.BlockPalette";
    props = useProps({
        onAdd: t.function(),
        onDragEnd: t.function(),
    });

    setup() {
        this.state = proxy({ search: "" });
    }

    getCategories() {
        const search = this.state.search.trim().toLowerCase();
        return BLOCK_CATEGORIES.map((category) => ({
            ...category,
            blockTypes: BLOCK_TYPES.filter(
                (info) =>
                    info.category === category.id &&
                    (!search || `${info.label} ${info.help}`.toLowerCase().includes(search))
            ),
        })).filter((category) => category.blockTypes.length);
    }

    onSearchInput(ev) {
        this.state.search = ev.target.value;
    }

    onDragStart(ev, info) {
        ev.dataTransfer.effectAllowed = "copy";
        ev.dataTransfer.setData(BLOCK_DRAG_TYPE, info.type);
    }

    onKeydown(ev, info) {
        if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            this.props.onAdd(info.type);
        }
    }
}
