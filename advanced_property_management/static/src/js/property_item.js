/**@odoo-module **/
import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';

export class PropertyItemView extends Interaction {
    static selector = '.property_container';
    dynamicContent = {
        '#loadMap': { 't-on-click': this._MapLoad },
    };
    _MapLoad(e) {
        const { lat, lng } = e.target.dataset;

        this.el.querySelector('#map-view').style.display = 'block';
        this.el.querySelector('#loadMap').style.display = 'none';

        const location = { lat: parseFloat(lat), lng: parseFloat(lng) };

        const map = new google.maps.Map(this.el.querySelector("#map-view"), {
            zoom: 12,
            center: location,
        });

        new google.maps.Marker({
            position: location,
            map,
        });
    }
};
registry
    .category('public.interactions')
    .add('advanced_property_management.property_view_item', PropertyItemView);
