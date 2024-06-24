/** @odoo-module **/
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.car_garage = publicWidget.Widget.extend({
    selector : '.car_garage',
    init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
    },
    async start() {
        const data = await this.rpc('/get_garage_car',{})
        if(data){
            this.$target.empty().append(data);
        }
    }
});