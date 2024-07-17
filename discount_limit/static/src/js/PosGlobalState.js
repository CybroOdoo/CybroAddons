odoo.define('discount_limit.pos', function(require) {
 "use strict";
 var { PosGlobalState } = require('point_of_sale.models');
 const Registries = require('point_of_sale.Registries');
//loading model
 const ProductPosGlobalState = (PosGlobalState) => class ProductPosGlobalState extends PosGlobalState {
     async _processData(loadedData) {
         await super._processData(...arguments);
         this.product_template = loadedData['product.product'];
         this.pos_category = loadedData['pos.category'];
         this.hr_employee = loadedData['hr.employee'];
     }
 }
 Registries.Model.extend(PosGlobalState, ProductPosGlobalState);
});
