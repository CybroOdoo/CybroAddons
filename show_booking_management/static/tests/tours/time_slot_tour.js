import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("show_booking_time_slot_tour", {
    steps: () => [
        {
            content: "The OWL 3 time picker widget is rendered on the time slot form",
            trigger: ".o_form_view .timepicker-component input.time-input",
            // hoot's `edit` cannot drive an <input type="time"> (getNodeValue reads
            // valueAsDate on it): set the value and blur it like a user leaving the field.
            run({ anchor }) {
                anchor.value = "21:30";
                anchor.dispatchEvent(new Event("input", { bubbles: true }));
                anchor.dispatchEvent(new FocusEvent("blur"));
            },
        },
        {
            content: "Save the time slot",
            trigger: ".o_form_button_save",
            run: "click",
        },
        {
            content: "The picked time was committed to the record (name derived on create)",
            trigger: ".o_form_view .o_field_widget[name='name']:contains('09:30 PM')",
        },
    ],
});
