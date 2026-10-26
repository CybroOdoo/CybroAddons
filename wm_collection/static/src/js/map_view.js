/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { MapController } from "./map_controller";
import { MapModel } from "./map_model";
import { MapRenderer } from "./map_renderer";

import { MapArchParser } from "./map_arch_parser";

// Registered as its own view type ("wm_map") so it coexists with the
// Enterprise `web_map` view instead of overriding the global "map" type.
export const mapView = {
    type: "wm_map",
    display_name: _t("Map"),
    Controller: MapController,
    Renderer: MapRenderer,
    Model: MapModel,
    ArchParser: MapArchParser,
    icon: "fa fa-map-marker",
    multiRecord: true,
    searchMenuTypes: ["filter", "groupBy", "comparison", "favorite"],

    props: (genericProps, view) => {
        const { ArchParser } = view;
        const { arch, relatedModels, resModel } = genericProps;
        const archInfo = new ArchParser().parse(arch, relatedModels, resModel);
        return {
            ...genericProps,
            Model: view.Model,
            Renderer: view.Renderer,
            archInfo,
        };
    },
};

registry.category("views").add("wm_map", mapView);


