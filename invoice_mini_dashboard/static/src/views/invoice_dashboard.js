/** @odoo-module */
import {
    useService
} from "@web/core/utils/hooks";

const {
    Component,
    onWillStart
} = owl;

export class AccountDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        onWillStart(async () => {
            this.invoiceData = await this.orm.call(
                "account.move",
                "retrieve_out_invoice_dashboard",
            );
        });
    }
    /**
     * This method clears the current search query and activates
     * the filters found in `filter_name` attibute from button pressed
     */
    setSearchContext(ev) {
        let filter_name = ev.currentTarget.getAttribute("filter_name");
        let filters = filter_name.split(',');
        let searchItems = this.env.searchModel.getSearchItems((item) => filters.includes(item.name));
        this.env.searchModel.query = [];
        for (const item of searchItems) {
            this.env.searchModel.toggleSearchItem(item.id);
        }
    }
}
AccountDashboard.template = 'account.AccountDashboard'
