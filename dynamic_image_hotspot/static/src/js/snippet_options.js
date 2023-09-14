odoo.define('dynamic_image_hotspot.snippets.options', function (require) {
'use strict';

    var options = require('web_editor.snippets.options');

    /**
    * JavaScript file defining a registry of options for the image hotspot feature in the web editor snippets.
    * The registry includes methods for toggling the image hotspot feature, setting the vertical and horizontal position
    of the hotspot, and setting the product template for the hotspot link.
    */
    options.registry.ImageHotspot = options.Class.extend({
        init: function () {
            this._super(...arguments);
            this.imageHotspot()
        },
        imageHotspot: function (previewMode, widgetValue) {
            if (widgetValue == 'on' && previewMode === false){
                this.$target[0].parentElement.style.position = "relative";
                const target = this.$target[0].parentElement;
                var document = this.ownerDocument;
                const newA = document.createElement('a');
                newA.className = 'popup-product';
                this.$target[0].after(newA);
            }
            if (widgetValue == 'off' && previewMode === false){
                const target = this.$target[0]
                if (target.nextElementSibling){
                    if(target.nextElementSibling.className == 'popup-product'){
                        target.nextElementSibling.remove();
                    }
                }
            }
        },
        async setVertical(previewMode, widgetValue) {
            let target = this.$target[0].nextElementSibling;
            let value = parseFloat(widgetValue);
            target.style.top = `${value}%`;
        },
        async setHorizontal(previewMode, widgetValue) {
            let target = this.$target[0].nextElementSibling;
            let value = parseFloat(widgetValue);
            target.style.left = `${value}%`;
        },
        async setProductTemplate(previewMode, widgetValue) {
            let target = this.$target[0].nextElementSibling;
            let value  = `/shop/${widgetValue}`
            target.setAttribute("href", value);
        }
    })
})
