/** @odoo-module **/
// Import necessary components and functionalities from Odoo libraries
import { jsonrpc } from "@web/core/network/rpc_service";
const { useRef, onWillStart, xml ,onMounted} = owl;
import { session } from "@web/session";
// Define the InfinitoRecentApps component

export default class InfinitoRecentApps extends owl.Component {
    // Setup method to initialize the component
    setup(){
        super.setup();
        this.ref = useRef('recentApps');
        onWillStart(this.willStart);
        onMounted(this.mounted)
    }
    // Method to execute logic before component starts
    async willStart(){
        // Retrieve recent apps data from the server
        await jsonrpc('/theme_studio/get_recent_apps', {
            method: 'call',
        }).then(data => this.recent_app = data);
    }
    // Getter method to access the recent apps data
    get recentApps(){
        return this.recent_app;
    }
    // Method executed after component is mounted
    mounted(){
        // Initialize drag functionality for recent apps tray
        this.dragElement(this.__owl__.refs.recentApps, 'x');
    }
}
// XML template for InfinitoRecentApps component
InfinitoRecentApps.template = xml`
<div class="recent-apps d-none" id="recentApps" t-ref="recentApps">
        <div class="icon-tray">
         <t t-foreach="recentApps" t-as="app" t-key="app">
            <a class="icon" t-attf-href="#menu_id={{app.app_id}}">
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