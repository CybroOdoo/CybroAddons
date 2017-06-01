
openerp.customer_pos_pricelist = function (instance) {
    var module = instance.point_of_sale;
    customer_pos_pricelist_db(instance, module);
    customer_pos_pricelist_models(instance, module);
    customer_pos_pricelist_screens(instance, module);
    customer_pos_pricelist_widgets(instance, module);
};
