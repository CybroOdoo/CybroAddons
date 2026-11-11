/** @odoo-modules */
import { Component, onMounted, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class OnedriveDashboard extends Component {
    static template = "onedrive_integration_odoo.OnedriveDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.state = proxy({
            allFiles: [],
            displayedFiles: [],
            activeFilter: "allfiles",
        });

        onMounted(() => {
            this.synchronize();
        });
    }

    /**
     * Opens a file upload wizard.
     */
    async upload() {
        this.action.doAction({
            name: "Upload File",
            type: "ir.actions.act_window",
            res_model: "upload.file",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }

    /**
     * Retrieves and displays files from OneDrive.
     */
    async synchronize() {
        const result = await this.orm.call(
            "onedrive.dashboard",
            "action_synchronize_onedrive",
            []
        );

        if (!result) {
            this.notification.add("Please setup credentials.", {
                type: "warning",
            });
            return;
        }

        if (Array.isArray(result) && result[0] === "error") {
            const message =
                result[1] === "itemNotFound"
                    ? "Error: Folder not found."
                    : `Error: ${result[2]}`;
            this.notification.add(message, {
                type: "warning",
            });
            return;
        }

        const files = Object.entries(result).map(([name, url]) => ({
            name,
            url,
            extension: name.split(".").pop().toLowerCase(),
        }));

        this.state.allFiles = files;
        this.applyFilter(this.state.activeFilter);
    }

    /**
     * Filters files displayed based on file type.
     * @param {string} filter
     */
    filterFileType(filter) {
        this.state.activeFilter = filter;
        this.applyFilter(filter);
    }

    applyFilter(filter) {
        if (filter === "allfiles") {
            this.state.displayedFiles = this.state.allFiles;
        } else if (filter === "image") {
            const imageExts = ["jpg", "jpeg", "png", "gif", "webp", "svg"];
            this.state.displayedFiles = this.state.allFiles.filter((f) =>
                imageExts.includes(f.extension)
            );
        } else {
            this.state.displayedFiles = this.state.allFiles.filter(
                (f) => f.extension === filter
            );
        }
    }
}

registry.category("actions").add("onedrive_dashboard", OnedriveDashboard);
