/** @odoo-module **/

import { PivotRenderer } from "@web/views/pivot/pivot_renderer";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { useListener, onMounted, onPatched, proxy } from "@odoo/owl";

patch(PivotRenderer.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.isMouseDown = false;
        this.condState = proxy({
            showButton: true,
            showContainer: false,
            condition: "greater than",
            value: "",
            secondValue: "",
            color: "#ff0000",
            textColor: "#ffffff",
            hasError: false,
        });

        useListener(document, "mouseup", () => this.mouse_up_function());

        onMounted(() => {
            this.set_default_rules();
        });

        onPatched(() => {
            if (!this.conditional_rules && !this.loadingRules) {
                this.set_default_rules();
            } else if (this.conditional_rules && this.conditional_rules.length) {
                this.apply_rules_to_cells(this.conditional_rules);
            }
        });
    },

    getTableEl() {
        return typeof this.tableRef === "function" ? this.tableRef() : this.tableRef?.el;
    },

    async set_default_rules() {
        const model = this.env.searchModel?.resModel || this.model?.metaData?.resModel;
        if (!model) {
            return;
        }

        let viewId = this.env.config?.viewId;
        if (!viewId && this.env.config?.views) {
            const pivotView = this.env.config.views.find((v) => v[1] === "pivot");
            if (pivotView) {
                viewId = pivotView[0];
            }
        }
        if (!viewId && this.props?.info?.viewId) {
            viewId = this.props.info.viewId;
        }

        const domain = [["model_id.model", "=", model]];
        if (viewId) {
            domain.push("|", ["view_id", "=", viewId], ["view_id", "=", false]);
        }

        this.loadingRules = true;
        try {
            const res = await this.orm.call("conditional.rules", "search_read", [], {
                domain: domain,
            });
            this.conditional_rules = res || [];
            this.apply_rules_to_cells(this.conditional_rules);
            requestAnimationFrame(() => {
                this.apply_rules_to_cells(this.conditional_rules);
            });
        } catch (_err) {
            this.conditional_rules = [];
        } finally {
            this.loadingRules = false;
        }
    },

    apply_rules_to_cells(rules) {
        const tableEl = this.getTableEl();
        if (!tableEl || !rules || !rules.length) {
            return;
        }
        const cells = tableEl.querySelectorAll("td.o_pivot_cell_value");
        for (let i = 0, len = cells.length; i < len; i++) {
            if (!cells[i].dataset.customBg) {
                cells[i].style.removeProperty("background-color");
                cells[i].style.removeProperty("color");
                cells[i].querySelectorAll("*").forEach((el) => el.style.removeProperty("color"));
            }
        }

        for (let i = 0, len = rules.length; i < len; i++) {
            this.apply_condition_to_cells(cells, rules[i]);
        }

        tableEl.querySelectorAll("[data-custom-bg]").forEach((cell) => {
            cell.classList.remove("bg-100");
            cell.style.setProperty("background-color", cell.dataset.customBg, "important");
            cell.style.setProperty("color", cell.dataset.customColor, "important");
            cell.querySelectorAll("*").forEach((el) => {
                el.style.setProperty("color", cell.dataset.customColor, "important");
            });
        });
    },

    apply_condition_to_cells(cells, ruleObj) {
        const condition = ruleObj.rule;
        const condVal = parseFloat(ruleObj.value);
        const secondCondVal = parseFloat(ruleObj.second_value);
        const colorVal = ruleObj.color;
        const textColorVal = ruleObj.text_color;

        for (let j = 0, len = cells.length; j < len; j++) {
            const cell = cells[j];
            let cellText = cell.innerText ? cell.innerText.trim() : "";
            let clean = cellText.replace(/[^0-9.,-]/g, "");
            if (clean.includes(",") && clean.includes(".")) {
                if (clean.indexOf(",") < clean.indexOf(".")) {
                    clean = clean.replace(/,/g, "");
                } else {
                    clean = clean.replace(/\./g, "").replace(",", ".");
                }
            } else if (clean.includes(",")) {
                const parts = clean.split(",");
                if (parts.length === 2 && parts[1].length !== 3) {
                    clean = parts[0] + "." + parts[1];
                } else {
                    clean = clean.replace(/,/g, "");
                }
            }
            const numericVal = parseFloat(clean);
            let matches = false;

            if (condition === "less than" || condition === "less_than") {
                if (!isNaN(numericVal) && !isNaN(condVal) && numericVal < condVal) {
                    matches = true;
                }
            } else if (condition === "greater than" || condition === "greater_than") {
                if (!isNaN(numericVal) && !isNaN(condVal) && numericVal > condVal) {
                    matches = true;
                }
            } else if (condition === "null" || condition === "is_empty") {
                if (cellText === "" || cell.classList.contains("o_empty")) {
                    matches = true;
                }
            } else if (condition === "in between" || condition === "in_between") {
                if (
                    !isNaN(numericVal) &&
                    !isNaN(condVal) &&
                    !isNaN(secondCondVal) &&
                    numericVal >= Math.min(condVal, secondCondVal) &&
                    numericVal <= Math.max(condVal, secondCondVal)
                ) {
                    matches = true;
                }
            }

            if (matches) {
                cell.classList.remove("bg-100");
                cell.dataset.customBg = colorVal;
                cell.dataset.customColor = textColorVal;
                cell.style.setProperty("background-color", colorVal, "important");
                cell.style.setProperty("color", textColorVal, "important");
                cell.querySelectorAll("*").forEach((el) => {
                    el.style.setProperty("color", textColorVal, "important");
                });
            }
        }
    },

    conditional_format_tab() {
        this.condState.showContainer = !this.condState.showContainer;
        if (this.condState.showContainer) {
            this.condState.value = "";
            this.condState.secondValue = "";
            this.condState.hasError = false;
        } else {
            const tableEl = this.getTableEl();
            tableEl?.querySelectorAll(".selected_cell").forEach((c) => c.classList.remove("selected_cell"));
        }
    },

    onOpenView(cell, newWindow) {
        if (this.condState?.showContainer) {
            return;
        }
        return super.onOpenView(...arguments);
    },

    conditional_format_cell(e) {
        if (!this.condState.showContainer) {
            return;
        }
        const tableEl = this.getTableEl();
        const cell = e.target.closest("td.o_pivot_cell_value") || e.target.closest("td");
        if (cell && tableEl && tableEl.contains(cell)) {
            this.isMouseDown = true;
            cell.classList.toggle("selected_cell");
            cell.classList.add("prevent-select");
            this.condState.showButton = true;
        }
    },

    mouse_over_function(e) {
        if (!this.isMouseDown || !this.condState.showContainer) {
            return;
        }
        const tableEl = this.getTableEl();
        const cell = e.target.closest("td.o_pivot_cell_value") || e.target.closest("td");
        if (cell && tableEl && tableEl.contains(cell)) {
            cell.classList.add("selected_cell");
            this.condState.showButton = true;
        }
    },

    mouse_up_function() {
        this.isMouseDown = false;
    },

    display_field() {
        this.condState.hasError = false;
        this.condState.value = "";
        this.condState.secondValue = "";
    },

    set_rule() {
        const tableEl = this.getTableEl();
        const container = tableEl?.parentElement?.querySelector('.conditional_container') || document.querySelector('.conditional_container');
        const inputEl = container?.querySelector('#condition_val');
        const secondInputEl = container?.querySelector('#secondcondition_val');
        const colorInput = container?.querySelector('#colorpicker');
        const textColorInput = container?.querySelector('#text_color');
        const selectEl = container?.querySelector('.condition_select');

        const condition = selectEl?.value || this.condState.condition;
        const colorVal = colorInput?.value || this.condState.color;
        const textColorVal = textColorInput?.value || this.condState.textColor;
        const conditionVal = (inputEl && inputEl.value !== "") ? inputEl.value : this.condState.value;
        const secondConditionVal = (secondInputEl && secondInputEl.value !== "") ? secondInputEl.value : this.condState.secondValue;

        if (condition === "in between" || condition === "in_between") {
            if (parseFloat(conditionVal) >= parseFloat(secondConditionVal)) {
                this.condState.hasError = true;
                return;
            }
        }
        this.condState.hasError = false;

        if (!tableEl) {
            return;
        }

        const selectedCells = tableEl.querySelectorAll(".selected_cell");
        const newRule = {
            rule: condition,
            value: conditionVal,
            second_value: secondConditionVal,
            color: colorVal,
            text_color: textColorVal,
        };

        if (selectedCells.length) {
            this.apply_condition_to_cells(selectedCells, newRule);
            selectedCells.forEach((c) => {
                c.classList.remove("selected_cell");
                c.classList.remove("prevent-select");
            });
        } else {
            const allCells = tableEl.querySelectorAll("td.o_pivot_cell_value");
            this.apply_condition_to_cells(allCells, newRule);
            if (!this.conditional_rules) {
                this.conditional_rules = [];
            }
            this.conditional_rules.push(newRule);
        }

        this.condState.value = "";
        this.condState.secondValue = "";
        if (inputEl) {
            inputEl.value = "";
        }
        if (secondInputEl) {
            secondInputEl.value = "";
        }
    },
});
