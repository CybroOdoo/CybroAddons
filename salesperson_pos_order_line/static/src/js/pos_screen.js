/** @odoo-module **/
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { _t } from "@web/core/l10n/translation";
import { SelectionPopup } from "@point_of_sale/app/components/popups/selection_popup/selection_popup";
import { patch } from "@web/core/utils/patch";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(ControlButtons.prototype, {

    /**
     * Initializes the component by setting up services such as ORM and Dialog.
     */
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.dialog = useService("dialog");
    },

    /**
     * Handles the click event for selecting a salesperson for a highlighted order line.
     * Displays a selection popup with a list of users.
     */
    async onClick() {
        const orderline = this.pos.getOrder()?.getSelectedOrderline();
        if (!orderline) {
            this.dialog.add(AlertDialog, {
                title: _t("No orderline selected."),
                body: _t("Select an orderline to add a salesperson"),
            });
            return;
        }
        const res_users = await this.orm.call("res.users", "search_read", [[], ["id", "name"]]);
        const salespersonList = res_users.map((salesperson) => ({
            id: salesperson.id,
            item: salesperson,
            label: salesperson.name,
            isSelected: false,
        }));
        const confirmed = await makeAwaitable(this.dialog, SelectionPopup, {
            title: _t("Select the Salesperson"),
            list: salespersonList,
        });
        if (confirmed) {
            orderline.update({ user_id: confirmed });
            orderline.salesperson = confirmed.name;
        }
    }
});
