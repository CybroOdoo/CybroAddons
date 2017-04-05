openerp.pos_category_wise_receipt = function(instance){

    var module = instance.point_of_sale;
    var OrderlineParent = module.Orderline;
    var orderline_id = 1;
    console.log("12");

    module.Orderline = module.Orderline.extend({
        initialize: function(attr,options){
            this.pos = options.pos;

            this.order = options.order;

            this.product = options.product;

            this.price   = options.product.price;
            this.set_quantity(1);
            this.discount = 0;
            this.discountStr = '0';
            this.type = 'unit';
            this.selected = false;
            this.count = true;
            this.category_selected=true;
            this.id       = orderline_id++;

        },
        get_category: function(){

            var product = this.product.pos_categ_id[1];
            return (product ? this.product.pos_categ_id[1] : undefined) || 'UnCategorised Product';
        },
        get_category_id: function(){
            return this.product.pos_categ_id[0];
        },
        // selects or deselects this orderline
        set_selected: function(selected){

            this.selected = selected;
        },
        set_selected_product: function(selected){
            this.count = selected;
            this.trigger('change',this);
        },
        set_selected_category: function(selected){
            this.category_selected = selected;
            this.trigger('change',this);
        },
        is_selected_product: function(){
            return this.count;
        },
        is_selected_category: function(){
            return this.category_selected;
        },

    });

}

