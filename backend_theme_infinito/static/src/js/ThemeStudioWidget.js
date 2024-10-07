/** @odoo-module **/
import { Component, useState } from "@odoo/owl";

export class ThemeStudioWidget extends Component {
    constructor() {
        super(...arguments);
        // Initialize local storage
        this.localStorage = window.localStorage;
        // Load data from local storage
        this.loadData();
    }
     /**
     * Loads data from local storage.
     */
    loadData() {
        this.editMode = this.localStorage.getItem('editMode') || 'tree';
        this.sidebar = JSON.parse(this.localStorage.getItem('sidebar')) || false;
        this.data = JSON.parse(this.localStorage.getItem('data')) || {};
        this.tool = JSON.parse(this.localStorage.getItem('tool')) || false;
    }
    /**
     * Saves data to local storage.
     */
    saveData() {
        this.localStorage.setItem('editMode', this.editMode);
    }
}
