/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
import { renderToElement } from "@web/core/utils/render";
    var get_featured_products = PublicWidget.Widget.extend({
        selector : '.featured_2',
        willStart: async function(){
            const data = await jsonrpc('/get_featured_products', {})
            this.$el.html(renderToElement('theme_diva.diva_index2_features', {
                  featured_products2: data.featured_products2,
                  currency_symbol: data.currency_symbol
            }))
        }
    });
PublicWidget.registry.get_featured_products = get_featured_products;
return get_featured_products;