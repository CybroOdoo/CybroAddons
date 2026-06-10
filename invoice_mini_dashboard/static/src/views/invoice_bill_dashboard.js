/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onWillUpdateProps } from "@odoo/owl";

//const { Component, onWillStart,  } = owl;
export class AccountDashboardBill extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.fetchData = async () => {
            this.invoiceData = await this.orm.call(
                "account.move",
                "retrieve_in_invoice_dashboard",
                [this.props.domain || []],
                { context: this.props.context || this.env.searchModel.context }
            );
        };
        onWillStart(this.fetchData);
        onWillUpdateProps(this.fetchData);
    }
    /**
     * This method clears the current search query and activates
     * the filters found in `filter_name` attibute from button pressed
     */
    setSearchContext(ev) {
        let filter_name = ev.currentTarget.getAttribute("filter_name");
        let filters = filter_name.split(',');
        let conflictingFilters = {
            'draft': ['posted', 'cancel', 'paid', 'open'],
            'posted': ['draft', 'cancel', 'paid', 'open'],
            'cancel': ['draft', 'posted', 'paid', 'open'],
            'paid': ['draft', 'cancel', 'open', 'posted'],
            'open': ['draft', 'cancel', 'paid', 'posted']
        };
        // 1. Clear conflicting filters
        let allToRemove = new Set();
        for (const f of filters) {
            let conflicts = conflictingFilters[f] || [];
            conflicts.forEach(c => allToRemove.add(c));
        }
        for (const filterName of allToRemove) {
            const searchItem = this.env.searchModel.getSearchItems((item) => item.name === filterName)[0];
            if (searchItem && this.env.searchModel.query.some(q => q.searchItemId === searchItem.id)) {
                this.env.searchModel.toggleSearchItem(searchItem.id);
            }
        }
        // 2. Activate target filters
        let searchItems = this.env.searchModel.getSearchItems((item) => filters.includes(item.name));
        for (const item of searchItems) {
            if (!this.env.searchModel.query.some(q => q.searchItemId === item.id)) {
                this.env.searchModel.toggleSearchItem(item.id);
            }
        }
        // 3. Restore Default Move Type Filter (Smart Context Restoration)
        const defaultMoveType = this.props.context?.default_move_type || this.env.searchModel.context?.default_move_type;
        if (defaultMoveType) {
            const typeFilter = this.env.searchModel.getSearchItems((item) => {
                const domainStr = String(item.domain || "");
                return domainStr.includes('move_type') && domainStr.includes(defaultMoveType);
            })[0];
            if (typeFilter) {
                const isActive = this.env.searchModel.query.some(q => q.searchItemId === typeFilter.id);
                if (!isActive) {
                    this.env.searchModel.toggleSearchItem(typeFilter.id);
                }
            }
        }
    }
}
AccountDashboardBill.template = 'account.AccountDashboardBill'
