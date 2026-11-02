import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("website_return_management_tour", {
    steps: () => [
        {
            content: "Wait for the frontend JavaScript to be ready",
            trigger: "body[is-ready='true']",
        },
        {
            content: "The Return button is shown for a delivered order",
            trigger: "#hidden_box_btn",
            run: "click",
        },
        {
            content: "The Interaction opened the return modal",
            trigger: "#hidden_box.show",
        },
        {
            content: "Pick a product in the return form",
            trigger: "#hidden_box #product",
            run: "selectByLabel Test Product",
        },
        {
            content: "Picking a product reveals the Submit button",
            trigger: "#hidden_box #submit:not(.d-none)",
        },
        {
            content: "Picking None again hides the Submit button",
            trigger: "#hidden_box #product",
            run: "selectByLabel None",
        },
        {
            content: "Submit button hidden again",
            trigger: "#hidden_box #submit.d-none:not(:visible)",
        },
    ],
});
