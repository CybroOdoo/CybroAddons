/** @odoo-module **/
import { Dropdown } from "@web/core/dropdown/dropdown";
import { onMounted, onWillUnmount, useRef } from "@odoo/owl";

// Extending the Dropdown and adding the inputData into the props
export class FountainDropdown extends Dropdown {
    setup() {
        super.setup();
        this.state.open = false; // Default state is closed

        // Use OWL's useRef to reference the root element
        this.rootRef = useRef("root");

        // Add click outside detection
        this.handleClickOutside = (event) => {
            if (
                this.rootRef.el &&
                !this.rootRef.el.contains(event.target) &&
                this.state.open
            ) {
                this.state.open = false; // Close dropdown if clicked outside
            }
        };

        onMounted(() => {
            // Add event listener when component is mounted
            document.addEventListener('click', this.handleClickOutside);
        });

        onWillUnmount(() => {
            // Remove event listener when component is unmounted
            document.removeEventListener('click', this.handleClickOutside);
        });
    }

    onClick(event) {
        event.preventDefault(); // Prevent default behavior
        this.state.open = !this.state.open; // Toggle dropdown visibility
    }
}

FountainDropdown.template = "fountain.Dropdown";
FountainDropdown.props = {
    ...Dropdown.props,
    inputData: { type: Object, optional: true }
};