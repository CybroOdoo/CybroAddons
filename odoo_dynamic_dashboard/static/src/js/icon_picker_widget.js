/** @odoo-module **/
import { Component, useState, useExternalListener, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const ICONS = [
    // Charts
    "fa-solid fa-chart-bar", "fa-solid fa-chart-line", "fa-solid fa-chart-pie",
    "fa-solid fa-chart-area", "fa-solid fa-chart-column",
    // Business
    "fa-solid fa-briefcase", "fa-solid fa-building", "fa-solid fa-store",
    "fa-solid fa-handshake", "fa-solid fa-receipt", "fa-solid fa-file-invoice",
    "fa-solid fa-file-invoice-dollar", "fa-solid fa-coins", "fa-solid fa-dollar-sign",
    "fa-solid fa-credit-card", "fa-solid fa-wallet", "fa-solid fa-piggy-bank",
    "fa-solid fa-money-bill-wave", "fa-solid fa-cash-register",
    // People & HR
    "fa-solid fa-users", "fa-solid fa-user", "fa-solid fa-user-tie",
    "fa-solid fa-people-group", "fa-solid fa-id-card", "fa-solid fa-address-book",
    "fa-solid fa-user-group",
    // Operations
    "fa-solid fa-box", "fa-solid fa-boxes-stacked", "fa-solid fa-warehouse",
    "fa-solid fa-truck", "fa-solid fa-industry", "fa-solid fa-gear",
    "fa-solid fa-gears", "fa-solid fa-screwdriver-wrench", "fa-solid fa-wrench",
    "fa-solid fa-cube",
    // Tech
    "fa-solid fa-laptop", "fa-solid fa-desktop", "fa-solid fa-server",
    "fa-solid fa-database", "fa-solid fa-cloud", "fa-solid fa-shield-halved",
    "fa-solid fa-code", "fa-solid fa-wifi", "fa-solid fa-microchip",
    // Marketing & Sales
    "fa-solid fa-bullhorn", "fa-solid fa-envelope", "fa-solid fa-paper-plane",
    "fa-solid fa-tags", "fa-solid fa-star", "fa-solid fa-heart",
    "fa-solid fa-thumbs-up", "fa-solid fa-comments", "fa-solid fa-bullseye",
    "fa-solid fa-percent",
    // Tasks & Projects
    "fa-solid fa-list-check", "fa-solid fa-calendar", "fa-solid fa-clock",
    "fa-solid fa-flag", "fa-solid fa-bookmark", "fa-solid fa-bell",
    "fa-solid fa-magnifying-glass", "fa-solid fa-filter",
    "fa-solid fa-circle-check", "fa-solid fa-clipboard",
    // Finance
    "fa-solid fa-scale-balanced", "fa-solid fa-arrow-trend-up",
    "fa-solid fa-arrow-trend-down", "fa-solid fa-sack-dollar",
    "fa-solid fa-file-contract",
    // Communication
    "fa-solid fa-phone", "fa-solid fa-mobile", "fa-solid fa-at",
    "fa-solid fa-globe", "fa-solid fa-map-location-dot", "fa-solid fa-headset",
    // Misc
    "fa-solid fa-house", "fa-solid fa-graduation-cap", "fa-solid fa-stethoscope",
    "fa-solid fa-car", "fa-solid fa-plane", "fa-solid fa-bolt",
    "fa-solid fa-fire", "fa-solid fa-leaf", "fa-solid fa-robot",
    "fa-solid fa-wand-magic-sparkles", "fa-solid fa-trophy", "fa-solid fa-gem",
    "fa-solid fa-rocket", "fa-solid fa-shield",
];

class IconPickerWidget extends Component {
    static template = "odoo_dynamic_dashboard.IconPickerWidget";
    static props = { ...standardFieldProps };

    setup() {
        this.state = useState({ open: false, search: "" });
        this.root = useRef("root");
        useExternalListener(window, "click", this._onOutsideClick.bind(this));
    }

    get value() {
        return this.props.record.data[this.props.name] || "fa-solid fa-box";
    }

    get filteredIcons() {
        const q = this.state.search.toLowerCase().trim();
        if (!q) return ICONS;
        return ICONS.filter(cls => {
            const name = cls.replace("fa-solid ", "").replace(/fa-/g, "").replace(/-/g, " ");
            return name.includes(q);
        });
    }

    _onOutsideClick(ev) {
        if (this.root.el && !this.root.el.contains(ev.target)) {
            this.state.open = false;
        }
    }

    toggleOpen = (ev) => {
        ev.stopPropagation();
        this.state.open = !this.state.open;
        this.state.search = "";
    }

    selectIcon = (ev, cls) => {
        ev.stopPropagation();
        this.props.record.update({ [this.props.name]: cls });
        this.state.open = false;
    }

    onSearchClick = (ev) => {
        ev.stopPropagation();
    }
}

registry.category("fields").add("icon_picker", {
    component: IconPickerWidget,
    supportedTypes: ["char"],
    extractProps: ({ attrs }) => ({}),
});
