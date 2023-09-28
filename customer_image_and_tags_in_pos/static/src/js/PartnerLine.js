/** @odoo-module **/
import PartnerLine from 'point_of_sale.PartnerLine';
import Registries from 'point_of_sale.Registries';

const PosPartnerLine = (PartnerLine) =>
    class extends PartnerLine {
        /**
        Add tag into props
        **/
        get highlight() {
            var self = this;
            var tags = []
            this.env.pos.customer_tag.forEach(function(items){
                var partner = items.partner_ids
                partner.forEach(function(item){
                    if (self.props.partner.id == item){
                        tags.push(items.name)
                    }
                });
            });
            this.props.partner['tags'] = tags
        }
    }
Registries.Component.extend(PartnerLine, PosPartnerLine);