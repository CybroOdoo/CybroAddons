odoo.define("pos_pricing.pricelist", function (require) {
    "use strict";
    var core = require('web.core');
    var pos_model = require('point_of_sale.models');
    var pos_chrome = require('point_of_sale.chrome')
    var models = pos_model.PosModel.prototype.models;
    var PosModelSuper = pos_model.PosModel;
    var OrderSuper = pos_model.Order;
    var OrderlineSuper = pos_model.Orderline;
    // get pos_pricelist_id of each customer
    for(var i=0; i<models.length; i++){
        var model=models[i];
        if(model.model === 'res.partner'){
             model.fields.push('pos_pricelist_id');
        }
    }
    // getting pricelists and pricelist items
    models.push(
        {
            model: 'pos.pricelist',
            fields: ['id', 'name'],
            loaded: function (self, pricelists) {
                for (var i in pricelists){
                    self.pricelists.push(pricelists[i]);
                }
            },
        },{
            model: 'pos.pricelist.items',
            fields: ['id', 'fixed_price', 'date_end', 'applied_on', 'min_quantity',
                'percent_price', 'date_start', 'product_tmpl_id', 'pos_pricelist_id', 'compute_price', 'categ_id'],
            loaded: function (self, pricelist_items) {
                self.pricelist_items = pricelist_items;
            },
        },
        {
            model: 'product.template',
            fields: ['id', 'categ_id'],
            loaded: function (self, category) {
                self.category = category;
            },
        }
        );
    // this function is used to get the id of selected pricelist using the name of pricelist
    function get_pricelist_id(pricelists, name){
        for(var i in pricelists){
            if(pricelists[i].name == name){
                return pricelists[i].id;
            }
        }
        return false;
    }
    // PosModel is extended to store category, pricelists and pricelist items on startup
    pos_model.PosModel = pos_model.PosModel.extend({
        initialize: function(session, attributes) {
            PosModelSuper.prototype.initialize.call(this, session, attributes)
            this.pricelist_items = [''];
            this.pricelists = [];
            this.category = [];
        },
    });

    pos_model.Order = pos_model.Order.extend({
        // case : selecting product after selecting client ----------------------------------
        // here we will get the pricelist selected, if there are any and apply the pricelist after validation
        add_product: function (product, options) {
            var self = this;
            var pricelist_id = get_pricelist_id(self.pos.pricelists, $("#pos_pricelist").val());
            OrderSuper.prototype.add_product.call(this, product, options);
            if (pricelist_id){
                if (this.pos.get_client()){
                    self.apply_pricelist(this.pos.get_client(), pricelist_id);
                }
            }
        },
        // this function returns the new price after checking the computation method of the pricelist item
        set_price: function (line, item) {
            var new_price = 0;
            switch (item.compute_price){
                case 'fixed': new_price = item.fixed_price; break;
                case 'percentage': new_price = line.product.price -(line.product.price * item.percent_price / 100); break;
            }
            return new_price;
        },
        /*this function is used to check the given id is present in the array or not,
        since the 'in' operator was not working properly*/
        find_pricelist_item: function (id, item_ids) {
            for (var j in item_ids){
                if(item_ids[j] == id){
                    return true;
                    break;
                }
            }
            return false;
        },

        // apply pricelist for this client----------------------------
        apply_pricelist: function(client, pricelist_id){
            var self = this;
            //  list of all pricelist items available
            var pricelist_items = self.pos.pricelist_items;
            var items = [];
            // getting this client's pricelist items from the complete list ---------------------------
            for (var i in pricelist_items){
                if(pricelist_items[i].pos_pricelist_id[0] == pricelist_id){
                    items.push(pricelist_items[i]);
                }
            }
//            checking the start date and end date of these items and selecting only the valid items
            pricelist_items = [];
            var today = moment().format('YYYY-MM-DD');
            for (var i in items){
                if(((items[i].date_start == false) || (items[i].date_start <= today))
                                        && ((items[i].date_end == false) || (items[i].date_end >= today)))
                                        {
                                            pricelist_items.push(items[i]);
                                        }
            }
            //    grouping the pricelist items based on applicability
            //    we are listing those products and categories which has a pricelist item for them
            //    for making the checkings easier
            var global_items = [];
            var category_items = [];
            var category_ids = [];
            var product_items = [];
            var product_ids = [];
            for(var i in pricelist_items){
                switch(pricelist_items[i].applied_on){
                case 'global': global_items.push(pricelist_items[i]); break;
                case 'product_category': category_items.push(pricelist_items[i]);
                    category_ids.push(pricelist_items[i].categ_id[0]) ; break;
                case 'product': product_items.push(pricelist_items[i]);
                    product_ids.push(pricelist_items[i].product_tmpl_id[0]) ;break;
                }
            }

            // getting current order ====================================================
            var order = self.pos.get_order();
            var lines = order ? order.get_orderlines() : null;

            //looping through each line
            for (var l in lines){
                // checking if this product has a valid pricelist rule set or not
                var product_item = self.find_pricelist_item(lines[l].product.product_tmpl_id, product_ids);
                // checking if this product's category has a valid pricelist rule set or not
                var categ_item = self.find_pricelist_item(lines[l].product.pos_categ_id[0], category_ids);
                var temp = -1;
                var new_price = lines[l].product.price;
//                checking if the product has any pricelist item set
                if(product_item){
                    for(var j in product_items){
                        if(product_items[j].product_tmpl_id[0] == lines[l].product.product_tmpl_id){
                           if(lines[l].quantity >= product_items[j].min_quantity){
                                if(temp < 0){
                                    temp = lines[l].quantity - product_items[j].min_quantity;
                                    new_price = self.set_price(lines[l], product_items[j]);
                                }
                                else if(temp > (lines[l].quantity - product_items[j].min_quantity) &&
                                    (lines[l].quantity - product_items[j].min_quantity) >= 0){
                                    temp = lines[l].quantity - product_items[j].min_quantity;
                                    new_price = self.set_price(lines[l], product_items[j]);
                                }
                            }
                        }
                    }
                    lines[l].set_unit_price(new_price);
                }
                else if(categ_item){
                    for(var j in category_items){
                        if(category_items[j].categ_id[0] == lines[l].product.pos_categ_id[0]){
                           if(lines[l].quantity >= category_items[j].min_quantity)
                            {
                                if(temp < 0){
                                    temp = lines[l].quantity - category_items[j].min_quantity;
                                    new_price = self.set_price(lines[l], category_items[j]);
                                }
                                else if(temp > (lines[l].quantity - category_items[j].min_quantity) &&
                                    (lines[l].quantity - category_items[j].min_quantity) >= 0){
                                    temp = lines[l].quantity - category_items[j].min_quantity;
                                    new_price = self.set_price(lines[l], category_items[j]);
                                }
                            }
                        }
                    }
                    lines[l].set_unit_price(new_price);
                }
//                if there are no rules set for product or category, we will check global pricelists
                else if(global_items.length > 0){
                    for(var j in global_items){
                        if(lines[l].quantity >= global_items[j].min_quantity)
                        {
                            if(temp < 0){
                                temp = lines[l].quantity - global_items[j].min_quantity;
                                new_price = self.set_price(lines[l], global_items[j]);
                            }
                            else if(temp > (lines[l].quantity - global_items[j].min_quantity) &&
                                (lines[l].quantity - global_items[j].min_quantity) >= 0){
                                temp = lines[l].quantity - global_items[j].min_quantity;
                                new_price = self.set_price(lines[l], global_items[j]);
                            }
                        }
                    }
                    lines[l].set_unit_price(new_price);
                }
//                else we set the original price
                else{
                    lines[l].set_unit_price(lines[l].product.price);
                }
            }
        },
        // this function will first set a customer for this order and then, it will apply the pricelist of this customer to
        // this order if there are any
        set_client: function(client){
            var self = this;
            var current_pricelist = document.getElementById('pos_pricelist');
            if(client){
                if (current_pricelist != null){
                    current_pricelist.value = client.pos_pricelist_id[1];
                }
                var order = self.pos.get_order();
                if (order) {
                    if (order.orderlines.length) {
                        self.apply_pricelist(client, client.pos_pricelist_id[0]);
                    }
                }
            }
            else if(current_pricelist){
               current_pricelist.value = '';
            }
            OrderSuper.prototype.set_client.call(this, client);
        },
    });

    pos_model.Orderline = pos_model.Orderline.extend({
        set_quantity: function(quantity){
            OrderlineSuper.prototype.set_quantity.call(this, quantity);
            var pricelist_id = get_pricelist_id(this.pos.pricelists, $("#pos_pricelist").val());
            if (this.order.get_client() && pricelist_id) {
                this.order.apply_pricelist(this.order.get_client(), pricelist_id);
            }
        },

    });
    
    pos_chrome.OrderSelectorWidget.include({
        renderElement: function(){
            var pos_pricelist = $("#pos_pricelist");
            this.pos_pricelist = false;
            if (pos_pricelist != null){
                this.pos_pricelist = pos_pricelist.val();
            }
            var self = this;
            this._super();
            this.$("#pos_pricelist").change(function () {
                self.pos.pos_pricelist = false;
                var order = self.pos.get_order();
                var client = order.get_client();
                var pricelist_id = get_pricelist_id(self.pos.pricelists, $("#pos_pricelist").val());
                if (client && pricelist_id){
                    order.apply_pricelist(client, pricelist_id);
                }
                else if (!client){
                    $("#pos_pricelist").val('')
                    alert("Unable to set pricelist. Please check customer...!!")
                }
            });
            this.$('.order-button.select-order').click(function(event){
                self.order_click_handler(event,$(this));
            });
            this.$('.neworder-button').click(function(event){
                self.neworder_click_handler(event,$(this));
            });
            this.$('.deleteorder-button').click(function(event){
                self.deleteorder_click_handler(event,$(this));
            });
        },
    });
});
