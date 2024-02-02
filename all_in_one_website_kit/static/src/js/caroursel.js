odoo.define('all_in_one_website_kit.carousel_dashboard', function(require){
    'use strict';
    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    Animation.registry.get_dashboard_carousel = Animation.Class.extend({
        /**
         * Represents an extended Animation class.
         * This class inherits properties and methods from the Animation class and allows additional
         * functionality to be added or overridden in the extended class.
         */
        selector : '.s_carousel_template',
        init: function() {
        /**
          Initialize the object using the parent class's constructor.
         */
            this._super.apply(this, arguments);
        },
        start: function(){
        // Implementation of the start method goes here
            var self = this;
            ajax.jsonRpc('/get_dashboard_carousel', 'call', {})
            .then(function (data) {
                if(data){
                    self.$target.empty().append(data);
                }
            });
        }
    });
});
