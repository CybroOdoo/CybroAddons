/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
import { renderToElement } from "@web/core/utils/render";
//Extending publicwidget for diva main product snippet
     var get_main_product = PublicWidget.Widget.extend({
        selector : '.main_product',
        willStart: async  function(){
            const data = await jsonrpc('/get_main_product', {})
            this.$el.html(renderToElement('theme_diva.diva_index_main_product', {
                  main_products: data.main_products,
            }))
        }
    });
PublicWidget.registry.get_main_product = get_main_product;
return get_main_product;
