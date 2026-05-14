/** @odoo-module */
import { useService } from "@web/core/utils/hooks";

const { Component, onWillStart } = owl;

export class StockPickingDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        onWillStart(async () => {
            this.stockpickingData = await this.orm.call(
                "stock.picking",
                "stock_picking_dashboard",
            );
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
StockPickingDashboard.template = 'stock.StockPickingDashboard'
