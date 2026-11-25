import { proxy, signal } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.lockOrm = useService("orm");
        this.lockDialog = proxy({ open: false, invalid: false });
        this.lockPassword = signal.ref();
    },

    async openWithMenuLock(menu, openMenu) {
        if (!menu) {
            return;
        }
        const selection = { menu, openMenu };
        this.pendingSelection = selection;
        this.lockDialog.open = false;
        this.lockDialog.invalid = false;
        const required = await this.lockOrm.call("res.users", "menu_lock_required", [menu.id]);
        if (this.pendingSelection !== selection) {
            return;
        }
        if (required) {
            this.lockDialog.open = true;
        } else {
            this.pendingSelection = null;
            return openMenu();
        }
    },

    onNavBarDropdownItemSelection(menu) {
        return this.openWithMenuLock(menu, () => super.onNavBarDropdownItemSelection(menu));
    },

    _onMenuClicked(menu) {
        return this.openWithMenuLock(menu, () => super._onMenuClicked(menu));
    },

    async confirmMenuLock() {
        const selection = this.pendingSelection;
        if (!selection) {
            return;
        }
        const valid = await this.lockOrm.call("res.users", "verify_menu_lock", [
            selection.menu.id, this.lockPassword().value,
        ]);
        if (this.pendingSelection !== selection) {
            return;
        }
        if (valid) {
            this.cancelMenuLock();
            return selection.openMenu();
        }
        this.lockDialog.invalid = true;
    },

    showPassword() {
        const input = this.lockPassword();
        input.type = input.type === "password" ? "text" : "password";
    },

    cancelMenuLock() {
        this.pendingSelection = null;
        this.lockDialog.open = false;
    },
});
