/** @odoo-module **/

import {Component, useState} from "@odoo/owl";
import {Tool} from "./Tool"
import {SaveChanges} from "./SaveChanges";
import {NewTools} from "./change"
import {useService, useBus} from "@web/core/utils/hooks";
import {InfinitoDialog} from "./style_add"
import {rpc} from "@web/core/network/rpc";

const {onWillUnmount, xml} = owl;

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
	                                            <li data-align="left"
	                                                data-type="text-align"
	                                                t-on-click="_onTextAlign">
	                                                <a>
	                                                    <img src="/backend_theme_infinito/static/src/img/infinito/3.svg"/>
	                                                </a>
	                                            </li>
	                                            <li data-align="center"
	                                                data-type="text-align"
	                                                t-on-click="_onTextAlign">
	                                                <a>
	                                                    <img src="/backend_theme_infinito/static/src/img/infinito/2.svg"/>
	                                                </a>
	                                            </li>
	                                            <li data-align="right"
	                                                data-type="text-align"
	                                                t-on-click="_onTextAlign">
	                                                <a>
	                                                    <img src="/backend_theme_infinito/static/src/img/infinito/4.svg"/>
	                                                </a>
	                                            </li>
	                                            <li data-align="middle"
	                                                data-type="vertical-align"
	                                                t-on-click="_onTextAlign">
	                                                <a>
	                                                    <img src="/backend_theme_infinito/static/src/img/infinito/align-center.svg"/>
	                                                </a>
	                                            </li>
	                                            <li data-align="text-top"
	                                                data-type="vertical-align"
	                                                t-on-click="_onTextAlign">
	                                                <a>
	                                                    <img src="/backend_theme_infinito/static/src/img/alignment/top-alignment.svg"/>
	                                                </a>
	                                            </li>
	                                            <li data-align="text-bottom"
	                                                data-type="vertical-align"
	                                                t-on-click="_onTextAlign">
	                                                <a>
	                                                    <img src="/backend_theme_infinito/static/src/img/alignment/align-right.svg"/>
	                                                </a>
	                                            </li>
	                                        </ul>
	                                    </div>
                                    <div class="optss infinito-remove">
    <t t-foreach="state.tools" t-as="tool" t-key="tool.name">
        <div>

            <t t-if="tool.type == 'select'">
                <div class="b_slider">
                    <h6><t t-esc="tool.displayName"/></h6>
                    <select class="form-control"
                            t-att-name="tool.name"
                            t-att-data-alt="tool.alt"
                            t-on-change="_onClickInput">
                        <t t-foreach="tool.options" t-as="opt" t-key="opt">
                            <option t-att-value="opt">
                                <t t-esc="opt"/>
                            </option>
                        </t>
                    </select>
                </div>
            </t>

            <t t-if="tool.type == 'color'">
                <div class="bg_color">
                    <h6><t t-esc="tool.displayName"/></h6>
                    <input type="color"
                           t-att-name="tool.name"
                           t-att-data-alt="tool.alt"
                           t-on-change="_onClickInput"/>
                </div>
            </t>

            <t t-if="tool.type == 'range'">
                <div class="b_slider">
                    <h6><t t-esc="tool.displayName"/></h6>
                    <input type="range"
                           t-att-name="tool.name"
                           t-att-min="tool.min"
                           t-att-max="tool.max"
                           t-att-data-unit="tool.unit"
                           t-on-input="_onClickInput"/>
                </div>
            </t>

        </div>
    </t>
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
        this._alive = true;
        onWillUnmount(() => {
            this._alive = false;
        });

        this.tools = NewTools.property
        this.current_tools = [],
            this.parent = parent;
        this.state = useState({
            display_name: null,
            DesignDictionary: {},
            preset_type: null,
            presets: null,
            tools: [],

        })
        this.renderPresets();
        // Set display name based on props
        const result_string = this.props.elem_name || '';
        this.state.display_name = result_string;
        // Listen for renderEvent bus event to update chart
        useBus(this.env.bus, "renderEvent", (ev) => this.updateChart(ev))

        this._resetSnapshot = this._captureResetSnapshot();
    }

    _captureResetSnapshot() {
        const root = this.props.object?.target;
        if (!root) return new Map();

        const els = new Set();
        const add = (el) => {
            if (el && el.nodeType === 1) els.add(el);
        };

        add(root);

        const tag = (root.tagName || "").toUpperCase();
        if (tag === "TR" || tag === "TBODY" || tag === "THEAD" || tag === "TFOOT" || tag === "TABLE") {
            root.querySelectorAll("th,td").forEach(add);
            root.querySelectorAll("th>div,td>div,th>span,td>span").forEach(add);
        } else if (tag === "TD" || tag === "TH") {
            add(root.firstElementChild);
        }

        const snap = new Map();
        els.forEach((el) => snap.set(el, el.getAttribute("style")));
        return snap;
    }

    /**
     * Asynchronously renders presets based on props
     */
    async renderPresets() {
        if (this.props && this.props.preset) {
            // Set preset type from props
            this.state.preset_type = this.props.preset
            try {
                const response = await rpc('/theme_studio/get_presets', {method: 'call'});
                if (this._alive) {
                    this.state.presets = response;
                }
            } catch {
                // ignore preset load failures
            }
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
        const config = ev.detail.config || {};
        this.state.tools = Object.values(config);
    }


    /**
     * Handles the change event when a preset is selected.
     * @param {Event} ev - The event object representing the change event.
     */



    _onPresetChange(ev) {
        const option = ev.target.selectedOptions[0];
        const styleString = option?.getAttribute('style') || '';

        const target = this.props.object?.target;
        if (!target) return;

        styleString.split(';')
            .map(s => s.trim())
            .filter(Boolean)
            .forEach(rule => {
                const [k, v] = rule.split(':').map(x => x.trim());
                if (k && v) target.style.setProperty(k, v, 'important');
            });
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
        try {
            const selector = '.' + this.props.object.target.dataset.class;
            const data = await rpc('/theme_studio/get_current_style', {
                method: 'call',
                kwargs: {selector},
            });
            if (this._alive && data) {
                self.renderExistingTool(data);
            }
        } catch {
            // ignore style load failures
        }
    }

    /**
     * Handles the event when adding a new style.
     */
    _OnAddStyle() {
        // Get the tools CSS
        var tools_css = this.tools
        this.dialog.add(InfinitoDialog, {tools: tools_css});
    }

    _onTextAlign(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        const btn =
            ev.target?.closest?.(".t_align [data-align][data-type]") || ev.currentTarget;
        const align = btn?.dataset?.align;
        const type = btn?.dataset?.type;
        if (!align || !type) return;

        const selectedTarget = this.props.object?.currentTarget || this.props.object?.target;
        let target = selectedTarget;
        if (!target || target.isConnected === false) {

            const fallback =
                document.querySelector(".preview_area .item[data-name][data-class]") ||
                document.querySelector(".preview_area .item[data-name]") ||
                document.querySelector(".preview_area .item");
            if (fallback) {
                fallback.dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true}));
            }
            return;
        }


        if (target.querySelector) {
            if (target.classList?.contains("o_cp_top_left")) {
                const innerInput = target.querySelector("input.o_searchview_input, .o_searchview_input");
                if (innerInput) target = innerInput;
            } else if (target.classList?.contains("o_cp_searchview")) {
                const innerSearchview = target.querySelector(".o_searchview");
                if (innerSearchview) target = innerSearchview;
            }
        }
        // If the original click was inside a cell, style the cell (and not a nested span, etc.).
        if (target.closest) {
            const cell = target.closest("td,th");
            if (cell) target = cell;
        }

        // For table elements, apply alignment to the actual cells to keep table layout intact.
        const tag = (target.tagName || "").toUpperCase();
        let nodes = [target];
        if (tag === "TR" || tag === "TBODY" || tag === "THEAD" || tag === "TFOOT" || tag === "TABLE") {
            const cells = target.querySelectorAll?.("th,td");
            if (cells && cells.length) nodes = Array.from(cells);
        }

        if (type === 'text-align') {
            const flexMap = {left: "flex-start", center: "center", right: "flex-end"};
            const selfAlign = (n) => {
                if (!n || !n.style) return;
                try {
                    const parent = n.parentElement;
                    if (!parent) return;
                    const isInputLike =
                        n.matches?.("input,select,textarea") ||
                        n.classList?.contains("o_input") ||
                        n.classList?.contains("form-control") ||
                        n.classList?.contains("o_datepicker_input");
                    if (!isInputLike) return;

                    // Only try to reposition if it doesn't already span full width.
                    const rect = n.getBoundingClientRect();
                    const prect = parent.getBoundingClientRect();
                    if ((prect.width - rect.width) < 4) return;

                    // Margins are the safest way to align a fixed-width control in its container.
                    n.style.setProperty("display", "block", "important");
                    if (align === "left") {
                        n.style.setProperty("margin-left", "0", "important");
                        n.style.setProperty("margin-right", "auto", "important");
                    } else if (align === "center") {
                        n.style.setProperty("margin-left", "auto", "important");
                        n.style.setProperty("margin-right", "auto", "important");
                    } else if (align === "right") {
                        n.style.setProperty("margin-left", "auto", "important");
                        n.style.setProperty("margin-right", "0", "important");
                    }
                } catch {
                    // ignore
                }
            };

            const searchInputContainer = target?.closest?.(".o_searchview_input_container");
            if (searchInputContainer && flexMap[align]) {
                searchInputContainer.style.setProperty("display", "flex", "important");
                searchInputContainer.style.setProperty("justify-content", flexMap[align], "important");
                // Make alignment visible in the preview.
                searchInputContainer.style.setProperty("min-height", "36px", "important");
            }

            const navTabs = target?.closest?.("ul.nav-tabs, .nav-tabs");
            if (navTabs && flexMap[align]) {
                navTabs.style.setProperty("display", "flex", "important");
                navTabs.style.setProperty("justify-content", flexMap[align], "important");
            }

            nodes.forEach((n) => {
                if (!n?.style) return;
                const isProgress =
                    n.classList?.contains("progress") ||
                    n.classList?.contains("o_kanban_counter_progress");
                if (isProgress && flexMap[align]) {
                    // Keep Bootstrap progress behavior intact (must remain flex).
                    n.style.setProperty("display", "flex", "important");
                    n.style.setProperty("justify-content", flexMap[align], "important");
                    n.style.setProperty("align-items", "stretch", "important");
                    return;
                }
                n.style.setProperty("text-align", align, "important");
                selfAlign(n);
                try {
                    const disp = window.getComputedStyle(n).display;
                    if (disp && disp.includes("flex") && flexMap[align]) {
                        n.style.setProperty("justify-content", flexMap[align], "important");
                    }
                } catch {
                    // Ignore if computed styles are not available for some reason.
                }
            });
        }

        if (type === "vertical-align") {

            const flexAlignMap = {
                top: "flex-start",
                middle: "center",
                bottom: "flex-end",
                "text-top": "flex-start",
                "text-bottom": "flex-end",
            };

            try {
                const disp = selectedTarget && window.getComputedStyle(selectedTarget).display;
                const flexVal = flexAlignMap[align];
                if (disp && disp.includes("flex") && flexVal) {
                    const isProgress =
                        selectedTarget?.classList?.contains("progress") ||
                        selectedTarget?.classList?.contains("o_kanban_counter_progress");
                    if (isProgress) {

                        selectedTarget.style.setProperty("display", "flex", "important");
                        selectedTarget.style.setProperty("align-items", flexVal, "important");
                        selectedTarget.style.setProperty("height", "18px", "important");
                        selectedTarget
                            .querySelectorAll?.(".progress-bar")
                            ?.forEach((pb) => pb.style.setProperty("height", "10px", "important"));
                    } else {
                        selectedTarget.style.setProperty("align-items", flexVal, "important");
                        if (!selectedTarget.style.minHeight) {
                            selectedTarget.style.setProperty("min-height", "48px", "important");
                        }
                    }
                }
            } catch {
                // ignore
            }

            try {
                const searchInputContainer = target?.closest?.(".o_searchview_input_container");
                const flexVal = flexAlignMap[align];
                if (searchInputContainer && flexVal) {
                    searchInputContainer.style.setProperty("display", "flex", "important");
                    searchInputContainer.style.setProperty("align-items", flexVal, "important");
                    searchInputContainer.style.setProperty("min-height", "36px", "important");
                }
            } catch {
                // ignore
            }

            nodes.forEach((n) => {
                if (!n?.style) return;
                n.style.setProperty("vertical-align", align, "important");
                try {
                    const disp = window.getComputedStyle(n).display;
                    const flexVal = flexAlignMap[align];
                    if (!flexVal) return;

                    const applyFlexAlign = (el) => {
                        if (!el?.style) return;
                        // Avoid forcing flex on table structural elements (tr/tbody/etc).
                        const t = (el.tagName || "").toUpperCase();
                        if (t === "TR" || t === "TBODY" || t === "THEAD" || t === "TFOOT" || t === "TABLE") return;
                        el.style.setProperty("display", "flex", "important");
                        el.style.setProperty("align-items", flexVal, "important");
                        // If the container has height, 100% makes the alignment visible.
                        el.style.setProperty("height", "100%", "important");
                        if (!el.style.minHeight) {
                            el.style.setProperty("min-height", "48px", "important");
                        }
                    };

                    if (disp && disp.includes("flex")) {
                        const isProgress =
                            n?.classList?.contains("progress") ||
                            n?.classList?.contains("o_kanban_counter_progress");
                        if (isProgress) {
                            n.style.setProperty("display", "flex", "important");
                            n.style.setProperty("align-items", flexVal, "important");
                            n.style.setProperty("height", "18px", "important");
                            n.querySelectorAll?.(".progress-bar")?.forEach((pb) => {
                                pb.style.setProperty("height", "10px", "important");
                            });
                        } else {
                            n.style.setProperty("align-items", flexVal, "important");
                        }
                        return;
                    }

                    const tag = (n.tagName || "").toUpperCase();
                    if (tag === "TD" || tag === "TH" || disp === "table-cell") {
                        const inner = n.firstElementChild;
                        if (inner && (inner.tagName === "DIV" || inner.tagName === "SPAN")) {
                            applyFlexAlign(inner);
                        } else {
                            applyFlexAlign(n);
                        }
                        return;
                    }

                    applyFlexAlign(n);
                } catch {
                }
            });
        }


        // Active UI state
        const scope = this.el || document;
        scope
            .querySelectorAll(`.t_align [data-type="${type}"]`)
            .forEach(el => el.classList.remove('active'));
        btn.classList.add('active');
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
    _onResetChanges(ev) {
        ev?.preventDefault?.();
        ev?.stopPropagation?.();

        // Restore original inline styles (unsaved changes) for the selected element + any touched descendants.
        if (this._resetSnapshot) {
            for (const [el, styleAttr] of this._resetSnapshot.entries()) {
                if (!el || !el.isConnected) continue;
                if (styleAttr) {
                    el.setAttribute("style", styleAttr);
                } else {
                    el.removeAttribute("style");
                }
            }
        }

        // Reset sidebar UI state.
        this.state.tools = [];
        const scope = this.el || document;
        scope
            .querySelectorAll(".t_align [data-align][data-type]")
            .forEach((el) => el.classList.remove("active"));
    }


    /**
     * Handles the click event on input elements.
     * @param {Event} ev - The event object representing the click event.
     */
    _onClickInput(ev) {
        const el = ev.target;
        const attr = this.props.object?.target;
        if (!attr) return;

        const inputType = el.name;
        let value = el.value;

        const unit = el.dataset.unit || '';
        const alt = el.dataset.alt;

        if (unit) {
            value += unit;
        }

        let style = `${inputType}: ${value} !important;`;

        // ✅ SAFE alt handling
        if (Array.isArray(alt)) {
            alt.forEach(prefix => {
                style += `${prefix}${inputType}: ${value} !important;`;
            });
        }

        attr.style.cssText += style;
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
                                        <input
  class="favcolor"
  type="color"
  name="${tool.name}"
  data-alt="${tool.alt || ''}"
>

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
        if (ev && ev.preventDefault) ev.preventDefault();
        // Prefer letting the parent client action close the sidebar so it can
        // also restore any hidden panels and offsets.
        if (this.props && typeof this.props.onClose === "function") {
            this.props.onClose();
            return;
        }
        // Fallback for older callers that don't pass `onClose`.
        var parent = document.querySelector("#theme_editor_sidebar_preset");
        if (parent) {
            var main_div = document.querySelector('.marg_main');
            if (main_div) {
                main_div.style.marginLeft = "0px";
                main_div.style.width = "100%";
            }
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