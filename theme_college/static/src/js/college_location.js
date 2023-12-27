/** @odoo-module **/

import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";

    //    Defines a new animation class called get_product_tab by extending Animation.Class.
    //    This class is used to perform an animation when selecting elements with the
    //    class .college_location_class.
publicWidget.registry.CollegeLocation = animations.Animation.extend({
    selector : '.college_location_class',
    start() {
        var self = this;
        jsonrpc('/get_college_locations', {}).then(function (data){
            if(data){
                self.$target.empty().append(data);
            }
        })
    }
});
