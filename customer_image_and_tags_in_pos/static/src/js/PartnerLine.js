/** @odoo-module **/
import { PartnerLine } from "@point_of_sale/app/screens/partner_list/partner_line/partner_line";
import { patch } from "@web/core/utils/patch";

patch(PartnerLine.prototype, {
    get highlight() {
        var self = this;
        var tags = []
        self.env.services.pos.customer_tag.forEach(function(items){
            var partner = items.partner_ids
            partner.forEach(function(item){
                if (self.props.partner.id == item){
                    tags.push(items.name)
                }
            });
        });
        this.props.partner['tags'] = tags
    },
});
