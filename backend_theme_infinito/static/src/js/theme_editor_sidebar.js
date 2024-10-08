/** @odoo-module **/
// Importing necessary modules and components
import {_t} from "@web/core/l10n/translation";
import {Component, useState} from "@odoo/owl";
import {
    ConfirmationDialog
} from "@web/core/confirmation_dialog/confirmation_dialog";
import {ThemeStudioWidget} from "./ThemeStudioWidget";
import {Tool} from "./Tool"
import {SaveChanges} from "./SaveChanges";
import {NewTools} from "./change"
import {useService, useBus} from "@web/core/utils/hooks";
import {InfinitoDialog} from "./style_add"
import {jsonrpc} from "@web/core/network/rpc_service";
import {Dialog} from "@web/core/dialog/dialog";

const {useRef, onWillStart, xml, onMounted} = owl;

export class ThemeEditorSidebar extends Component {
    static template = xml`<t t-name="backend_theme_infinito.theme_editor_sidebar">
        <div id="theme_editor_sidebar_preset" class="main_sidebar">
            <div class="toggle-btn" t-on-click="toggleSidebar">
                <div class="img_wrapper">
                    <img src="/backend_theme_infinito/static/src/img/infinito/arrow,-direction,-down,-navigate.svg"
                         alt=""/>
                </div>
            </div>
            <div class="sidebar_wrapper">
                <div class="sidebar_content">
                    <div class="button_properties">
                        <p>
                            <a class="btn btn-primary_style">
                                <span id="elem_name"><t t-esc="state.display_name"/></span>
                                <i class="fa fa-plus js_add_tool" t-on-click="_OnAddStyle"/>
                            </a>
                        </p>
                        <div class="infinito-tools">
                            <div class="card card-body">
                                <div class="button_cutomise">
                                    <h6>Presets</h6>
                                    <div class="optss">
                                        <t t-if="state.preset_type == 'button' ">
                                            <div class="form-group infinito-preset">
                                                <select class="form-control"
                                                        id="presets" t-on-change="_onPresetChange">
                                                        <t t-if="state.presets">
                                                            <t t-foreach="state.presets.button" t-as="preset" t-key="preset.name">
                                                                <option t-att-value="preset.name" t-att-style="_convertStyle(preset.style)"><t t-esc="preset.name"/></option>
                                                            </t>
                                                        </t>
                                                </select>
                                            </div>
                                        </t>
                                    </div>
                                    <h6>Text-alignment</h6>
                                    <div class="optss">
                                        <ul class="t_align">
                                            <li>
                                                <a data-align="left"
                                                   data-type="text-align">
                                                    <img src="backend_theme_infinito/static/src/img/infinito/3.svg"
                                                         alt=""/>
                                                </a>
                                            </li>
                                            <li>
                                                <a data-align="center"
                                                   data-type="text-align">
                                                    <img src="backend_theme_infinito/static/src/img/infinito/2.svg"
                                                         alt=""/>
                                                </a>
                                            </li>
                                            <li>
                                                <a data-align="right"
                                                   data-type="text-align">
                                                    <img src="backend_theme_infinito/static/src/img/infinito/4.svg"
                                                         alt=""/>
                                                </a>
                                            </li>
                                            <li>
                                                <a data-align="middle"
                                                   data-type="vertical-align">
                                                    <img src="backend_theme_infinito/static/src/img/infinito/align-center.svg"
                                                         alt=""/>
                                                </a>
                                            </li>
                                            <li>
                                                <a data-align="text-top"
                                                   data-type="vertical-align">
                                                    <img src="backend_theme_infinito/static/src/img/alignment/top-alignment.svg"
                                                         alt=""/>
                                                </a>
                                            </li>
                                            <li>
                                                <a data-align="text-bottom"
                                                   data-type="vertical-align">
                                                    <img src="backend_theme_infinito/static/src/img/alignment/align-right.svg"
                                                         alt=""/>
                                                </a>
                                            </li>
                                        </ul>
                                    </div>
                                    <div class="optss infinito-remove">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="sidebar_footer">
                <a href="#" class="btn btn-reset js_reset_changes" t-on-click="_onResetChanges" style="margin-top:0px;">Reset</a>
                <a href="#" class="btn btn-submit js_save_changes" t-on-click="_onSaveChanges">Save Change
                </a>
            </div>
        </div>
    </t>`;

