import { Component, onWillStart, proxy } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class AccountDashboardBill extends Component {
    static template = "invoice_mini_dashboard.AccountDashboardBill";

    setup() {
        this.orm = useService("orm");
        this.state = proxy({
            invoiceData: {
                draft: 0,
                posted: 0,
                cancelled: 0,
                paid: 0,
                not_paid: 0,
                not_paid_amount: 0,
                paid_amount: 0,
                lost_amount: 0,
                expected_amount: 0,
                company_currency_symbol: "",
            },
        });

        onWillStart(async () => {
            this.state.invoiceData = await this.orm.call(
                "account.move",
                "retrieve_in_invoice_dashboard",
            );
        });
    }

    /**
     * Clear the current search query and activate the filters listed in the
     * `filter_name` attribute of the pressed button.
     */
    setSearchContext(ev) {
        const filterName = ev.currentTarget.getAttribute("filter_name");
        const moveTypeFilter = ev.currentTarget.getAttribute("move_type_filter");
        const filters = filterName.split(",");
        if (moveTypeFilter) {
            filters.push(moveTypeFilter);
        }
        const searchItems = this.env.searchModel.getSearchItems(
            (item) => filters.includes(item.name)
        );
        this.env.searchModel.query.length = 0;
        for (const item of searchItems) {
            this.env.searchModel.toggleSearchItem(item.id);
        }
    }
}
