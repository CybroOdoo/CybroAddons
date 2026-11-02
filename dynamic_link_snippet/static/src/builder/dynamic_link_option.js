import { BaseOptionComponent } from "@html_builder/core/base_option_component";
import { registry } from "@web/core/registry";

export class DynamicLinkOption extends BaseOptionComponent {
    static id = "dynamic_link_option";
    static template = "dynamic_link_snippet.DynamicLinkOption";
}

registry.category("builder-options").add(DynamicLinkOption.id, DynamicLinkOption);
