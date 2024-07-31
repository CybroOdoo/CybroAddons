odoo.define('pos_custom_message.PosSession', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    const ProductScreen = require('point_of_sale.ProductScreen');

    models.load_models([
    {
        model: 'pos.custom.message',
        fields: ['message_type','title', 'message_text', 'execution_time', 'pos_config_ids'],
        domain: function(self){ return [['id','in',self.config.message_ids]]; },
        loaded: function(self,messages){
            self.pos_custom_message = {};
            for (var i = 0; i < messages.length; i++) {
                self.pos_custom_message[messages[i].id] = messages[i];
            }
        },
      },
    ],{'before': 'product.product'});
});
