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
    AccountDashboard
} from '@invoice_mini_dashboard/views/invoice_dashboard';

export class AccountDashBoardRenderer extends ListRenderer {

static template = 'invoice_mini_dashboard.AccountListView';
static components = {...ListRenderer.components,
    AccountDashboard,
};
}
export const AccountDashboardListView = {
    ...listView,
    Renderer: AccountDashBoardRenderer,
};
registry.category("views").add("account_dashboard_list", AccountDashboardListView);
