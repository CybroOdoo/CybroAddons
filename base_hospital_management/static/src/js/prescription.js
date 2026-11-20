import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class PrescriptionWidget extends Interaction {
    static selector = "#my_prescriptions";
    dynamicContent = {
        ".pr_download": {
            "t-on-click": this.onDownloadClick,
        },
    };

    async onDownloadClick(ev) {
        const recId = ev.currentTarget.dataset.id;
        if (!recId) {
            return;
        }
        const result = await this.waitFor(
            rpc("/my/op/prescription/download", {
                op_id: parseInt(recId, 10),
            })
        );
        if (result?.url) {
            window.open(result.url, "_blank");
        }
    }
}

registry
    .category("public.interactions")
    .add("base_hospital_management.prescription", PrescriptionWidget);