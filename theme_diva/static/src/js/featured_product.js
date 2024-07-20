/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
import { renderToFragment } from "@web/core/utils/render";
    var featured_product = PublicWidget.Widget.extend({
        selector : '.featured',
        willStart: async function(){
            const data = await jsonrpc('/get_featured_product', {})
            this.$el.html(renderToFragment('theme_diva.diva_index_features', {
                  featured_products1: data.featured_products1,
                  currency_symbol: data.currency_symbol
            }))
        }
    });
PublicWidget.registry.featured_product = featured_product;
return featured_product;
