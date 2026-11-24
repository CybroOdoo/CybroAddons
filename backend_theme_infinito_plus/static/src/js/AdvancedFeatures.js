/** @odoo-module **/
import { Component, xml } from "@odoo/owl";
import { Sidebar } from "./Sidebar";

export class AdvancedFeatures extends Component {
    static template = xml`<div class="sidebar_simple_editor"><Sidebar/></div>`;
    static components = { Sidebar };
}