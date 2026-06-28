/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

var Dynamic = publicWidget.Widget.extend({
    selector: '.dynamic_snippet_blogs',

    start: function() {
        /* Get the element with class 'iframes' */
        var iframesDiv = $(this.$el[0].children[0].children[0]);
        /* Clearing all the content in the iframe */
        iframesDiv.empty();
        if (this.$target[0].children[0].attributes[3]) {
            var url = this.$target[0].children[0].attributes[3].nodeValue
            /* Adding the iframe element to iframesDiv */
            var iframesStyle = '<iframe id=url_id width="100%" height="100%" src="' + url + '"></iframe>'
            console.log("url",url)
            console.log("iframesStyle",iframesStyle)
            iframesDiv.prepend(iframesStyle)
        }
    }

});
publicWidget.registry.dynamic_snippet_blogs = Dynamic;
return Dynamic;