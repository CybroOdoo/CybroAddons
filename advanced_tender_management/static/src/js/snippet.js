/** @odoo-module **/

import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from '@web/legacy/js/public/public_widget';
import { renderToFragment } from "@web/core/utils/render";

export function _chunk(array,size){
    const chunk_array=[]
    for (let i=0;i<array.length;i+=size){
        chunk_array.push(array.slice(i,i+size));
    }
    return chunk_array
}
publicWidget.registry.TenderManagementSnippet=publicWidget.Widget.extend({
        selector: '.dynamic_snippet_blog',
    	willStart: async function() {
        	var self = this;
        	await jsonrpc('/tender_management_snippet').then((data) => {
            	this.data = data;
        	});
    	},
    	start: function() {
        	var chunks = _chunk(this.data,1)
        	this.$el.find("div[id='carousel']").html(renderToFragment('advanced_tender_management.tender_snippet_carousel',{chunks}))
    	},
})