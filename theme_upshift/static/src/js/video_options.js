/** @odoo-module **/
import { BuilderAction } from "@html_builder/core/builder_action";
import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { withSequence } from "@html_editor/utils/resource";
import { SNIPPET_SPECIFIC } from "@html_builder/utils/option_sequence";

class VideoOptionPlugin extends Plugin {
    static id = "videoOption";
    resources = {
        builder_options: [
            withSequence(SNIPPET_SPECIFIC, {
                template: "theme_upshift.videoOption",
                selector: ".media_iframe_video",
            }),
        ],
        builder_actions: {
            VideoUpdateSrcAction,
        },
    };
}

export class VideoUpdateSrcAction extends BuilderAction {
    static id = "videoUpdateSrc";
    apply({ editingElement }) {
        const iframe = editingElement.querySelector("iframe");
        const url = editingElement.dataset.oeExpression;
        if (iframe && url) {
            if (url !== iframe.getAttribute("src")) {
                iframe.setAttribute("src", url);
                editingElement.dataset.src = url;
            }
        }
    }
}

registry.category("website-plugins").add(VideoOptionPlugin.id, VideoOptionPlugin);
