/** @odoo-module */
import { renderToElement } from "@web/core/utils/render";
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.get_property_list = publicWidget.Widget.extend({
    selector: '.main_section_levelo',
    async willStart() {
        const result = await jsonrpc('/get_property_list', {});
        if (result && result.properties && result.properties.length > 0) {
            const properties = result.properties || [];
            const categorized = {
                all: properties,
                apartment: properties.filter(p => p.property_type === 'apartment'),
                villa: properties.filter(p => p.property_type === 'villa'),
                studio: properties.filter(p => p.property_type === 'studio'),
                house: properties.filter(p => p.property_type === 'house'),
                office: properties.filter(p => p.property_type === 'office'),
            };
            this.$target.empty().html(renderToElement('theme_livelo.property_list_data', { 
                result: result,
                categorized: categorized
            }));
            this.$el.find('.css_non_editable_mode_hidden').css('display', 'none');
        }
    },
});

