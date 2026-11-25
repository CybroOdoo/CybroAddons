import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, proxy } from "@odoo/owl";

export class ViberSystray extends Component {
    static template = "odoo_viber_integration.ViberSystray";

    setup() {
        this.orm = useService("orm");
        this.state = proxy({ isOpen: false, users: [] });
        onWillStart(this.fetchUsers);
    }

    /**
     * Load the users that can be contacted through Viber.
     */
    async fetchUsers() {
        const { users } = await this.orm.call("res.users", "get_users", []);
        this.state.users = users;
    }

    /**
     * Hide the Viber contact form.
     */
    onCloseViber() {
        this.state.isOpen = false;
    }

    /**
     * Show the Viber contact form.
     */
    onClickViber() {
        this.state.isOpen = true;
    }

    /**
     * Open the Viber chat of the selected user.
     *
     * @param {Event} ev change event of the user selector
     */
    onSelectionUser(ev) {
        const phone = ev.target.value;
        if (phone) {
            const userNumber = phone.replace(/[-()\s]/g, "");
            window.location.assign(
                `viber://chat?number=${encodeURIComponent(userNumber)}`
            );
        }
    }
}

registry.category("systray").add("ViberSystray", { Component: ViberSystray }, {
    sequence: 1,
});
