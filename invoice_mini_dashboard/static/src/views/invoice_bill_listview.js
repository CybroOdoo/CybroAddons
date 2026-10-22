import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { AccountDashboardBill } from "@invoice_mini_dashboard/views/invoice_bill_dashboard";

export class AccountDashBoardBillRenderer extends ListRenderer {
    static template = "invoice_mini_dashboard.AccountListBillView";
    static components = { ...ListRenderer.components, AccountDashboardBill };
}

export const AccountDashBoardBillRendererListView = {
    ...listView,
    Renderer: AccountDashBoardBillRenderer,
};

registry.category("views").add("account_dashboard_list_bill", AccountDashBoardBillRendererListView);
