odoo.define('advanced_loyalty_management.OrderLine', function (require) {
    "use strict";
    var models = require('point_of_sale.models');
    var _super_orderline = models.Orderline.prototype;

    models.Orderline = models.Orderline.extend({
//        To include a is_reward_line flag for reward lines, during initialization and JSON export
        initialize: function(attr, options) {
            _super_orderline.initialize.apply(this, arguments);
            if (options.extras && options.extras.is_reward_line) {
                this.is_reward_line = options.extras.is_reward_line;
            }
        },
        export_as_JSON: function() {
            var json = _super_orderline.export_as_JSON.apply(this, arguments);
            json.is_reward_line = this.is_reward_line || false;
            return json;
        },
    });
});
