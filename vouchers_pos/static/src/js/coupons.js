odoo.define("vouchers_pos.coupons", function (require) {
    "use strict";
    var core = require('web.core');
    var pos_screen = require('point_of_sale.screens');
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var pos_model = require('point_of_sale.models');
    var pos_popup = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');
    var models = pos_model.PosModel.prototype.models;
    var PosModelSuper = pos_model.PosModel;
    var OrderSuper = pos_model.Order;
    var rpc = require('web.rpc');
    var core = require('web.core');
    var _t = core._t;
    var utils = require('web.utils');
    var round_pr = utils.round_precision;

    function find_coupon(code, coupons, vouchers) {
        var coupon = [];
        for(var i in coupons){
            if (coupons[i]['code'] == code){
                coupon.push(coupons[i]);
            }
        }
        if(coupon.length > 0){
            for(var i in vouchers){
                if (vouchers[i]['id'] == coupon[0]['voucher'][0]){
                    coupon.push(vouchers[i]);
                    return coupon;
                }
            }
        }
        return false
    }

    function check_validity(coupon, applied_coupons, customer) {
        // checking it is already used or not
        for (var i in applied_coupons){
            if(applied_coupons[i]['coupon_pos'] == coupon[0]['code'] && applied_coupons[i]['partner_id'][0] == customer['id']){
                return applied_coupons[i];
            }
        }
        return false;
    }

    function check_expiry(start, end) {
        var today = moment().format('YYYY-MM-DD');
        if(start && end) {
            if (today < start || today > end)
                return false;
        }
        else if(start){
            if (today < start)
                return false;
        }
        else if(end){
            if (today > end)
                return false;
        }
        return true;
    }

    function get_coupon_product(products) {
        for (var i in products){
            if(products[i]['display_name'] == 'Gift-Coupon')
                return products[i]['id'];
        }
        return false;
    }

    // getting vouchers and coupons
    models.push(
        {
            model: 'gift.voucher.pos',
            fields: ['id', 'voucher_type', 'name', 'product_id', 'expiry_date', 'product_categ'],
            loaded: function (self, vouchers) {
                    self.vouchers = vouchers;
            },
        },{
            model: 'gift.coupon.pos',
            fields: ['id', 'name', 'code', 'voucher', 'start_date',
                'end_date', 'partner_id', 'limit', 'total_avail', 'voucher_val', 'type'],
            loaded: function (self, coupons) {
                self.coupons = coupons;
            },
        },
        {
            model: 'partner.coupon.pos',
            fields: ['partner_id', 'coupon_pos', 'number_pos'],
            loaded: function (self, applied_coupon) {
                self.applied_coupon = applied_coupon;
            },
        }
        );

    var VoucherWidget = pos_screen.ActionButtonWidget.extend({
        template:"VoucherWidget",
        init: function(parent) {
            return this._super(parent);
        },
        renderElement: function () {
            var self = this;
            this._super();
            this.$(".coupons").click(function () {
                self.gui.show_popup('coupon',{
                    'title': _t('Enter Your Coupon'),
                });
            });
        },
    });


    pos_screen.ProductScreenWidget.include({
        start: function(){
            this._super();
            this.coupons = new VoucherWidget(this,{});
            this.coupons.replace(this.$('.placeholder-VoucherWidget'));
        },
    });

    var CouponPopupWidget = pos_popup.extend({
        template: 'CouponPopupWidget',
        init: function(parent) {
            this.coupon_product = null;
            return this._super(parent);
        },
        show: function(options){
            options = options || {};
            this._super(options);
            if(!this.coupon_product)
                this.coupon_product = get_coupon_product(this.pos.db.product_by_id);
            this.flag = true;
            this.coupon_status = [];
            this.renderElement();
            this.$('input').focus();
        },
        click_confirm: function(){
            var value = this.$('input').val();
            this.gui.close_popup();
            if( this.options.confirm ){
                this.options.confirm.call(this,value);
            }
        },
        renderElement: function () {
            this._super();
            var self = this;

            this.$(".validate_coupon").click(function () {
                // checking the code entered
                var current_order = self.pos.get_order();
                var coupon = $(".coupon_code").val();
                if (current_order.orderlines.models.length == 0){
                    self.gui.show_popup('error',{
                        'title': _t('No products !'),
                        'body': _t('You cannot apply coupon without products.'),
                    });
                }
                else if(coupon){
                    if(self.pos.get_client()){
                        var customer = self.pos.get_client();
                        var coupon_res = find_coupon(coupon, self.pos.coupons, self.pos.vouchers);
                        var flag = true;
                        // is there a coupon with this code which has balance above zero
                        if(coupon_res && coupon_res[0]['total_avail'] > 0){
                            var applied_coupons = self.pos.applied_coupon;
                            // checking coupon status
                            var coupon_stat = check_validity(coupon_res, applied_coupons, customer);
                            // if this coupon was for a particular customer and is not used already
                            if(coupon_res[0]['partner_id'] && coupon_res[0]['partner_id'][0] != customer['id']){
                                flag = false;
                            }
                            var today = moment().format('YYYY-MM-DD');
                            // checking coupon balance and expiry
                            if(flag && coupon_stat && coupon_stat.number_pos < coupon_res[0]['limit'] &&
                                today <= coupon_res[1]['expiry_date']){
                                // checking coupon validity
                                flag = check_expiry(coupon_res[0]['start_date'], coupon_res[0]['end_date']);
                            }
                            // this customer has not used this coupon yet
                            else if(flag && !coupon_stat && today <= coupon_res[1]['expiry_date']){
                                flag = check_expiry(coupon_res[0]['start_date'], coupon_res[0]['end_date']);
                            }
                            else{
                                flag = false;
                                $(".coupon_status_p").text("Unable to apply coupon. Check coupon validity.!");
                            }
                        }
                        else{
                            flag = false;
                            $(".coupon_status_p").text("Invalid code or no coupons left. Please try again !!");
                        }
                        if(flag){
                            var val = coupon_res[0]['type'] == 'fixed' ?
                                coupon_res[0]['voucher_val'] : coupon_res[0]['voucher_val'] + "%";
                            var obj = $(".coupon_status_p").text("Voucher value is : "+val+" \n" +
                                " Do you want to proceed ? \n This operation cannot be reversed.");
                            obj.html(obj.html().replace(/\n/g,'<br/>'));
                            var order = self.pos.get_order();
                            order.set_coupon_value(coupon_res[0]);
                        }
                        self.flag = flag;
                        if(flag){
                           $(".confirm-coupon").css("display", "block");
                        }
                        else{
                            var ob = $(".coupon_status_p").text("Invalid code or no coupons left. \nPlease check coupon validity.\n" +
                                "or check whether the coupon usage is limited to a particular customer.");
                            ob.html(ob.html().replace(/\n/g,'<br/>'));
                        }
                    }
                    else{
                        $(".coupon_status_p").text("Please select a customer !!");
                    }
                }
            });
            this.$(".confirm-coupon").click(function () {
                // verifying and applying coupon
                if(self.flag){
                    var order = self.pos.get_order();
                    var lines = order ? order.orderlines : false;
                    if(order.coupon){
                        self.gui.close_popup();
                        self.gui.show_popup('error',{
                            'title': _t('Unable to apply Coupon !'),
                            'body': _t('Either coupon is already applied or you have not selected any products.'),
                        });
                    }
                    else{
                        if(lines.models.length > 0 && order.check_voucher_validy()) {
                            var product = self.pos.db.get_product_by_id(self.coupon_product);
                            var price = -1;
                            if (order.coupon_status['type'] == 'fixed') {
                                price *= order.coupon_status['voucher_val'];
                            }
                            if (order.coupon_status['type'] == 'percentage') {
                                price *= order.get_total_with_tax() * order.coupon_status['voucher_val'] / 100;
                            }
                            if ((order.get_total_with_tax - price) <= 0) {
                                self.gui.close_popup();
                                self.gui.show_popup('error', {
                                    'title': _t('Unable to apply Coupon !'),
                                    'body': _t('Coupon amount is too large to apply. The total amount cannot be negative'),
                                });
                            }
                            else{
                                order.add_product(product, {quantity: 1, price: price});
                                order.coupon_applied();
                                // updating coupon balance after applying coupon
                                var client = self.pos.get_client();
                                var temp = {
                                    'partner_id': client['id'],
                                    'coupon_pos': order.coupon_status['code'],
                                };
                                rpc.query({
                                    model: 'partner.coupon.pos',
                                    method: 'update_history',
                                    args: ['', temp]
                                }).then(function (result) {
                                    var applied = self.pos.applied_coupon;
                                    var already_used = false;
                                    for (var j in applied) {
                                        if (applied[j]['partner_id'][0] == client['id'] &&
                                            applied[j]['coupon_pos'] == order.coupon_status['code']) {
                                            applied[j]['number_pos'] += 1;
                                            already_used = true;
                                            break;
                                        }
                                    }
                                    if (!already_used) {
                                        console.log("already_used")
                                        var temp = {
                                            'partner_id': [client['id'], client['name']],
                                            'number_pos': 1,
                                            'coupon_pos': order.coupon_status['code']
                                        };
                                        self.pos.applied_coupon.push(temp);
                                        self.gui.close_popup();
                                    }
                                });
                            }
                        }
                        else{
                            self.gui.close_popup();
                            self.gui.show_popup('error',{
                                'title': _t('Unable to apply Coupon !'),
                                'body': _t('This coupon is not applicable on the products or category you have selected !'),
                            });
                        }
                    }
                }
                else{
                    self.gui.close_popup();
                    self.gui.show_popup('error',{
                        'title': _t('Unable to apply Coupon !'),
                        'body': _t('Invalid Code or no Coupons left !'),
                    });
                }
            });
        },
    });
    gui.define_popup({name:'coupon', widget: CouponPopupWidget});

    // PosModel is extended to store vouchers, & coupon details
    pos_model.PosModel = pos_model.PosModel.extend({
        initialize: function(session, attributes) {
            PosModelSuper.prototype.initialize.call(this, session, attributes)
            this.vouchers = [''];
            this.coupons = [];
            this.applied_coupon = [];
        },
    });

    pos_model.Order = pos_model.Order.extend({
        initialize: function(attributes,options){
            this.coupon = false;
            this.coupon_status = [];
            return OrderSuper.prototype.initialize.call(this, attributes,options);;
        },
        set_coupon_value: function (coupon) {
            this.coupon_status = coupon;
            return;
        },
        coupon_applied: function () {
            this.coupon = true;
            this.export_as_JSON();
            return;
        },
        check_voucher_validy: function () {
            var self = this;
            var order = self.pos.get_order();
            var vouchers = self.pos.vouchers;
            var voucher = null;
            for (var i in vouchers){
                if(vouchers[i]['id'] == self.coupon_status.voucher[0]){
                    voucher = vouchers[i];
                    break;
                }
            }
            var flag ;
            if(voucher){
                switch(voucher.voucher_type){
                    case 'product': {
                        var lines = order.orderlines.models;
                        var products = {};
                        for (var p in lines){
                            products[lines[p].product.id] = null;
                        }
                        if(voucher.product_id[0] in products){
                            flag = true;
                        }
                        else
                            flag = false;
                        break;
                    }
                    case 'category':{
                        var lines = order.orderlines.models;
                        var category = {};
                        for (var p in lines){
                            if(lines[p].product.pos_categ_id){
                                category[lines[p].product.pos_categ_id[0]] = null;
                            }
                        }
                        if(voucher.product_categ[0] in category){
                            flag = true;
                        }
                        else
                            flag = false;
                        break;
                    }
                    case 'all': flag = true; break;
                    default: break;
                }
            }
            return flag;
        },
        export_as_JSON: function () {
            var self = OrderSuper.prototype.export_as_JSON.call(this);
            self.coupon = this.coupon;
            self.coupon_status = this.coupon_status;
            return self;
        },
        init_from_JSON: function(json) {
            this.coupon = json.coupon;
            this.coupon_status = json.coupon_status;
            OrderSuper.prototype.init_from_JSON.call(this, json);
        },
        get_total_without_tax: function() {
            var res = OrderSuper.prototype.get_total_without_tax.call(this);
            var final_res = round_pr(this.orderlines.reduce((function(sum, orderLine) {
                return sum + (orderLine.get_unit_price() * orderLine.get_quantity() * (1.0 - (orderLine.get_discount() / 100.0)));
            }), 0), this.pos.currency.rounding);
            return final_res;
        },
    });
});