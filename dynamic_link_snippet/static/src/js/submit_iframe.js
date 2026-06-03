/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.dynamic_snippet_blogs = publicWidget.Widget.extend({
    selector: '.dynamic_snippet_blogs',

    /**
     * @override
     */
    start: function () {
        var self = this;
        // Search for the URL in multiple potential locations for robustness
        var url = this.el.getAttribute('url') || this.el.dataset.url || 
                  this.$('.external-link').attr('url') || this.$('.external-link').data('url') ||
                  this.$('.iframes').attr('url') || this.$('.iframes').data('url');

        var iframesDiv = this.el.querySelector('.iframes');
        if (iframesDiv) {
            iframesDiv.innerHTML = '';
            if (url) {
                var iframe = document.createElement('iframe');
                iframe.id = 'url_id';
                iframe.style.width = '100%';
                iframe.style.height = '100%';
                iframe.src = url;
                iframe.setAttribute('frameborder', '0');
                iframesDiv.appendChild(iframe);
            }
        }
        return this._super.apply(this, arguments);
    },
});
