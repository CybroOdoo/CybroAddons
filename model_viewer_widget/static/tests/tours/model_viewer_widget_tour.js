import { registry } from "@web/core/registry";

const MODEL_URL = "/model_viewer_widget/static/src/assets/3d.glb";

// Starts like a GLB 2.0 file, but it is not a model
const DAMAGED_MODEL = "glTF\x02 damaged";

async function uploadFile(name, content) {
    const data = content ?? (await (await fetch(MODEL_URL)).blob());
    const file = new File([data], name);
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    const input = document.querySelector(".o_field_3d .o_input_file");
    input.files = dataTransfer.files;
    input.dispatchEvent(new Event("change", { bubbles: true }));
}

registry.category("web_tour.tours").add("model_viewer_widget_tour", {
    steps: () => [
        {
            content: "Open the 3D model viewer page",
            trigger: ".nav-link[name='model_3d_viewer']",
            run: "click",
        },
        {
            content: "The viewer has started on its full size",
            trigger: ".o_field_3d_viewer canvas:not([width='300'])",
        },
        {
            content: "The sample model has been loaded",
            trigger: ".o_field_3d:not(:has(.alert-danger))",
        },
        {
            content: "Nothing can be cleared yet",
            trigger: ".o_field_3d:not(:has(.o_clear_file_button))",
        },
        {
            content: "Upload a file which is not a GLB model",
            trigger: ".o_field_3d .o_select_file_button",
            run: () => uploadFile("model.txt"),
        },
        {
            content: "The file is refused",
            trigger: ".o_notification:contains('Only GLB 3D models are supported.')",
        },
        {
            content: "Upload a damaged GLB model",
            trigger: ".o_field_3d .o_select_file_button",
            run: () => uploadFile("damaged.glb", DAMAGED_MODEL),
        },
        {
            content: "The failure is reported in the widget, not in an error dialog",
            trigger: ".o_field_3d .alert-danger",
        },
        {
            content: "Upload a GLB model",
            trigger: ".o_field_3d .o_select_file_button",
            run: () => uploadFile("model.glb"),
        },
        {
            content: "The uploaded model is ready to be saved",
            trigger: ".o_field_3d .o_clear_file_button",
        },
        {
            content: "The uploaded model is displayed",
            trigger: ".o_field_3d:not(:has(.alert-danger))",
        },
        {
            content: "Save the product",
            trigger: ".o_form_button_save",
            run: "click",
        },
        {
            content: "The product is saved",
            trigger: ".o_form_saved",
        },
    ],
});
