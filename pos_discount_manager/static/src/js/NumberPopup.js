odoo.define('pos_discount_manager.NumberPopup', function(require) {
    'use strict';

  const Registries = require('point_of_sale.Registries');
  const NumberPopup = require('point_of_sale.NumberPopup');

     const Managers = (NumberPopup) =>
        class extends NumberPopup {
     }
        NumberPopup.template = 'NumberPopupNumber';
  Registries.Component.extend(NumberPopup, Managers);
     return Managers;
});
