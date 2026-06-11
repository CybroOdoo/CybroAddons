/** @odoo-module **/
import { registry } from "@web/core/registry";
import { TaxTotalsComponent } from "@account/components/tax_totals/tax_totals";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { formatMonetary } from "@web/views/fields/formatters";

patch(TaxTotalsComponent.prototype, {
    setup() {
        this.orm = useService("orm");
        super.setup();
    },
    formatData(props) {
        const formattedData = super.formatData(props);
        const recordId = props.record._values.id;
        let global_discount = parseFloat(props.record._values.global_discount) || 0.0;
    let global_discount_amount = 0.0;
    if (global_discount != 0){
     global_discount_amount = this.totals.total_amount_currency * (global_discount / 100);
        this.totals.global_discount = global_discount_amount;
    }

    if (props.record.resModel === "purchase.order") {
        this.updateRecord(recordId, {
            global_discount: global_discount
        });
    }
        let amount_total = (this.totals.total_amount_currency || 0) - global_discount_amount;
        this.totals.total_amount_currency = amount_total;
        const currencyFmtOpts = { currencyId: props.record.data.currency_id && props.record.data.currency_id[0] };
        this.totals.formatted_amount_total = formatMonetary(amount_total, currencyFmtOpts);
        return formattedData;
    },

    async updateRecord(recordId, updateData) {
        if (recordId) {
                await this.orm.write("purchase.order", [recordId], updateData);
    }
    }
});
