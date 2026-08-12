/** @odoo-module */
import { ListRenderer } from "@web/views/list/list_renderer";
const { onWillStart, useState, useSubEnv } = owl;
export class SaleOrderLineCompareListRenderer extends ListRenderer {
    setup() {
        super.setup();
        this.highestFields = useState({
                highest_price_ids: [],
                highest_price_unit_ids: [],
        });
        onWillStart(async () => {
            await this.updateHighestFields();
        });
        const defaultOnClickViewButton = this.env.onClickViewButton;
        useSubEnv({
            onClickViewButton: async (params) => {
                await defaultOnClickViewButton(params);
                await this.updateHighestFields();
            }
        });
    }

    async updateHighestFields() {
        [this.highestFields.highest_price_ids,
         this.highestFields.highest_price_unit_ids] = await this.props.list.model.orm.call(
            "sale.order",
            "get_tender_best_lines",
            [this.props.list.context.sale_order_id || this.props.list.context.active_id],
            { context: this.props.list.context }
        );
    }

    getCellClass(column, record) {
        //to highlight the lines having highest price and unit price
        let classNames = super.getCellClass(...arguments);
        const customClassNames = [];
        if (column.name === "price_subtotal" && this.highestFields.highest_price_ids.includes(record.resId)) {
            customClassNames.push("text-success"); // Changed to warning (orange/yellow) for highest prices
        }
        if (column.name === "price_unit" && this.highestFields.highest_price_unit_ids.includes(record.resId)) {
            customClassNames.push("text-success"); // Changed to warning for highest prices
        }
        return classNames.concat(" ", customClassNames.join(" "));
    }
}