    /**
     * Setup method for initializing the component
     * @param {Object} parent - The parent object
     * @param {Object} object - The object to initialize
     */
    setup(parent, object) {
        this.action = useService("action");
        this.dialog = useService("dialog");
        this.tools = NewTools.property
        this.current_tools = [],
            this.parent = parent;
        this.state = useState({
            display_name: null,
            DesignDictionary: {},
            preset_type: null,
            presets: null,
        })
        this.renderPresets();
        // Set display name based on props
        const result_string = this.props.elem_name || '';
        this.state.display_name = result_string;
        // Listen for renderEvent bus event to update chart
        useBus(this.env.bus, "renderEvent", (ev) => this.updateChart(ev))
    }

    /**
     * Asynchronously renders presets based on props
     */
    async renderPresets() {
        if (this.props && this.props.preset) {
            // Set preset type from props
            this.state.preset_type = this.props.preset
            let content = '';
            // Fetch presets data from server
            await jsonrpc('/theme_studio/get_presets', {
                method: 'call',
            }).then(response => this.state.presets = response);
        }
    }

    /**
     * Converts a style object into a CSS style string.
     * @param {Object} styleObject - The style object to convert.
     * @returns {string} The CSS style string.
     */
    _convertStyle(styleObject) {
        var styleString = '';
        for (var key in styleObject) {
            if (styleObject.hasOwnProperty(key)) {
                styleString += key + ':' + styleObject[key] + ';';
            }
        }
        return styleString;
    }

    /**
     * Updates the chart based on the configuration received.
     * @param {CustomEvent} ev - The custom event containing the configuration data.
     */
    updateChart(ev) {
        // Extract configuration from the event detail
        this.state.DesignDictionary = ev.detail.config;
        // Clear existing elements in the InfinitoDiv
        const InfinitoDiv = document.querySelector(".infinito-remove");
        InfinitoDiv.innerHTML = '';
        // Iterate over the configuration and create corresponding UI elements
        for (const key in this.state.DesignDictionary) {
            const displayName = this.state.DesignDictionary[key].displayName;
            var newElement = document.createElement('div');
            // Generate HTML based on the type of configuration
            if (this.state.DesignDictionary[key].type == 'select') {
                // Handling select type configuration
                newElement.innerHTML = `<div class="b_slider">
                                            <h6>${displayName}</h6>
                                            <div class="form-group">
                                                <select class="form-control" id="select" t-att-name="${this.state.DesignDictionary[key].name}" aria-label="Default select example"
                                                    t-att-data-alt="${this.state.DesignDictionary[key].alt}" t-on-click="_onClickInput">
                                                    ${this.state.DesignDictionary[key].options.map(option => `
                                                        <option t-att-value="${option}">${option}</option>
                                                    `).join('')}
                                                </select>
                                            </div>
                                        </div>`;
                newElement.querySelector('#select').addEventListener('change', (event) => {
                    this._onClickInput(event);
                });
            } else if (this.state.DesignDictionary[key].type == 'input') {
                // Handling input type configuration
                newElement.innerHTML = `<div class="b_slider">
                                            <h6>${displayName}</h6>
                                          </div>
                                          <ul class="b_style">
                                            <li>
                                                <input type="text" id="text" t-att-name="${this.state.DesignDictionary[key].name}"
                                                    t-att-value="${this.state.DesignDictionary[key].default}" t-att-placeholder="${displayName}"
                                                    t-att-data-alt="${this.state.DesignDictionary[key].alt}" t-on-click="_onClickInput"/>
                                            </li>
                                          </ul>`;
                newElement.querySelector('#text').addEventListener('click', (event) => {
                    this._onClickInput(event);
                });
            } else if (this.state.DesignDictionary[key].type == 'color') {
                // Handling color type configuration
                newElement.innerHTML = `<div class="bg_color">
                                            <h6>${displayName}</h6>
                                            <div class="color_picker">
                                                <input class="favcolor" id="favcolor" type="color" name="${this.state.DesignDictionary[key].name}"
                                                    property="color" alt="${this.state.DesignDictionary[key].alt}"/>
                                            </div>
                                        </div>`;
                newElement.querySelector('.favcolor').addEventListener('change', (event) => {
                    this._onClickInput(event);
                });
            } else if (this.state.DesignDictionary[key].type == 'range') {
                // Handling range type configuration
                newElement.innerHTML = `<div class="b_slider">
                                            <h6>${displayName}</h6>
                                            <h6>${this.state.DesignDictionary[key].unit}</h6>
                                        </div>
                                        <div class="b_width">
                                            <div class="sliderContainer">
                                                <input type="range" name="${this.state.DesignDictionary[key].name}"
                                                    value="${this.state.DesignDictionary[key].default}" min="${this.state.DesignDictionary[key].min}" max="${this.state.DesignDictionary[key].max}"
                                                    id="slider" data-unit="${this.state.DesignDictionary[key].unit}"/>
                                                <span id="output"/>
                                            </div>
                                        </div>`;
                newElement.querySelector('#slider').addEventListener('change', (event) => {
                    this._onClickInput(event);
                });
            }
            // Append the newly created element to the InfinitoDiv
            InfinitoDiv.appendChild(newElement);
        }
    }

