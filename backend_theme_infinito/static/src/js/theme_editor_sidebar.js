/** @odoo-module **/
import { Component, onWillUnmount, proxy, signal, t, useProps, xml } from "@odoo/owl";
import { useEnv } from "@web/owl2/utils";



import {SaveChanges} from "./SaveChanges";
import {NewTools} from "./change"
import {useService, useBus} from "@web/core/utils/hooks";
import {InfinitoDialog} from "./style_add"
import { _t } from "@web/core/l10n/translation";
import {rpc} from "@web/core/network/rpc";




export class ThemeEditorSidebar extends Component {
    panelRef = signal.ref();

    props = useProps({
        elem_name: t.string().optional(""),
        preset: t.string().optional(),
        object: t.object(),
        onClose: t.function().optional(),
    });

    static template = xml`<t t-name="backend_theme_infinito.theme_editor_sidebar">
        <div id="theme_editor_sidebar_preset" class="main_sidebar" t-ref="this.panelRef">
            <div class="toggle-btn" t-on-click="this.toggleSidebar">
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
                                <span id="elem_name"><t t-out="this.state.display_name"/></span>
                                <i class="js_add_tool oi" data-icon="add" t-on-click="this._OnAddStyle"/>
                            </a>
                        </p>
                        <div class="infinito-tools">
                            <div class="card card-body">
                                <div class="button_cutomise">
                                    <h6>Presets</h6>
                                    <div class="optss">
                                        <t t-if="this.state.preset_type == 'button' ">
                                            <div class="mb-3 infinito-preset">
                                                <select class="form-control"
                                                        id="presets" t-on-change="this._onPresetChange">
                                                        <t t-if="this.state.presets">
                                                            <t t-foreach="this.state.presets.button" t-as="preset" t-key="preset.name">
                                                                <option t-att-value="preset.name" t-att-style="this._convertStyle(preset.style)"><t t-out="preset.name"/></option>
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
	                                                t-on-click="this._onTextAlign">
	                                                <a>
	                                                    <img src="/backend_theme_infinito/static/src/img/infinito/3.svg"/>
	                                                </a>
	                                            </li>
	                                            <li data-align="center"
	                                                data-type="text-align"
	                                                t-on-click="this._onTextAlign">
	                                                <a>
	                                                    <img src="/backend_theme_infinito/static/src/img/infinito/2.svg"/>
	                                                </a>
	                                            </li>
	                                            <li data-align="right"
	                                                data-type="text-align"
	                                                t-on-click="this._onTextAlign">
	                                                <a>
	                                                    <img src="/backend_theme_infinito/static/src/img/infinito/4.svg"/>
	                                                </a>
	                                            </li>
	                                            <li data-align="middle"
	                                                data-type="vertical-align"
	                                                t-on-click="this._onTextAlign">
	                                                <a>
	                                                    <img src="/backend_theme_infinito/static/src/img/infinito/align-center.svg"/>
	                                                </a>
	                                            </li>
	                                            <li data-align="text-top"
	                                                data-type="vertical-align"
	                                                t-on-click="this._onTextAlign">
	                                                <a>
	                                                    <img src="/backend_theme_infinito/static/src/img/alignment/top-alignment.svg"/>
	                                                </a>
	                                            </li>
	                                            <li data-align="text-bottom"
	                                                data-type="vertical-align"
	                                                t-on-click="this._onTextAlign">
	                                                <a>
	                                                    <img src="/backend_theme_infinito/static/src/img/alignment/align-right.svg"/>
	                                                </a>
	                                            </li>
	                                        </ul>
	                                    </div>
                                    <div class="optss infinito-remove">
    <t t-foreach="this.state.tools" t-as="tool" t-key="tool.name">
        <div>

            <t t-if="tool.type == 'select'">
                <div class="b_slider">
                    <h6><t t-out="tool.displayName"/></h6>
                    <select class="form-control"
                            t-att-name="tool.name"
                            t-att-data-alt="tool.alt"
                            t-on-change="this._onClickInput">
                        <t t-foreach="tool.options" t-as="opt" t-key="opt">
                            <option t-att-value="opt">
                                <t t-out="opt"/>
                            </option>
                        </t>
                    </select>
                </div>
            </t>

            <t t-if="tool.type == 'color'">
                <div class="bg_color">
                    <h6><t t-out="tool.displayName"/></h6>
                    <input type="color"
                           t-att-name="tool.name"
                           t-att-data-alt="tool.alt"
                           t-on-change="this._onClickInput"/>
                </div>
            </t>

            <t t-if="tool.type == 'range'">
                <div class="b_slider">
                    <h6><t t-out="tool.displayName"/></h6>
                    <input type="range"
                           t-att-name="tool.name"
                           t-att-min="tool.min"
                           t-att-max="tool.max"
                           t-att-data-unit="tool.unit"
                           t-on-input="this._onClickInput"/>
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
                <a href="#" class="btn btn-reset js_reset_changes" t-on-click="this._onResetChanges" style="margin-top:0px;">Reset</a>
                <a href="#" class="btn btn-submit js_save_changes" t-on-click="this._onSaveChanges">Save Changes
                </a>
            </div>
        </div>
    </t>`;

