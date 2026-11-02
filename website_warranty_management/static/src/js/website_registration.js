import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class WarrantyClaim extends Interaction {
    static selector = ".warranty-claim-widget";
}

registry
    .category("public.interactions")
    .add("website_warranty_management.WarrantyClaim", WarrantyClaim);