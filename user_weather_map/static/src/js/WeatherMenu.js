/** @odoo-module **/

import { CheckBox } from "@web/core/checkbox/checkbox";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { Component } from '@odoo/owl';
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";
import { browser } from "@web/core/browser/browser";

   /**
    * Menu item appended in the systray part of the navbar
    */
export class WeatherMenu extends Component{
    setup() {
        this.user = useService("user");
        this.session = session;
        this.rpc = useService("rpc");
        this.fetch_data()
    }
    async getElements() {
        /**Updating weather data while loading template**/
        const self = this;
        const weather_data = this.data;
        if (weather_data.hasOwnProperty("data")) {
            self.session.name = '';
            self.session.main = '';
            self.session.description = 'Provide a valid API key.';
            self.session.temp = '';
        } else {
            self.session.name = weather_data.name;
            self.session.main = weather_data.weather[0].main;
            self.session.description = weather_data.weather[0].description;
            self.session.temp = Math.round(weather_data.main['temp'] - 273.15);
        }
    }
    fetch_data() {
        /**Fetching weather data using rpc call**/
            var self = this;
            this.rpc('/weather/notification/check', {}).then((data) => {
                this.data = data
            });
    }
};

WeatherMenu.template = 'systrayWeatherMenu';
export const WeatherSystrayItem = {
    Component: WeatherMenu,
};
WeatherMenu.components = {
    Dropdown,
    DropdownItem,
    CheckBox
};
registry.category("systray").add("WeatherNotification", WeatherSystrayItem);
