/** @odoo-module **/
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { CheckBox } from "@web/core/checkbox/checkbox";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";
import { Component } from "@odoo/owl";
var ajax = require('web.ajax');
const { onWillStart } = owl;
/**Component for displaying weather information in the user menu. **/
export class WeatherMenu extends Component {
    setup() {
        this.user = useService("user");
        this.session = session;
        onWillStart(async () => {
            /**Updating weather data at initial time **/
            const weather_data = await this.fetch_data();
            if (weather_data.hasOwnProperty("data")) {
                this.session.name = '';
                this.session.main = '';
                this.session.description = 'Configure Notification Settings';
                this.session.temp = '';
            } else {
                this.session.name = weather_data.name;
                this.session.main = weather_data.weather[0].main;
                this.session.description = weather_data.weather[0].description;
                this.session.temp =
                Math.round(weather_data.main['temp'] - 273.15);
            }
        });
        const { origin } = browser.location;
        const { userId } = this.user;
    }
    async getElements() {
        /**Updating weather data while loading template**/
        const self = this;
        const weather_data = await self.fetch_data();
        if (weather_data.hasOwnProperty("data")) {
            self.session.name = '';
            self.session.main = '';
            self.session.description = 'Configure Notification Settings';
            self.session.temp = '';
        } else {
            self.session.name = weather_data.name;
            self.session.main = weather_data.weather[0].main;
            self.session.description = weather_data.weather[0].description;
            self.session.temp = Math.round(weather_data.main['temp'] - 273.15);
        }
    }
    fetch_data() {
        /**Fetching weather data using jsonrpc call**/
        return new Promise(function(resolve, reject) {
            var self = this;
            ajax.jsonRpc('/weather/notification/check', 'call', {}).
                    then(function(data) {
                        resolve(data);
            })
        });
    }
}
WeatherMenu.template = "user_weather_notification.UserMenuS";
WeatherMenu.components = {
    Dropdown,
    DropdownItem,
    CheckBox
};
/**
  Component for displaying weather information in the system tray.
 **/
export const systrayItem = {
    Component: WeatherMenu,
};
registry.category("systray").add("user_weather_notification.user_menus",
    systrayItem, {
        sequence: 0
});
