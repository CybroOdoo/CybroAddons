odoo.define('dynamic_link_snippet.dynamics', function (require)
{
   var PublicWidget = require('web.public.widget');
   var Dynamic = PublicWidget.Widget.extend({
         selector: '.dynamic_snippet_blogs',
         start: function () {
         /* Get the element with class 'iframes' */
         var iframesDiv = $(this.$el[0].children[0].children[0]);
         /* Clearing all the content in the iframe */
         iframesDiv.empty();
         if (this.$target[0].children[0].attributes[3]) {
         var url = this.$target[0].children[0].attributes[3].nodeValue
         /* Adding the iframe element to iframesDiv */
         var iframesStyle = '<iframe id=url_id width="100%" height="100%" src="' + url + '"></iframe>'
         iframesDiv.prepend(iframesStyle)
         }
         },
    });
   PublicWidget.registry.dynamic_snippet_blog_rec = Dynamic;
   return Dynamic;
});
