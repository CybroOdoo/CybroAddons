import { Component, useProps, t } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";

export class BagPopup extends Component {
    static template = "carry_bag_pos.BagPopup";
    static components = { Dialog };
    props = useProps({
        title: t.string().optional(_t("Available Bags")),
        bags: t.array().optional([]),
        getPayload: t.function(),
        close: t.function(),
    });

    setup() {
        this.bags = this.props.bags.map(({ template, stock }) => ({
            template,
            imageUrl: template.getImageUrl(),
            // Quantity on hand as a plain number; empty when it is unknown.
            stock: stock === undefined ? "" : String(Math.round(stock * 100) / 100),
        }));
    }

    onClickBag(template) {
        this.props.getPayload(template);
        this.props.close();
    }
}
