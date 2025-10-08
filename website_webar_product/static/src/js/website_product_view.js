odoo.define('website_webar_product.product_ar_view', function (require) {
'use strict';
    /* Extend Public widget for AR Model on website.*/
    var publicWidget = require('web.public.widget');
    var rpc = require('web.rpc');
    publicWidget.registry.product_detail_view_3d = publicWidget.Widget.extend({
        selector: '.o_wsale_product_page',
        events: {
            'click .product_images':'_arViewBtn',
        },
        /* View AR Model On Product Page. */
         _arViewBtn:function (ev){
            var self = this;
            ev.preventDefault();
            if (this.$(ev.currentTarget).data('type') == "3d"){
                this.$('.o_carousel_product_outer').hide()
                this.$('#product_main').show()
                rpc.query({
                route: '/product/ar_image',
                params: {
                        product_id: parseInt(ev.currentTarget.id)
                        },
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
});