    /**
     * Handles the change event when a preset is selected.
     * @param {Event} ev - The event object representing the change event.
     */
    _onPresetChange(ev) {
        // Get the index and selected option element
        let index = ev.target.selectedIndex;
        let elem = ev.target.children[index];
        // Extract inline style string from the selected option element
        let styleString = elem.getAttribute('style');
        // Split the style string into individual style declarations and create a dictionary of styles
        const styleDeclarations = styleString.split(';');
        const styles_dict = {}
        styleDeclarations.forEach(style => {
            const [key, value] = style.split(':').map(part => part.trim());
            styles_dict[key] = value;
        })
        // Initialize data array and new_style string
        let data = [];
        let new_style = '';
        // Apply the styles from the selected preset to the target element and build the data array and new_style string
        let targetElement = this.props.object.target
        for (let rule in styles_dict) {
            new_style += `${rule}: ${styles_dict[rule]} !important;`
            data.push([rule, styles_dict[rule]]);
        }
        // Apply the new style to the target element
        if (targetElement) {
            targetElement.style.cssText = new_style;
        }
        // Render existing tool with the updated data
        this.renderExistingTool(data);
    }

    /**
     * Asynchronously renders tools based on the current state.
     */
    async renderTools() {
        // Store reference to the current instance
        var self = this;
        // Render tools based on the current state
        this.tools = this.tool || new Tool(this, this.props.object.target).render();
        // Fetch current style data from the server
        await jsonrpc('/theme_studio/get_current_style', {
            method: 'call',
            kwargs: {
                'selector': '.' + this.props.object.target.dataset.class,
            }
        }).then(function (data) {
            // If data is available, render existing tool with the fetched data
            if (data) {
                self.renderExistingTool(data);
            }
        });
    }

    /**
     * Handles the event when adding a new style.
     */
    _OnAddStyle() {
        // Get the tools CSS
        var tools_css = this.tools
        // Open a dialog to add a new style with the tools CSS
        this.dialog.add(InfinitoDialog, {tools: tools_css});
    }

    /**
     * Handles the event when saving changes.
     */
    _onSaveChanges() {
        // Store reference to the current instance
        var self = this;
        // Extract target class and styles from props
        var targetClass = this.props.object.target.dataset.class
        var styles = this.props.object.target.style
        // Open a dialog to save changes with the target styles and class
        this.dialog.add(SaveChanges, {tools: styles, targetClass: targetClass});
    }

