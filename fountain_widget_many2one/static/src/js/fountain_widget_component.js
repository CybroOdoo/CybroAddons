/** @odoo-module **/

import { Component, types as t, useProps, proxy, signal, useEffect } from "@odoo/owl";
import { dropdownProps } from "@web/core/dropdown/dropdown";

export class FountainDropdown extends Component {
    static template = "fountain.Dropdown";
    props = useProps({
        ...dropdownProps,
        inputData: t.object().optional(),
    });

    rootRef = signal.ref();

    setup() {
        this.state = proxy({ isOpen: false });
        this.onWindowClick = this.onWindowClick.bind(this);
        useEffect(() => {
            window.addEventListener("click", this.onWindowClick);
            return () => window.removeEventListener("click", this.onWindowClick);
        }, () => []);
    }

    onWindowClick(ev) {
        const rootEl = this.rootRef();
        if (this.state.isOpen && rootEl && !rootEl.contains(ev.target)) {
            this.state.isOpen = false;
        }
    }

    onClick(event) {
        event.preventDefault(); // Prevent default behavior
        this.state.isOpen = !this.state.isOpen;
    }
}