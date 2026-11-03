/** @odoo-module **/
import { Dropdown } from "@web/core/dropdown/dropdown";
import { Component, proxy } from '@odoo/owl';
import { registry } from '@web/core/registry';
import { rpc } from "@web/core/network/rpc";
/**
 * Menu item appended in the systray part of the navbar
 */
export class WeatherMenu extends Component {
    static template = 'systrayWeatherMenu';
    static components = { Dropdown };

    setup() {
        super.setup();
        this.state = proxy({
            weather_data: null,
        });
        this.fetch_data();
    }

    async fetch_data() {
        /** Fetching weather data using RPC call **/
        try {
            this.state.weather_data = await rpc('/weather/notification/check', {});
        } catch (error) {
            console.error("Failed to fetch weather data", error);
        }
    }
}

export const WeatherSystrayItem = {
    Component: WeatherMenu,
};

registry.category("systray").add("WeatherNotification", WeatherSystrayItem, { sequence: 100 });
