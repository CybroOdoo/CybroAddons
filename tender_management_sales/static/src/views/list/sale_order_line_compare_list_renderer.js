/** @odoo-module */

import { ListRenderer } from "@web/views/list/list_renderer";

const { onWillStart, useState, useSubEnv } = owl;

export class SaleOrderLineCompareListRenderer extends ListRenderer {
//    extending the list renderer
    setup() {
        super.setup();
        this.bestFields = useState({
                best_price_ids: [],
                best_price_unit_ids: [],
        });
        onWillStart(async () => {
            await this.updateBestFields();
        });
        const defaultOnClickViewButton = this.env.onClickViewButton;
        useSubEnv({
            onClickViewButton: async (params) => {
                await defaultOnClickViewButton(params);
                await this.updateBestFields();
            }
        });
    }

    async updateBestFields() {
        //to update the lines having best price and unit price
        [this.bestFields.best_price_ids,
         this.bestFields.best_price_unit_ids] = await this.props.list.model.orm.call(
            "sale.order",
            "get_tender_best_lines",
            [this.props.list.context.sale_order_id || this.props.list.context.active_id],
            { context: this.props.list.context }
        );
    }

    getCellClass(column, record) {
        //to highlight the lines having best price and unit price
        let classNames = super.getCellClass(...arguments);
        const customClassNames = [];
        if (column.name === "price_subtotal" && this.bestFields.best_price_ids.includes(record.resId)) {
        customClassNames.push("text-success");
        }
        if (column.name === "price_unit" && this.bestFields.best_price_unit_ids.includes(record.resId)) {
        customClassNames.push("text-success");
        }
        return classNames.concat(" ", customClassNames.join(" "));
    }
}
