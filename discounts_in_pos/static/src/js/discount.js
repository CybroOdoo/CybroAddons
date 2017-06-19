odoo.define('discounts_in_pos', function (require) {
"use strict";

var screens = require('point_of_sale.screens');
var models = require('point_of_sale.models');
var core = require('web.core');
var formats = require('web.formats');
var utils = require('web.utils');

var QWeb = core.qweb;
var round_di = utils.round_decimals;
var round_pr = utils.round_precision;
    
screens.OrderWidget.include({

    set_value: function(val) {
    	var order = this.pos.get_order();
    	if (order.get_selected_orderline()) {
            var mode = this.numpad_state.get('mode');
            if( mode === 'quantity'){
                order.get_selected_orderline().set_quantity(val);
            }else if( mode === 'discount'){
                order.get_selected_orderline().set_discount(val);
            }else if( mode === 'price'){
                order.get_selected_orderline().set_unit_price(val);
            }
 // for the new button 'DiscFix'
            else if( mode === 'discount_fixed'){
                console.log(order)
                console.log(order.get_selected_orderline())
                order.get_selected_orderline().set_discount_fixed(val);
            }
            else if( mode === 'discount_total'){
                order.get_selected_orderline().set_discount_total(val);
                order.set_discount_total_order(val);
            }
            else if( mode === 'discount_percent'){
                order.get_selected_orderline().set_discount_percent(val);
                order.set_discount_percent_order(val);
            }
    	}
    },
//    ============================updates total discount(fixed and percentage) on order ==========================================
    update_summary: function(){
        var order = this.pos.get_order();
        if (!order.get_orderlines().length) {
            return;
        }
        var total     = order ? order.get_total_with_tax() : 0;
        var taxes     = order ? total - order.get_total_without_tax() : 0;
        var discount_total     = (order && order.get_discount_total_order() > 0) ? order.get_discount_total_order() : 0;
        var discount_percent   = (order && order.get_discount_percent_order() > 0) ? order.get_discount_percent_order() : 0;

        this.el.querySelector('.summary .total > .value').textContent = this.format_currency(total);
        this.el.querySelector('.summary .total .subentry .value').textContent = this.format_currency(taxes);

        if (discount_total > 0) {
        this.el.querySelector('.summary .total .subentry .value_discount_percent').textContent = "";
        this.el.querySelector('.summary .total .subentry .value_discount_total').textContent = "Discount(Total Fixed)" +this.format_currency(discount_total);
        }
        else {
        this.el.querySelector('.summary .total .subentry .value_discount_total').textContent = "";
        }
        if (discount_percent > 0) {
        this.el.querySelector('.summary .total .subentry .value_discount_total').textContent = "";
        this.el.querySelector('.summary .total .subentry .value_discount_percent').textContent = "Discount(Total %)" + discount_percent;
        }
        else {
        this.el.querySelector('.summary .total .subentry .value_discount_percent').textContent = "";
        }
    },
});
var OrderlineSuper = models.Orderline;
models.Orderline = models.Orderline.extend({
    initialize: function(attr,options){
        OrderlineSuper.prototype.initialize.call(this, attr,options);
        this.discount_fixed = 0;
        this.discount_total = 0;
        this.discount_percent = 0;
    },
    init_from_JSON: function(json) {
        OrderlineSuper.prototype.init_from_JSON.call(this, json);
        if(json.discount_fixed > 0) {
         this.set_discount_fixed(json.discount_fixed);
        }
        else {
         this.set_discount(json.discount);
        }
    },
    clone: function(){
        var orderline = OrderlineSuper.prototype.clone.call(this);
        orderline.discount_fixed = this.discount_fixed;
        return orderline;
    },
    set_discount: function(discount){
        OrderlineSuper.prototype.set_discount.call(this, discount);
        this.discount_fixed = 0.0;
        this.discount_total = 0.0;
        this.discount_percent = 0.0;
        this.discountStr = 'percentage';
        this.trigger('change',this);
    },
    set_discount_fixed: function(discount){
        this.discount_fixed = discount;
        this.discount = 0.0;
        this.discount_total = 0.0;
        this.discount_percent = 0.0;
        this.discountStr = 'fixed' ;
        this.trigger('change',this);
    },
    set_discount_total: function(discount){
        this.discount_total = discount;
        this.discount_percent = 0.0;
    },
    set_discount_percent: function(discount){
        var disc = Math.min(Math.max(parseFloat(discount) || 0, 0),100);
        this.discount_percent = disc;
        this.discount_total = 0.0;
    },
    get_discount_total: function(){
        return this.discount_total;
    },
    get_discount_percent: function(){
        return this.discount_percent;
    },
    get_discount_fixed: function(){
        return this.discount_fixed;
    },
    set_quantity: function(quantity){
        var order = this.pos.get_order();
    	if (order) {
    	    if(order.selected_orderline == undefined) {
    	            	    order.set_discount_total_order(0);
    	                    order.set_discount_percent_order(0);
    	    }
    	}

        this.order.assert_editable();
        if(quantity === 'remove'){
            this.order.remove_orderline(this);
            return;
        }else{
            var quant = parseFloat(quantity) || 0;

            var unit = this.get_unit();
            if(unit){
                if (unit.rounding) {
                    this.quantity    = round_pr(quant, unit.rounding);
                    var decimals = this.pos.dp['Product Unit of Measure'];
                    this.quantityStr = formats.format_value(round_di(this.quantity, decimals), { type: 'float', digits: [69, decimals]});
                } else {
                    this.quantity    = round_pr(quant, 1);
                    this.quantityStr = this.quantity.toFixed(0);
                }
            }else{
                this.quantity    = quant;
                this.quantityStr = '' + this.quantity;
            }
        }
        this.trigger('change',this);
    },
    can_be_merged_with: function(orderline){
        if( this.get_product().id !== orderline.get_product().id){    //only orderline of the same product can be merged
            return false;
        }else if(!this.get_unit() || !this.get_unit().groupable){
            return false;
        }else if(this.get_product_type() !== orderline.get_product_type()){
            return false;
        }else if(this.get_discount() > 0){             // we don't merge discounted orderlines
            return false;
        }else if(this.get_discount_fixed() > 0){             // we don't merge discounted orderlines
            return false;
        }else if(this.price !== orderline.price){
            return false;
        }else{
            return true;
        }
    },
    export_as_JSON: function() {
        return {
            qty: this.get_quantity(),
            price_unit: this.get_unit_price(),
            discount: this.get_discount(),
            discount_fixed: this.get_discount_fixed(),
            discount_total: this.get_discount_total(),
            discount_percent: this.get_discount_percent(),
            discountStr:this.get_discount_str(),
            product_id: this.get_product().id,
            tax_ids: [[6, false, _.map(this.get_applicable_taxes(), function(tax){ return tax.id; })]],
            id: this.id,
        };
    },
    export_for_printing: function(){
        return {
            quantity:           this.get_quantity(),
            unit_name:          this.get_unit().name,
            price:              this.get_unit_display_price(),
            discount:           this.get_discount(),
            discount_fixed:     this.get_discount_fixed(),
            discount_total:     this.get_discount_total(),
            discount_percent:     this.get_discount_percent(),
            discountStr:        this.get_discount_str(),
            product_name:       this.get_product().display_name,
            price_display :     this.get_display_price(),
            price_with_tax :    this.get_price_with_tax(),
            price_without_tax:  this.get_price_without_tax(),
            tax:                this.get_tax(),
            product_description:      this.get_product().description,
            product_description_sale: this.get_product().description_sale,
        };
    },
    get_base_price:    function(){
        var rounding = this.pos.currency.rounding;
        if(this.discount_fixed !== 0){
            return round_pr(this.get_unit_price() * this.get_quantity() - this.get_discount_fixed(), rounding);
            }

        return round_pr(this.get_unit_price() * this.get_quantity() * (1 - this.get_discount()/100), rounding);
    },
    get_all_prices: function(){

       if(this.discount_fixed > 0)
       {
            var price_unit = this.get_unit_price() * this.get_quantity() - this.get_discount_fixed();
        }
       else {
            var price_unit = this.get_unit_price() * (1.0 - (this.get_discount() / 100.0));
            }
        var taxtotal = 0;

        var product =  this.get_product();
        var taxes_ids = product.taxes_id;
        var taxes =  this.pos.taxes;
        var taxdetail = {};
        var product_taxes = [];

        _(taxes_ids).each(function(el){
            product_taxes.push(_.detect(taxes, function(t){
                return t.id === el;
            }));
        });

        var all_taxes = this.compute_all(product_taxes, price_unit, this.get_quantity(), this.pos.currency.rounding);
        _(all_taxes.taxes).each(function(tax) {
            taxtotal += tax.amount;
            taxdetail[tax.id] = tax.amount;
        });
        if(this.get_discount_fixed() != 0) {
            all_taxes.total_excluded = price_unit;
        }
        return {
            "priceWithTax": all_taxes.total_included,
            "priceWithoutTax": all_taxes.total_excluded,
            "tax": taxtotal,
            "taxDetails": taxdetail,
        };
    },
});
    
var OrderSuper = models.Order; 
models.Order = models.Order.extend({
    initialize: function(attributes,options){
        var order = OrderSuper.prototype.initialize.call(this, attributes,options);
        order.discount_total = 0;
        order.discount_percent = 0;
        return order;
    },
    init_from_JSON: function(json) {
        OrderSuper.prototype.init_from_JSON.call(this, json);
        this.discount_total = json.discount_total;
        this.discount_percent = json.discount_percent;
    },
    export_as_JSON: function() {
        var json_new = OrderSuper.prototype.export_as_JSON.call(this);
        json_new.discount_total = this.get_discount_total_order();
        json_new.discount_percent = this.get_discount_percent_order();
        return json_new;
    },
    export_for_printing: function(){
        var orderlines = [];
        var self = this;

        this.orderlines.each(function(orderline){
            orderlines.push(orderline.export_for_printing());
        });

        var paymentlines = [];
        this.paymentlines.each(function(paymentline){
            paymentlines.push(paymentline.export_for_printing());
        });
        var client  = this.get('client');
        var cashier = this.pos.cashier || this.pos.user;
        var company = this.pos.company;
        var shop    = this.pos.shop;
        var date    = new Date();

        function is_xml(subreceipt){
            return subreceipt ? (subreceipt.split('\n')[0].indexOf('<!DOCTYPE QWEB') >= 0) : false;
        }

        function render_xml(subreceipt){
            if (!is_xml(subreceipt)) {
                return subreceipt;
            } else {
                subreceipt = subreceipt.split('\n').slice(1).join('\n');
                var qweb = new QWeb2.Engine();
                    qweb.debug = core.debug;
                    qweb.default_dict = _.clone(QWeb.default_dict);
                    qweb.add_template('<templates><t t-name="subreceipt">'+subreceipt+'</t></templates>');

                return qweb.render('subreceipt',{'pos':self.pos,'widget':self.pos.chrome,'order':self, 'receipt': receipt}) ;
            }
        }

        var receipt = {
            orderlines: orderlines,
            paymentlines: paymentlines,
            subtotal: this.get_subtotal(),
            total_with_tax: this.get_total_with_tax(),
            total_without_tax: this.get_total_without_tax(),
            total_tax: this.get_total_tax(),
            total_paid: this.get_total_paid(),
            discount_total_fixed: this.get_discount_total_order(),
            discount_total_percent: this.get_discount_percent_order(),
            total_discount: this.get_total_discount(),
            tax_details: this.get_tax_details(),
            change: this.get_change(),
            name : this.get_name(),
            client: client ? client.name : null ,
            invoice_id: null,   //TODO
            cashier: cashier ? cashier.name : null,
            precision: {
                price: 2,
                money: 2,
                quantity: 3,
            },
            date: {
                year: date.getFullYear(),
                month: date.getMonth(),
                date: date.getDate(),       // day of the month
                day: date.getDay(),         // day of the week
                hour: date.getHours(),
                minute: date.getMinutes() ,
                isostring: date.toISOString(),
                localestring: date.toLocaleString(),
            },
            company:{
                email: company.email,
                website: company.website,
                company_registry: company.company_registry,
                contact_address: company.partner_id[1],
                vat: company.vat,
                name: company.name,
                phone: company.phone,
                logo:  this.pos.company_logo_base64,
            },
            shop:{
                name: shop.name,
            },
            currency: this.pos.currency,
        };

        if (is_xml(this.pos.config.receipt_header)){
            receipt.header = '';
            receipt.header_xml = render_xml(this.pos.config.receipt_header);
        } else {
            receipt.header = this.pos.config.receipt_header || '';
        }

        if (is_xml(this.pos.config.receipt_footer)){
            receipt.footer = '';
            receipt.footer_xml = render_xml(this.pos.config.receipt_footer);
        } else {
            receipt.footer = this.pos.config.receipt_footer || '';
        }

        return receipt;
    },
    set_discount_total_order: function(discount){
        this.discount_total = discount;
        this.discount_percent = 0;
        this.trigger('change',this);
    },
    get_discount_total_order: function(){
        return this.discount_total;
    },
    set_discount_percent_order: function(discount){
        var disc = Math.min(Math.max(parseFloat(discount) || 0, 0),100);
        this.discount_percent = disc;
        this.discount_total = 0.0;
        this.trigger('change',this);
    },
    get_discount_percent_order: function(){
        return this.discount_percent;
    },
    get_total_without_tax: function() {
        var total_fixed_disc = this.get_discount_total_order();
        var total_percent_disc = this.get_discount_percent_order();
        if (total_fixed_disc) {
            return round_pr(this.orderlines.reduce((function(sum, orderLine) {
            return sum + orderLine.get_price_without_tax();
        }), 0), this.pos.currency.rounding) - total_fixed_disc ;
         }
         if (total_percent_disc) {
            var temp = round_pr(this.orderlines.reduce((function(sum, orderLine) {
            return sum + orderLine.get_price_without_tax();
        }), 0), this.pos.currency.rounding);
            return (temp - (temp * total_percent_disc / 100))
         }
        return round_pr(this.orderlines.reduce((function(sum, orderLine) {
            return sum + orderLine.get_price_without_tax();
        }), 0), this.pos.currency.rounding);
    },
    get_total_discount: function() {
        var sum = OrderSuper.prototype.get_total_discount.call(this);
        sum = 0.0;
        var disc = 0.0;
        for (var i = 0; i < this.orderlines.length; i++) {
        var NewOrder = this.orderlines.models[i];
        disc +=  (NewOrder.quantity * NewOrder.price);
        if (NewOrder.discountStr == 'fixed') {
            sum +=  parseFloat(NewOrder.discount_fixed);
        }
        else {
            sum +=  NewOrder.quantity * NewOrder.price * (parseFloat(NewOrder.discount) / 100);
        }
        }
        if (this.discount_total) { sum +=  parseFloat(this.discount_total); }
        disc -= parseFloat(this.get_total_without_tax() + sum);
        if (this.discount_percent) { sum +=  disc; }

        return sum;

    },
});   
models.PosModel = models.PosModel.extend({
    push_and_invoice_order: function(order){
        var self = this;
        var invoiced = new $.Deferred();

        if(!order.get_client()){
            invoiced.reject({code:400, message:'Missing Customer', data:{}});
            return invoiced;
        }

        var order_id = this.db.add_order(order.export_as_JSON());

        this.flush_mutex.exec(function(){
            var done = new $.Deferred(); // holds the mutex

            // send the order to the server
            // we have a 30 seconds timeout on this push.
            // FIXME: if the server takes more than 30 seconds to accept the order,
            // the client will believe it wasn't successfully sent, and very bad
            // things will happen as a duplicate will be sent next time
            // so we must make sure the server detects and ignores duplicated orders

            var transfer = self._flush_orders([self.db.get_order(order_id)], {timeout:30000, to_invoice:true});

            transfer.fail(function(error){
                invoiced.reject(error);
                done.reject();
            });

            // on success, get the order id generated by the server
            transfer.pipe(function(order_server_id){

                // generate the pdf and download it
                self.chrome.do_action('discounts_in_pos.pos_invoice_report',{additional_context:{
                    active_ids:order_server_id,
                }});

                invoiced.resolve();
                done.resolve();
            });

            return done;

        });

        return invoiced;
    },
});
});