    /**
     * Handles the event when resetting changes.
     */
    _onResetChanges() {
        // Remove the element with class 'infinito-remove'
        document.querySelector('.infinito-remove').remove();
    }

    /**
     * Handles the click event on input elements.
     * @param {Event} ev - The event object representing the click event.
     */
    _onClickInput(ev) {
        // Initialize variables
        var input_value, new_attr = '';
        // Extract input type, unit, and alt from the target element
        var input_type = $(ev.target).attr('name');
        var all_alts = [input_type];
        var unit = $(ev.target).data('unit');
        var alt = $(ev.target).data('alt');
        // Handle range input type
        if ($(ev.target).attr('type') == 'range') {
            let value = $(ev.target).val();
            if (unit) {
                value += unit;
            }
            value = $(ev.target).val() == '-1' ? 'infinite' : value;
            $(ev.target).next().html(value);
        }
        // Determine input value based on unit presence and handle infinite value
        if (unit) {
            input_value = $(ev.target).val() + unit + ' !important;';
        } else {
            input_value = $(ev.target).val() + ' !important;';
        }
        input_value = $(ev.target).val() == '-1' ? 'infinite !important;' : input_value;
        // Construct style string based on input value, type, and alt
        var style = input_type + ': ' + input_value;
        for (var i = 0; i < alt; i++) {
            if (alt[i] != '') {
                style += alt[i] + input_type + ': ' + input_value;
                all_alts.push(alt[i] + input_type)
            }
        }
        // Apply the style to the target element
        var attr = this.props.object.target;
        $(attr).css('cssText', style);
    }

    /**
     * Renders a new tool based on the provided tool configuration.
     * @param {Object} tool - The tool configuration object.
     * @param {string} [val=null] - Optional value to override the default value of the tool.
     */
    renderNewTool(tool, val = null) {
        if (tool) {
            // Get default value or use provided value
            var value = this.getDefaultValue(tool.name);
            if (val) {
                value = val;
            }
            if (tool.type == 'range') {
                value = value.replace(/[^0-9,.]+/g, "")
            }
            // Set the tool default value
            this.state.widget = tool;
            tool.default = value;
            // Create a new div element for the tool
            var newDiv = document.createElement("div");
            newDiv.classList.add("optss", "infinito-remove");
            // Generate HTML based on the tool type
            if (tool.type == 'color') {
                // Color type tool
                newDiv.innerHTML = `<div class="bg_color">
                                    <h6>${tool.displayName}</h6>
                                    <div class="color_picker">
                                        <input class="favcolor" id="favcolor" type="color" name="${tool.name}" value="${tool.default}" property="color" data-alt="${tool.alt}"/>
                                    </div>
                                </div>`;
                var customizeButton = document.querySelector('.button_cutomise');
                customizeButton.appendChild(newDiv);
            }
            var rangeDiv = document.createElement("div");
            rangeDiv.classList.add("optss", "infinito-remove");
            if (tool.type == 'range') {
                // Range type tool
                rangeDiv.innerHTML = `<div class="b_slider">
                                        <h6>
                                            ${tool.displayName}
                                        </h6>
                                        <h6>
                                            ${tool.unit}
                                        </h6>
                                    </div>
                                    <div class="b_width">
                                        <div class="sliderContainer">
                                            <input type="range" t-att-name="${tool.name}" t-att-data-unit="${tool.unit}"
                                                   value="${tool.default}" t-att-min="${tool.min}" t-att-max="${tool.max}"
                                                   id="slider" t-att-data-alt="${tool.alt}"/>
                                            <span id="output"/>
                                        </div>
                                    </div>`
                var customizeButton = document.querySelector('.button_cutomise');
                customizeButton.appendChild(rangeDiv);
                var rangeInput = document.getElementById('slider');
                rangeInput.addEventListener('click', function () {
                    // Handle click event if needed
                });
            }
            var SelectDiv = document.createElement("div");
            SelectDiv.classList.add("optss", "infinito-remove");
            if (tool.type == 'select') {
                // Select type tool
                SelectDiv.innerHTML = `<div class="b_slider">
                                        <h6>
                                             ${tool.displayName}
                                        </h6>
                                        <div class="form-group">
                                            <select class="form-control" id="select" t-att-name="${tool.name}" aria-label="Default select example" t-att-data-alt="${tool.alt}">
                                                <t t-foreach="${tool.options}" t-as="option" t-key="option">
                                                    <option t-att-value="option"><t t-esc="option"/></option>
                                                </t>
                                            </select>
                                        </div>
                                    </div>`;
                var customizeButton = document.querySelector('.button_cutomise');
                customizeButton.appendChild(SelectDiv);
            }
            var InputDiv = document.createElement("div");
            InputDiv.classList.add("optss", "infinito-remove");
            if (tool.type == 'input') {
                // Input type tool
                InputDiv.innerHTML = `<div class="b_slider">
                                        <h6>
                                            ${tool.displayName}
                                        </h6>
                                    </div>
                                    <ul class="b_style">
                                        <li>
                                            <input type="text" id="text" t-att-name="${tool.name}"
                                                   t-att-value="${tool.default}" t-att-placeholder="${tool.displayName}"
                                                   t-att-data-alt="${tool.alt}"/>
                                        </li>
                                    </ul>`
                // Append the new tool to the DOM
                var customizeButton = document.querySelector('.button_cutomise');
                customizeButton.appendChild(InputDiv);
            }
        }
    }

