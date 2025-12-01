import { Discuss } from "@mail/core/public_web/discuss";
import { patch} from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
const { useRef } = owl;
import { onMounted } from "@odoo/owl";

patch(Discuss.prototype, {
    setup() {
     super.setup(...arguments);
        this.core = useRef("core");
        onMounted(async () => {
            var self = this;
            await rpc('/select_color', {}).then(function(result) {
                if (result.background_color !== false){
                    self.core.el.style.setProperty("background-color",result.background_color
                    );
                    }
                if (result.layout_color !== false){
                    document.documentElement.style.setProperty("layout-color",result.layout_color);
                }
                if (result.background_image !== false){
                    self.core.el.style.setProperty("background-image",'url(data:image/png;base64,'+result.background_image+')',"important");
                    self.core.el.style.setProperty("background-size", "cover", "important");
                    self.core.el.style.setProperty("background-position", "center", "important");
                    self.core.el.style.setProperty("background-repeat", "no-repeat", "important");
                }
            });
        });
    },
});
