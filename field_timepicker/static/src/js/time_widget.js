/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";
import { Component, useRef, onMounted } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

export class FieldTimePicker extends Component {
    static template = 'FieldTimePicker';
    static props = {...standardFieldProps};

    setup() {
        this.input = useRef('input_time');
        onMounted(() => {
            if (!this.input.el) console.error("Input element is not available.");
        });
        useInputField({getValue: () => this.props.record.data[this.props.name] || "", refName: "input_time"});
    }
    
    _onClickTimeField(ev) {
        if (this.props.readonly) return;
        const timePicker = this.input.el;
        if (!timePicker) {
            console.error("Input element is not available.");
            return;
        }
        if (this.props.record.fields[this.props.name].type !== "char") {
            this.env.services.dialog.add(AlertDialog, {body: _t("This widget can only be added to 'Char' field")});
            return;
        }
        const currentTime = timePicker.value || "00:00:00";
        const [hour = 0, minute = 0, second = 0] = currentTime.split(':').map(Number);
        const timePickerContainer = document.createElement("div");
        timePickerContainer.className = "time-picker-container";
        timePickerContainer.style.cssText = `position: absolute; background: white; border: 1px solid #ccc; border-radius: 4px; padding: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); z-index: 1050; display: flex; gap: 10px; flex-direction: column;`;
        const rect = timePicker.getBoundingClientRect();
        timePickerContainer.style.top = `${rect.bottom + window.scrollY}px`;
        timePickerContainer.style.left = `${rect.left + window.scrollX}px`;
        const timeBoxesContainer = document.createElement("div");
        timeBoxesContainer.style.cssText = "display: flex; gap: 10px;";
        const createTimeBox = (label, value, max) => {
            const wrapper = document.createElement("div");
            wrapper.style.cssText = "display: flex; flex-direction: column; align-items: center; gap: 5px;";
            const labelEl = document.createElement("div");
            labelEl.textContent = label;
            labelEl.style.cssText = "font-size: 12px; font-weight: bold; color: #666;";
            wrapper.appendChild(labelEl);
            const incrementButton = document.createElement("button");
            incrementButton.textContent = "+";
            incrementButton.className = "btn btn-sm btn-secondary";
            incrementButton.style.cssText = "padding: 2px 8px; cursor: pointer;";
            wrapper.appendChild(incrementButton);
            const display = document.createElement("div");
            display.textContent = value < 10 ? `0${value}` : value;
            display.className = "time-box-display";
            display.style.cssText = "font-size: 18px; font-weight: bold; padding: 5px 10px; background: #f5f5f5; border-radius: 4px; min-width: 40px; text-align: center;";
            wrapper.appendChild(display);
            const decrementButton = document.createElement("button");
            decrementButton.textContent = "-";
            decrementButton.className = "btn btn-sm btn-secondary";
            decrementButton.style.cssText = "padding: 2px 8px; cursor: pointer;";
            wrapper.appendChild(decrementButton);
            incrementButton.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                let newValue = (parseInt(display.textContent, 10) + 1) % (max + 1);
                display.textContent = newValue < 10 ? `0${newValue}` : newValue;
            });
            decrementButton.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                let newValue = (parseInt(display.textContent, 10) - 1 + (max + 1)) % (max + 1);
                display.textContent = newValue < 10 ? `0${newValue}` : newValue;
            });
            return wrapper;
        };
        const hourBox = createTimeBox("Hour", hour, 23);
        const minuteBox = createTimeBox("Minute", minute, 59);
        const secondBox = createTimeBox("Second", second, 59);
        timeBoxesContainer.appendChild(hourBox);
        timeBoxesContainer.appendChild(minuteBox);
        timeBoxesContainer.appendChild(secondBox);
        timePickerContainer.appendChild(timeBoxesContainer);
        const buttonsContainer = document.createElement("div");
        buttonsContainer.style.cssText = "display: flex; gap: 5px; justify-content: flex-end;";
        const cancelButton = document.createElement("button");
        cancelButton.textContent = _t("Cancel");
        cancelButton.className = "btn btn-secondary btn-sm";
        buttonsContainer.appendChild(cancelButton);
        const confirmButton = document.createElement("button");
        confirmButton.textContent = _t("Set Time");
        confirmButton.className = "btn btn-primary btn-sm";
        buttonsContainer.appendChild(confirmButton);
        timePickerContainer.appendChild(buttonsContainer);
        document.body.appendChild(timePickerContainer);
        const closePicker = () => {
            if (document.body.contains(timePickerContainer)) document.body.removeChild(timePickerContainer);
        };
        cancelButton.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            closePicker();
        });
        confirmButton.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            const selectedTime = `${hourBox.querySelector('.time-box-display').textContent}:${minuteBox.querySelector('.time-box-display').textContent}:${secondBox.querySelector('.time-box-display').textContent}`;
            this.props.record.update({[this.props.name]: selectedTime});
            closePicker();
        });
        const handleOutsideClick = (e) => {
            if (!timePickerContainer.contains(e.target) && e.target !== timePicker) {
                closePicker();
                document.removeEventListener("click", handleOutsideClick);
            }
        };
        setTimeout(() => {document.addEventListener("click", handleOutsideClick);}, 100);
    }
}

export const TimePickerField = {
    component: FieldTimePicker,
    supportedTypes: ["char"],
};

registry.category("fields").add("timepicker", TimePickerField);
