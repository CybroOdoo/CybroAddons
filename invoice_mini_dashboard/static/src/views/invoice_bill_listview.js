/** @odoo-module **/
import {
    registry
} from "@web/core/registry";
import {
    listView
} from "@web/views/list/list_view";
import {
    ListRenderer
} from "@web/views/list/list_renderer";
import {
    AccountDashboardBill
} from '@invoice_mini_dashboard/views/invoice_bill_dashboard';
export class AccountDashBoardBillRenderer extends ListRenderer {};
AccountDashBoardBillRenderer.template = 'invoice_mini_dashboard.AccountListBillView';
AccountDashBoardBillRenderer.components = Object.assign({}, ListRenderer.components, {
    AccountDashboardBill
})
export const AccountDashboardListView = {
    ...listView,
    Renderer: AccountDashBoardBillRenderer,
};
registry.category("views").add("account_dashboard_list_bill", AccountDashboardListView);
