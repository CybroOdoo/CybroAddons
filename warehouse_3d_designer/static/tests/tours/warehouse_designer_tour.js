import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("warehouse_3d_designer_remove_location", {
    steps: () => [
        {
            content: "Select the placed location",
            trigger: ".o_placed_list .list-group-item:contains(Tour Rack)",
            run: "click",
        },
        {
            content: "Remove it from the layout",
            trigger: ".o_warehouse_content button:contains(Remove)",
            run: "click",
        },
        {
            content: "It is offered as an unplaced location again",
            trigger: ".o_warehouse_content .list-group-item:contains(Tour Rack)",
        },
        {
            content: "Save the layout",
            trigger: "button:enabled:contains(Save)",
            run: "click",
        },
        {
            content: "The save is confirmed",
            trigger: ".o_notification:contains(Layout saved)",
        },
    ],
});

registry.category("web_tour.tours").add("warehouse_3d_designer_read_only_map", {
    steps: () => [
        {
            content: "The map shows the placed location",
            trigger: ".o_placed_list .list-group-item:contains(Tour Rack)",
        },
        {
            content: "The canvas is displayed",
            trigger: ".o_warehouse_canvas_wrapper canvas",
        },
        {
            content: "The editing tools are hidden",
            trigger: ".o_warehouse_content:not(:has(.o_map_objects))",
        },
    ],
});
