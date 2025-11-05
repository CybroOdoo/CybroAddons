odoo.define('pos_product_category_filter.pos_product_category_filter', function (require) {
    "use strict";
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var PosDB = require('point_of_sale.DB');
    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var Widget = require('web.Widget');
    var QWeb = core.qweb;

    var model1 = {
           model:  'pos.category',
            fields: ['id','name','parent_id','child_id','image'],
            domain: null,
            loaded: function(self, categories){
                for(var i = 0, len =  categories.length; i < len; i++){
                    categories[i].available = false;
                    for(var j = 0, jlen =  self.config.available_categ.length; j < jlen; j++){
                        if(categories[i].id == self.config.available_categ[j]){
                           categories[i].available = true;
                        }
                    }
                }
                self.db.add_categories(categories);
            },
    }

    for(var i=0; i< models.PosModel.prototype.models.length; i++){
        var model = models.PosModel.prototype.models[i];
        if(model.model === 'pos.category'){
            models.PosModel.prototype.models[i] = model1;
        }
    }

    PosDB.include({
        add_categories: function(categories){
            var self = this;
            if(!this.category_by_id[this.root_category_id]){
                this.category_by_id[this.root_category_id] = {
                    id : this.root_category_id,
                    name : 'Root',
                };
            }
            for(var i=0, len = categories.length; i < len; i++){
                if(categories[i].available === true){
                    categories[i].parent_id = 0;
                }
            }
            for(var i=0, len = categories.length; i < len; i++){
                this.category_by_id[categories[i].id] = categories[i];
            }
            for(var i=0, len = categories.length; i < len; i++){

                var cat = categories[i];
                var parent_id = cat.parent_id[0] || this.root_category_id;
                this.category_parent[cat.id] = cat.parent_id[0];
                if(!this.category_childs[parent_id]){
                    this.category_childs[parent_id] = [];
                }
                this.category_childs[parent_id].push(cat.id);
            }
            function make_ancestors(cat_id, ancestors){
                self.category_ancestors[cat_id] = ancestors;
                ancestors = ancestors.slice(0);
                ancestors.push(cat_id);
                var childs = self.category_childs[cat_id] || [];
                for(var i=0, len = childs.length; i < len; i++){
                    make_ancestors(childs[i], ancestors);
                }
            }
            make_ancestors(this.root_category_id, []);

        },

        add_products: function(products){
            console.log(this.category_by_id);
            var stored_categories = this.product_by_category_id;
            for(var i = 0, len = products.length; i < len; i++){
                var ancestor_ids = this.get_category_ancestors_ids(products[i].pos_categ_id[0]);
                products[i].pos_categ_ancestors = ancestor_ids;
            }
            for(var i = 0, len = products.length; i < len; i++){
                products[i].available = false;
                var category = this.get_category_by_id(products[i].pos_categ_id[0]);
                if(category && category.available == true){
                    products[i].available = true;
                }else{
                    if(products[i].pos_categ_ancestors){
                        for(var j = 0, jlen = products[i].pos_categ_ancestors.length; j < jlen; j++){
                            var temp_categ = this.get_category_by_id(products[i].pos_categ_ancestors[j])
                            if(temp_categ != 0 && temp_categ.available == true){
                                products[i].available = true;
                            }
                        }
                    }
                }
            }
            if(!products instanceof Array){
                products = [products];
            }
            for(var i = 0, len = products.length; i < len; i++){
                var product = products[i];
                var search_string = this._product_search_string(product);
                var categ_id = product.pos_categ_id ? product.pos_categ_id[0] : this.root_category_id;
                product.product_tmpl_id = product.product_tmpl_id[0];
                if(!stored_categories[categ_id]){
                    stored_categories[categ_id] = [];
                }
                stored_categories[categ_id].push(product.id);
                if(this.category_search_string[categ_id] === undefined){
                    this.category_search_string[categ_id] = '';
                }
                this.category_search_string[categ_id] += search_string;
                var ancestors = this.get_category_ancestors_ids(categ_id) || [];
                for(var j = 0, jlen = ancestors.length; j < jlen; j++){
                    var ancestor = ancestors[j];
                    if(! stored_categories[ancestor]){
                        stored_categories[ancestor] = [];
                    }
                    stored_categories[ancestor].push(product.id);

                    if( this.category_search_string[ancestor] === undefined){
                        this.category_search_string[ancestor] = '';
                    }
                    this.category_search_string[ancestor] += search_string;
                }
                this.product_by_id[product.id] = product;
                if(product.barcode){
                    this.product_by_barcode[product.barcode] = product;
                }
            }
        },
    });

    screens.ProductCategoriesWidget.include({
        renderElement: function(){
            var db = this.pos.db;
            var self = this;
            var el_str  = QWeb.render(this.template, {widget: this});
            var el_node = document.createElement('div');

            el_node.innerHTML = el_str;
            el_node = el_node.childNodes[1];

            if(this.el && this.el.parentNode){
                this.el.parentNode.replaceChild(el_node,this.el);
            }

            this.el = el_node;

            var withpics = this.pos.config.iface_display_categ_images;

            var list_container = el_node.querySelector('.category-list');
            if (list_container) {
                if (!withpics) {
                    list_container.classList.add('simple');
                } else {
                    list_container.classList.remove('simple');
                }
                for(var i = 0, len = this.subcategories.length; i < len; i++){
                    if(this.subcategories[i].available == true){
                        list_container.appendChild(this.render_category(this.subcategories[i],withpics));
                    }else{
                        var ancestor_ids = db.get_category_ancestors_ids(this.subcategories[i].id)
                        for(var j = 0, jlen = ancestor_ids.length; j < jlen; j++){
                            if(ancestor_ids[j] != 0){
                                var ancestor = db.get_category_by_id(ancestor_ids[j])
                                if(ancestor.available == true){
                                    list_container.appendChild(this.render_category(this.subcategories[i],withpics));
                                }
                            }
                        }
                    }

                }
            }
            var buttons = el_node.querySelectorAll('.js-category-switch');
            for(var i = 0; i < buttons.length; i++){
                buttons[i].addEventListener('click',this.switch_category_handler);
            }
            var products = this.pos.db.get_product_by_category(this.category.id);
            var available_products = [];
            for(var i = 0, len = products.length; i < len; i++){
                if(products[i].available == true){
                    available_products.push(products[i]);
                }
            }
            this.product_list_widget.set_product_list(available_products);
            
            this.el.querySelector('.searchbox input').addEventListener('keypress',this.search_handler);

            this.el.querySelector('.searchbox input').addEventListener('keydown',this.search_handler);

            this.el.querySelector('.search-clear').addEventListener('click',this.clear_search_handler);

            if(this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard){
                this.chrome.widget.keyboard.connect($(this.el.querySelector('.searchbox input')));
            }
        },

    });
});