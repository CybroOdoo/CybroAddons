/** @odoo-module **/
import { CheckBox } from "@web/core/checkbox/checkbox";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { Component, useState } from '@odoo/owl';
import { registry } from '@web/core/registry';
import { session } from "@web/session";
import { rpc } from "@web/core/network/rpc";
/**
 * Menu item appended in the systray part of the navbar
 */
export class WeatherMenu extends Component {
    setup() {
        super.setup();
        this.state = useState({
            weather_data: null,  // Initialize with null or empty object
        });

        // Fetch the weather data initially
        this.fetch_data();
    }

    async fetch_data() {
        /** Fetching weather data using RPC call **/
        try {
            const data = await rpc('/weather/notification/check', {});
            this.state.weather_data = data;  // Update state with fetched data
            this.updateWeatherData();
        } catch (error) {
            console.error("Failed to fetch weather data", error);
        }
    }

    updateWeatherData() {
        /** Updating weather data after fetching **/
         const weather_data = this.state.weather_data;

    if (!weather_data || weather_data.hasOwnProperty("error")) {
        // Handle error or invalid data
        this.session = this.session || {};  // Ensure session object exists
        this.session.name = '';
        this.session.main = '';
        this.session.description = 'Provide a valid API key.';
        this.session.temp = '';
    } else {
        // Initialize session if undefined
        this.session = this.session || {};
        // Properly update session values with fetched data
        this.session.name = weather_data.name;
        this.session.main = weather_data.weather[0].main;
        this.session.description = weather_data.weather[0].description;
        this.session.temp = Math.round(weather_data.main.temp - 273.15);  // Convert Kelvin to Celsius
    }
    }
};
WeatherMenu.template = 'systrayWeatherMenu';
export const WeatherSystrayItem = {
    Component: WeatherMenu,
}
WeatherMenu.components = {
    Dropdown,
    DropdownItem,
    CheckBox
};
registry.category("systray").add("WeatherNotification", WeatherSystrayItem);
