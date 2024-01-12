odoo.define('website_quotation_template.dynamic', function (require) {
// Import required modules
var PublicWidget = require('web.public.widget');
var ajax = require('web.ajax');
var core = require('web.core');
var QWeb = core.qweb;
   /**
     * Website Quotation Template Dynamic Widget.
     * This widget fetches quotation templates data from the server and renders them on the website.
     */
var Dynamic = PublicWidget.Widget.extend({
   selector: '.dynamic_snippet_blog',
       start: function () {
           var self = this;
           // Fetch quotation templates data using JSON-RPC
            ajax.jsonRpc("/quotation_template", 'call', {
                     })
            .then(function (data) {
              // Render the templates using QWeb template 'ShowTemplate'
              self.$el.find('.dynamic_snippet_template').html(QWeb.render
              ('ShowTemplate' , {
              template:data
                }));
            });
       },
   });
   // Register the widget with the PublicWidget registry
   PublicWidget.registry.website_quotation_template_cybrosys = Dynamic;
   return Dynamic;
});
