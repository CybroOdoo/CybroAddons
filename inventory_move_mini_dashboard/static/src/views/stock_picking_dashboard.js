/** @odoo-module */
import { useService } from "@web/core/utils/hooks";

import { Component, onWillStart, useState } from "@odoo/owl";

export class StockPickingDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.stockpickingData = useState({
            draft: 0,
            waiting: 0,
            assigned: 0,
            done: 0,
            receipts: 0,
            outgoing: 0,
            internal: 0,
            cancel: 0,
        });

        onWillStart(async () => {
            const data = await this.orm.call(
                "stock.picking",
                "stock_picking_dashboard",
            );
            Object.assign(this.stockpickingData, data);
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
StockPickingDashboard.template = 'inventory_move_mini_dashboard.StockPickingDashboard';
