/** @odoo-module */
/**
 * This file is used to hide the set color to discuss model.
 */
import { DiscussContainer} from '@mail/components/discuss_container/discuss_container';
import { patch} from "@web/core/utils/patch";
var rpc = require('web.rpc');
const {onWillStart} = owl;
patch(DiscussContainer.prototype, 'discuss_container//  model: "mail",ord-patch', {
    setup() {
        this._super();
        onWillStart(async () => {
            await rpc.query({ //Call rpc to get color value.
            model: "res.config.settings",
            method: "get_color",
            args: [0],
        }).then(function(result) {
            if (result.background_color !== false){
                document.documentElement.style.setProperty("--background-color",result.background_color);
                }//set  discuss background color
            if (result.layout_color !== false){
                document.documentElement.style.setProperty("--layout-color",result.layout_color);
                }// set discuss layout color
            if (result.background_image !== false){
                document.documentElement.style.setProperty("--background-image",'url(data:image/png;base64,'+result.background_image+')');
            }// set discuss background image
        });
        });
    }
});