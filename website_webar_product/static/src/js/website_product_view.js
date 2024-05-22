/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

//Extending publicWidget
publicWidget.registry.product_detail_view_3d = publicWidget.Widget.extend({
    selector: '.o_wsale_product_page',
    events: {
        'click .product_images':'_arViewBtn',
    },
//    Function to see the AR image of the product
    _arViewBtn:function (ev){
            var self = this;
            ev.preventDefault();
            if (this.$(ev.currentTarget).data('type') == "3d"){
                this.$('.o_carousel_product_outer').hide()
                this.$('#product_main').show()
                jsonrpc('/product/ar_image', {
                    'product_id': parseInt(ev.currentTarget.id),
                }).then(function(data) {
                self.data = data
                var ar_image = data['type'] === 'url' ? data['ar_url'] : data['local_url'];
                    const autoRotateAttribute = data['auto_rotate'] ? 'auto-rotate = ""' : '';
                    const placementAttribute = data['ar_placement']
                    const scaleAttribute = data['ar_scale'] ;
                self.$('#product_main').html(`<model-viewer id="model-viewer" src= ${ar_image}
                ar="" ar-scale= ${scaleAttribute}  camera-controls="" touch-action="pan-y" ar-placement= ${placementAttribute}
                alt="A 3D model of the product" xr-environment="" ${autoRotateAttribute}>
                    <button slot="ar-button" id="custom-ar-button" class="btn btn-primary">View in AR</button>
                </model-viewer>`)
                });
            }else{
                this.$('.o_carousel_product_outer').show()
                this.$('#product_main').hide()
            }
        },
});
export default publicWidget.registry.product_detail_view_3d;

