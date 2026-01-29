/** @odoo-module **/
import ClientLine from 'point_of_sale.ClientLine';
import Registries from 'point_of_sale.Registries';
var models = require('point_of_sale.models');
/** To load field into pos **/
models.load_fields('res.partner', 'category_id');
/** To load model into pos **/
models.load_models([{
    model:  'res.partner.category',
    fields: ['id', 'name'],
    loaded: function(self, partner_category) {
        self.partner_category = partner_category;
    }
}]);
const PosPartnerLine = (ClientLine) =>
    class extends ClientLine {
        /** Add tag into props **/
        get highlight() {
            var self = this;
            var tags = []
            this.env.pos.partner_category.forEach(function(items){
                self.props.partner.category_id.forEach(function(item){
                    if(items.id == item){
                        tags.push(items.name)
                    }
                });
            });
            this.props.partner["tags"] = tags
        }
    }
Registries.Component.extend(ClientLine, PosPartnerLine);
