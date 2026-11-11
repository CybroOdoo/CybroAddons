/** @odoo-module */
import { useService } from "@web/core/utils/hooks";

import { Component, onWillStart, useState } from "@odoo/owl";

export class StockMoveDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.stockmoveData = useState({
            draft: 0,
            waiting: 0,
            assigned: 0,
            done: 0,
            count: 0,
            average_products: 0,
        });

        onWillStart(async () => {
            const data = await this.orm.call(
                "stock.move",
                "retrieve_inventory_dashboard",
            );
            Object.assign(this.stockmoveData, data);
        });
    }
    /**
     * This method clears the current search query and activates
     * the filters found in `filter_name` attribute from button pressed
     */
    setSearchContext(ev) {
        let filter_name = ev.currentTarget.getAttribute("filter_name");
        let filters = filter_name.split(',');
        let searchItems = this.env.searchModel.getSearchItems((item) => filters.includes(item.name));
        this.env.searchModel.query = [];
        for (const item of searchItems){
            this.env.searchModel.toggleSearchItem(item.id);
        }
    }
}

StockMoveDashboard.template = 'inventory_move_mini_dashboard.StockMoveDashboard';
