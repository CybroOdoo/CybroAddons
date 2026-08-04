/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { MapController } from "./map_controller";
import { MapModel } from "./map_model";
import { MapRenderer } from "./map_renderer";

import { MapArchParser } from "./map_arch_parser";

export const mapView = {
    type: "map",
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

registry.category("views").add("map", mapView);
