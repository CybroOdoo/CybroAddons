import { Component, onWillStart, proxy, status } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class DropboxDashboard extends Component {
    static template = "dropbox_integration.DropboxDashboard";

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = proxy({
            files: [],
            searchQuery: "",
        });

        onWillStart(async () => {
            await this.loadFiles();
        });
    }

    get filteredFiles() {
        const query = this.state.searchQuery.trim().toLowerCase();
        if (!query) {
            return this.state.files;
        }
        return this.state.files.filter((file) =>
            file.name.toLowerCase().includes(query)
        );
    }

    async loadFiles() {
        const result = await this.orm.call("dropbox.dashboard", "action_import_files", [""]);
        if (status(this) === "destroyed") {
            return;
        }
        if (Array.isArray(result) && result[0] === "e") {
            this.state.files = [];
            this.actionService.doAction({
                type: "ir.actions.client",
                tag: "display_notification",
                params: {
                    message: _t("Failed to load files [ %s ]", result[1]),
                    type: "warning",
                    sticky: false,
                },
            });
        } else if (!result) {
            this.state.files = [];
            this.actionService.doAction({
                type: "ir.actions.client",
                tag: "display_notification",
                params: {
                    message: _t("Please set up the Access Token"),
                    type: "warning",
                    sticky: false,
                },
            });
        } else {
            this.state.files = Object.entries(result).map(([name, url]) => ({
                name,
                url,
            }));
        }
    }

    onImageError(ev) {
        ev.target.onerror = null;
        ev.target.src = "/dropbox_integration/static/src/img/file.png";
    }

    search_file(ev) {
        this.state.searchQuery = ev.target.value || "";
    }

    async upload() {
        await this.actionService.doAction(
            {
                name: _t("Upload to Dropbox"),
                type: "ir.actions.act_window",
                res_model: "dropbox.upload",
                view_mode: "form",
                views: [[false, "form"]],
                target: "new",
            },
            {
                onClose: async () => {
                    await this.loadFiles();
                },
            }
        );
    }
}

registry.category("actions").add("dropbox_dashboard", DropboxDashboard);
