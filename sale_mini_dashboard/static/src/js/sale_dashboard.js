/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart } = owl;

/**
 * Sale Dashboard component for managing sales data and filters.
 * @extends Component
 */
export class SaleDashBoard extends Component {
    /**
     * Setup method for initializing the component.
     */
    setup() {
        // Get references to Odoo services
        this.orm = useService("orm");
        this.action = useService("action");

        // Fetch sales data when the component is about to start
        onWillStart(async () => {
            this.saleData = await this.orm.call(
                "sale.order",
                "get_dashboard_values"
            );
        });
    }

    /**
     * This method clears the current search query and activates
     * the filters found in the `filter_name` attribute from the pressed button.
     * @param {Event} ev - The event object from the button press.
     */
    setSearchContext(ev) {
        // Extract filter names from the button attribute
        let filter_name = ev.currentTarget.getAttribute("filter_name");
        let filters = filter_name.split(',');

        // Get search items based on the specified filter names
        let searchItems = this.env.searchModel.getSearchItems((item) => filters.includes(item.name));

        // Clear the current search query
        this.env.searchModel.query = [];

        // Activate filters in the search model
        for (const item of searchItems) {
            this.env.searchModel.toggleSearchItem(item.id);
        }
    }
}

// Template for the SaleDashBoard component
SaleDashBoard.template = 'sale_mini_dashboard.SaleDashboard';
