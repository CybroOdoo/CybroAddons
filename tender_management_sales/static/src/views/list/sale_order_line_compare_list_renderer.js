import { onWillStart, proxy, useSubEnv } from "@odoo/owl";
import { ListRenderer } from "@web/views/list/list_renderer";

export class SaleOrderLineCompareListRenderer extends ListRenderer {
    setup() {
        super.setup();
        this.highestFields = proxy({
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
            },
        });
    }

    async updateHighestFields() {
        const orderId =
            this.props.list.context.sale_order_id ||
            this.props.list.context.active_id;
        [
            this.highestFields.highest_price_ids,
            this.highestFields.highest_price_unit_ids,
        ] = await this.props.list.model.orm.call(
            "sale.order",
            "get_tender_best_lines",
            [orderId],
            { context: this.props.list.context }
        );
    }

    getCellClass(column, record) {
        // Highlight lines with highest price and unit price
        let classNames = super.getCellClass(...arguments);
        const customClassNames = [];
        const isHighestPrice =
            this.highestFields.highest_price_ids.includes(record.resId);
        const isHighestUnitPrice =
            this.highestFields.highest_price_unit_ids.includes(record.resId);

        if (column.name === "price_subtotal" && isHighestPrice) {
            customClassNames.push("text-success");
        }
        if (column.name === "price_unit" && isHighestUnitPrice) {
            customClassNames.push("text-success");
        }
        return classNames.concat(" ", customClassNames.join(" "));
    }
}

