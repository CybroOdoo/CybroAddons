odoo.define('pos_sync_orders.SyncOrder', function(require) {
'use strict';
  const PosComponent = require('point_of_sale.PosComponent');
  const { useListener } = require("@web/core/utils/hooks");
  const Registries = require('point_of_sale.Registries');

  // extend PosComponent for adding the button.
  class SyncOrder extends PosComponent {
      setup() {
          super.setup();
          useListener('click', this.onClick);
      }
      // extend PosComponent for adding the button for sync all orders.
      //onclick function of syn all button
      async onClick() {
           const { confirmed } = await this.showPopup('ConfirmPopup', {
                title: ('Sync All'),
                body:('Sync all confirmed orders.'),
                });
                // sync all orders to backend
                if (confirmed){
                     await this.env.pos.push_orders();
                }
           }
      }
  SyncOrder.template = 'SyncOrder';
  Registries.Component.add(SyncOrder);
  return SyncOrder;
});