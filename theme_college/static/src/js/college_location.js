odoo.define('theme_college.college_location', function(require){
    'use strict';

    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');

    //    Defines a new animation class called get_product_tab by extending Animation.Class.
    //    This class is used to perform an animation when selecting elements with the
    //    class .college_location_class.
    Animation.registry.get_product_tab = Animation.Class.extend({
        selector : '.college_location_class',
        start: function(){
            var self = this;
            ajax.jsonRpc('/get_college_locations', 'call', {})
            .then(function (data) {
                if(data){
                    self.$target.empty().append(data);
                }
            });
        }
    });
});