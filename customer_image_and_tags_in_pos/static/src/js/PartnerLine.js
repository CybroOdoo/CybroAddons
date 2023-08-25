/** @odoo-module **/
import PartnerLine from 'point_of_sale.PartnerLine';
import rpc from 'web.rpc';
import ajax from 'web.ajax';
import Registries from 'point_of_sale.Registries';

const PosPartnerLine = (PartnerLine) =>
    class extends PartnerLine {
        /**
        Add tag into props
        **/
        get highlight() {
            var self = this;
            var tags = []
            var customer_tag = self.props.partner.category_id
            this.env.pos.customer_tag.forEach(function(items){
                   customer_tag.forEach(function(item){
                       if(item == items["id"]){
                            tags.push(items.name)
                       }
                   });
            });
            this.props.tags = tags
        }
    }
Registries.Component.extend(PartnerLine, PosPartnerLine);
