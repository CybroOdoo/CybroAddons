import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { Component, onWillStart, proxy } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class AmazonDashboard extends Component {
    static template = "amazon_s3_connector.AmazonDashboard";

    /**
     * Initializes the component, sets up services, and defines the initial state.
     * Uses Owl 3's proxy for reactive state management.
     */
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notification = useService("notification");
        this.state = proxy({
            files: [],
            search: "",
            filter: "ALL FILES",
        });
        onWillStart(async () => {
            await this.fetch_data();
        });
    }

    /**
     * Fetches S3 file data from the server using the ORM service.
     * Maps the raw data into a structured format for the component state.
     * @returns {Promise<void>}
     */
    async fetch_data() {
        const result = await this.orm.call(
            "amazon.dashboard",
            "amazon_view_files"
        );
        if (!result) {
            return this.notify(
                _t("Please set up the Amazon S3 access keys in Settings.")
            );
        }
        if (result[0] === "e") {
            return this.notify(
                _t("Failed to load the files (%s)", result[1])
            );
        }
        this.state.files = result.map((f, index) => ({
            index: index + 1,
            name: f[0],
            url: f[1],
            size: f[2],
            date: f[3],
            type: f[4],
            ext: f[0].split(".").pop().toLowerCase(),
        }));
    }

    /**
     * Displays a warning notification to the user.
     * @param {string} message - The message to display.
     */
    notify(message) {
        this.notification.add(message, {
            type: "warning",
        });
    }

    /* ---------- Sorting ---------- */
    /**
     * Sorts the file list alphabetically by name.
     */
    sort_name() {
        this.state.files = [...this.state.files].sort((a, b) => a.name.localeCompare(b.name));
    }

    /**
     * Sorts the file list by their original index.
     */
    sort_number() {
        this.state.files = [...this.state.files].sort((a, b) => a.index - b.index);
    }

    /* ---------- Search & Filter ---------- */
    /**
     * Updates the search state based on the user input.
     * @param {Event} ev - The input event.
     */
    search_file(ev) {
        this.state.search = ev.target.value.toLowerCase();
    }

    /**
     * Updates the file filter state based on the user selection.
     * @param {Event} ev - The change event.
     */
    filter_files(ev) {
        this.state.filter = ev.target.value;
    }

    /**
     * Computed property that returns a filtered list of files based on
     * the current search query and category filter.
     * @returns {Array<Object>}
     */
    get filteredFiles() {
        if (!this.state || !Array.isArray(this.state.files)) {
            return [];
        }
        return this.state.files.filter((file) => {
            if (
                this.state.search &&
                !file.name.toLowerCase().includes(this.state.search)
            ) {
                return false;
            }
            const f = this.state.filter;
            if (f === "ALL FILES") return true;
            if (f === "image") return ["jpg", "jpeg", "png"].includes(file.ext);
            if (f === "txt") return ["txt", "docx"].includes(file.ext);
            return file.ext === f.toLowerCase();
        });
    }

    /* ---------- Upload ---------- */
    /**
     * Opens the S3 file upload wizard.
     */
    upload() {
        this.actionService.doAction({
            name: _t("Upload File"),
            type: "ir.actions.act_window",
            res_model: "amazon.upload.file",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }
}

registry.category("actions").add("amazon_dashboard", AmazonDashboard);
