/** @odoo-module **/

const {useRef, useState, onWillStart, xml, onMounted} = owl;
import {rpc} from "@web/core/network/rpc";
import {useService, useBus} from "@web/core/utils/hooks";


export default class InfinitoRecentApps extends owl.Component {
    setup() {
        super.setup();
        this.menuService = useService('menu');
        this.ref = useRef('recentApps');
        this.state = useState({recent_app: []});
        onWillStart(this.willStart);
        onMounted(this.mounted);
        useBus(this.env.bus, 'INFINITO:RECENT_APPS_UPDATED', () => this.refresh());
    }

    async willStart() {
        this.state.recent_app = await this.fetchRecentApps();
    }

    async refresh() {
        this.state.recent_app = await this.fetchRecentApps();
    }

    fetchRecentApps() {
        // Retrieve recent apps data from the server
        return rpc('/theme_studio/get_recent_apps', {
            method: 'call',
        });
    }

    get recentApps() {
        return this.state.recent_app;
    }

    openApp(app) {
        const menu = this.menuService.getMenu(app.app_id);
        if (menu) {
            this.menuService.selectMenu(menu);
        }
    }

    mounted() {
        this.dragElement(this.__owl__.refs.recentApps, 'x');
    }
}
InfinitoRecentApps.template = xml`
<div class="recent-apps d-none" id="recentApps" t-ref="recentApps">
        <div class="icon-tray">
         <t t-foreach="recentApps" t-as="app" t-key="app.id">
            <a class="icon" t-on-click="() => this.openApp(app)">
              <div class="img_wrapper">
                <img t-if="app.type=='svg'" class="sidebar_img" t-attf-src="data:image/svg+xml;base64,{{app.icon}}" width="40px" height="40px"/>
                <img  t-if="app.type=='png'" class="sidebar_img" t-attf-src="data:image/png;base64,{{app.icon}}" width="40px" height="40px"/>
              </div>
              <span class="zoomIn" t-esc="app.name"/>
            </a>
         </t>
        </div>
      </div>
`;