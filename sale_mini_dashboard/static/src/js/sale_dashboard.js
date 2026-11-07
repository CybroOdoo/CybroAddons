import { Component, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * Sale Dashboard component for managing sales data and filters.
 * @extends Component
 */
export class SaleDashBoard extends Component {
    static template = "sale_mini_dashboard.SaleDashboard";
    static props = {};

    /**
     * Setup method for initializing the component.
     */
    setup() {
        this.orm = useService("orm");
        this.saleData = {};

        // Fetch sales data when the component is about to start
        onWillStart(async () => {
            this.saleData = await this.orm.call("sale.order", "get_dashboard_values");
        });
    }

    /**
     * Clears the current search query and activates the filters listed in the
     * `filter_name` attribute of the clicked element.
     * @param {Event} ev - The click event.
     */
    setSearchContext(ev) {
        ev.preventDefault();
        const filters = ev.currentTarget.getAttribute("filter_name").split(",");
        const searchModel = this.env.searchModel;
        const searchItems = searchModel.getSearchItems((item) => filters.includes(item.name));
        // Clear the current search query, then activate the requested filters
        searchModel.query.length = 0;
        for (const item of searchItems) {
            searchModel.toggleSearchItem(item.id);
        }
    }
}