    /**
     * Renders existing tools based on the provided style data.
     * @param {Array} data - An array containing style data to render existing tools.
     */
    renderExistingTool(data) {
        // Iterate over each rule in the data
        for (var rule of data) {
            // Find the corresponding tool based on the rule name
            var current = NewTools.property.filter(tool => tool.name == rule[0].replace(' ', ''));
            // Push the tool name to the current_tools array
            this.current_tools.push(rule[0].replace(' ', ''));
            // Render the new tool based on the found tool configuration
            this.renderNewTool(current[0]);
        }
    }

    /**
     * Retrieves the default value of a CSS property from the target element.
     * @param {string} property - The CSS property to retrieve the default value for.
     * @returns {string} - The default value of the CSS property.
     */
    getDefaultValue(property) {
        // Get the computed style of the target element for the specified property
        var val = window.getComputedStyle(this.props.object.target).getPropertyValue(property);
        // Convert RGB color values to hexadecimal format if necessary
        if (val.includes('rgb')) {
            var rgb = val.match(/\d+/g);
            val = rgbToHex(rgb[0], rgb[1], rgb[2]);
        }
        // Return the default value
        return val
    }

    /**
     * Sets the browser location search to enable assets debugging.
     */
    setAssets() {
        browser.location.search = "?debug=assets";
    }

    /**
     * Toggles the visibility of the sidebar in the theme editor.
     * @param {Event} ev - The event object representing the click event.
     */
    toggleSidebar(ev) {
        // Get the parent element of the sidebar preset
        var parent = document.querySelector("#theme_editor_sidebar_preset")
        // If the parent element exists
        if (parent) {
            // Reset the margin of the main content area
            var main_div = document.querySelector('.marg_main');
            main_div.style.marginLeft = "0px";
            // Remove the sidebar preset
            parent.remove();
        }
    }
}

/**
 * Converts a single RGB component value to its hexadecimal representation.
 * @param {number} c - The RGB component value (0-255).
 * @returns {string} - The hexadecimal representation of the RGB component.
 */
function componentToHex(c) {
    c = parseInt(c);
    var hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

/**
 * Converts RGB color values to hexadecimal format.
 * @param {number} r - The red component value (0-255).
 * @param {number} g - The green component value (0-255).
 * @param {number} b - The blue component value (0-255).
 * @returns {string} - The hexadecimal representation of the RGB color.
 */
function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}
