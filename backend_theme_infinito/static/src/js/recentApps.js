/** @odoo-module **/
import ajax from 'web.ajax';
const { useRef } = owl.hooks;
import session from 'web.session';
export default class InfinitoRecentApps extends owl.Component {
    setup(){
        super.setup();
        this.ref = useRef('recentApps');
    }
    async willStart(){
        await ajax.jsonRpc('/theme_studio/get_recent_apps', 'call', {})
        .then((data) => {
            this.recent_app = data;
        });
    }
    get recentApps(){
        return this.recent_app;
    }

    mounted(){
        super.mounted();
        this.dragElement(this.__owl__.refs.recentApps, 'x');
    }

    _mount(){
        this.mount(document.body);
    }

    _unmount(){
        this.unmount();
    }
}
InfinitoRecentApps.template = 'backend_theme_infinito.RecentApps';