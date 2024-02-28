/** @odoo-module */
import { Discuss } from "@mail/core/common/discuss";
import { patch} from "@web/core/utils/patch";
import { jsonrpc } from "@web/core/network/rpc_service";
const { useRef } = owl;
import { onMounted } from "@odoo/owl";

patch(Discuss.prototype, {
    setup() {
     super.setup(...arguments);
        this.core = useRef("core");
        onMounted(async () => {
            var self = this;
            await jsonrpc('/select_color', {}).then(function(result) {
            if (result.background_color !== false){
                self.core.el.style.setProperty("--background-color",result.background_color
                );
                }//set  discuss background color
            if (result.layout_color !== false){
                document.documentElement.style.setProperty("--layout-color",result.layout_color);
                }// set discuss layout color
            if (result.background_image !== false){
                self.core.el.style.setProperty("background-image",'url(data:image/png;base64,'+result.background_image+')',"important");
            }// set discuss background image
        });
        });
    },
});
