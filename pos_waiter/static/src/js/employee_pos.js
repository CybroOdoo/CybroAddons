odoo.define('waiter_performance_analysis.employee_pos', function (require) {
    "use strict";
    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var PopupWidget = require('point_of_sale.popups');
    var _t = core._t;
    var models = require('point_of_sale.models');

    models.load_models({
        model: 'hr.employee',
        fields: ['id', 'name'],
        domain: function(){ return [['is_a_waiter','=',true]]; },
        loaded: function (self, employee) {
            self.employee_name_by_id = {};
            for (var i = 0; i < employee.length; i++) {
                self.employee_name_by_id[employee[i].id] = employee[i];
            }
        }
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        export_as_JSON: function () {
            var json = _super_order.export_as_JSON.apply(this, arguments);
            json.order_waiter = this.order_waiter;
            json.employee_id = this.employee_id;
            return json;
        },
        init_from_JSON: function (json) {
            _super_order.init_from_JSON.apply(this, arguments);
            this.order_waiter = json.order_waiter;
            this.employee_id = json.employee_id;
            _super_order.init_from_JSON.call(this, json);
        }
    });

    var WaiterPopupWidget = PopupWidget.extend({
        template: 'WaiterPopupWidget',
        init: function (parent, options) {
            this.options = options || {};
            this._super(parent, _.extend({}, {
                size: "medium"
            }, this.options));
        },
        renderElement: function () {
            this._super();
            for (var employee in this.pos.employee_name_by_id) {
                $('#employee_select').append($("<option>" + this.pos.employee_name_by_id[employee].name + "</option>").attr("value", this.pos.employee_name_by_id[employee].name).attr("id", this.pos.employee_name_by_id[employee].id))
            }
        },
        click_confirm: function () {
            var employee_id = $("#employee_select :selected").attr('id');
            var employee_name = $("#employee_select :selected").text();
            var order = this.pos.get_order();
            order.order_waiter = employee_name;
            order.employee_id = employee_id;
            this.gui.close_popup();
        },

    });
    gui.define_popup({name: 'pos_no', widget: WaiterPopupWidget});

    var WaiterSelectionButton = screens.ActionButtonWidget.extend({
        template: 'WaiterSelectionButton',
        button_click: function () {
            var note = this.pos.get_order().order_waiter;
            this.gui.show_popup('pos_no', {'value': this.pos.get_order().order_waiter});
        }
    });

    screens.define_action_button({
        'name': 'pos_waiter_selection',
        'widget': WaiterSelectionButton,
        'condition': function(){
        return this.pos.config.waiter_configuration;
    }
    });
});