    /**
     * Setup method for initializing the component
     */
    setup() {
        this.env = useEnv();
        this.action = useService("action");
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this._alive = true;
        onWillUnmount(() => {
            this._alive = false;
        });

        this.tools = NewTools.property
        this.current_tools = [];
        this.state = proxy({
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
                if (this._alive) {
                    this.notification.add(_t("Could not load theme presets."), { type: "warning" });
                }
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
        this.tools = NewTools.property;

        // Fetch current style data from the server
        try {
            const selector = '.' + this.props.object.target.dataset.class;
            const data = await rpc('/theme_studio/get_current_style', {

                kwargs: {selector},
            });
            if (this._alive && data) {
                self.renderExistingTool(data);
            }
        } catch {
            if (this._alive) {
                this.notification.add(_t("Could not load the current style."), { type: "warning" });
            }
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
                const disp = window.getComputedStyle(n).display;
                if (disp && disp.includes("flex") && flexMap[align]) {
                    n.style.setProperty("justify-content", flexMap[align], "important");
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


            const searchInputContainer = target?.closest?.(".o_searchview_input_container");
            if (searchInputContainer && flexVal) {
                searchInputContainer.style.setProperty("display", "flex", "important");
                searchInputContainer.style.setProperty("align-items", flexVal, "important");
                searchInputContainer.style.setProperty("min-height", "36px", "important");
            }


            nodes.forEach((n) => {
                if (!n?.style) return;
                n.style.setProperty("vertical-align", align, "important");
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

            });
        }


        // Active UI state
        const scope = this.panelRef();
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
        const target = this.props.object.target;
        const extraRules = [];
        // Table alignment is applied to cells in the preview. Persist those
        // declarations as well as the selected row/container's own style.
        if (target.matches('table,thead,tbody,tfoot,tr')) {
            for (const tag of ['th', 'td']) {
                const cell = target.querySelector(tag);
                if (cell?.style.length) {
                    extraRules.push({
                        targetClass: `${targetClass} ${tag}`,
                        styles: cell.style,
                    });
                }
            }
        }
        this.dialog.add(SaveChanges, {tools: styles, targetClass, extraRules});
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
        const scope = this.panelRef();
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
        let alt;
        try {
            alt = JSON.parse(el.dataset.alt || '[]');
        } catch {
            alt = (el.dataset.alt || '').split(',').filter(Boolean);
        }

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
        const container = this.panelRef().querySelector('.button_cutomise');
        if (!tool || !container) {
            return;
        }
        let value = val ?? this.getDefaultValue(tool.name);
        if (tool.type === 'range') {
            value = String(value).replace(/[^0-9,.]+/g, '');
        }
        this.state.widget = tool;
        tool.default = value;

        const wrapper = document.createElement('div');
        wrapper.className = 'optss infinito-remove';
        const heading = document.createElement('div');
        heading.className = tool.type === 'color' ? 'bg_color' : 'b_slider';
        const label = document.createElement('h6');
        label.textContent = tool.displayName;
        heading.appendChild(label);
        wrapper.appendChild(heading);

        const input = document.createElement(tool.type === 'select' ? 'select' : 'input');
        input.name = tool.name;
        input.dataset.alt = JSON.stringify(tool.alt || []);
        if (tool.type === 'select') {
            input.className = 'form-control';
            input.setAttribute('aria-label', tool.displayName);
            for (const optionValue of tool.options || []) {
                const option = document.createElement('option');
                option.value = optionValue;
                option.textContent = optionValue;
                input.appendChild(option);
            }
        } else {
            input.type = { color: 'color', range: 'range' }[tool.type] || 'text';
            if (tool.type === 'color') {
                input.className = 'favcolor';
            } else if (tool.type === 'range') {
                input.dataset.unit = tool.unit || '';
                input.min = tool.min;
                input.max = tool.max;
                const unit = document.createElement('h6');
                unit.textContent = tool.unit || '';
                heading.appendChild(unit);
            } else {
                input.placeholder = tool.displayName;
            }
        }
        input.value = value ?? '';
        input.addEventListener('change', (event) => this._onClickInput(event));
        const control = document.createElement(tool.type === 'input' ? 'ul' : 'div');
        control.className = {
            color: 'color_picker', range: 'b_width',
            select: 'mb-3', input: 'b_style',
        }[tool.type] || '';
        if (tool.type === 'range' || tool.type === 'input') {
            const inner = document.createElement(tool.type === 'range' ? 'div' : 'li');
            if (tool.type === 'range') {
                inner.className = 'sliderContainer';
            }
            inner.appendChild(input);
            control.appendChild(inner);
        } else {
            control.appendChild(input);
        }
        if (tool.type === 'color' || tool.type === 'select') {
            heading.appendChild(control);
        } else {
            wrapper.appendChild(control);
        }
        container.appendChild(wrapper);
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
        var parent = this.panelRef();
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
