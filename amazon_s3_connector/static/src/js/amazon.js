/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class AmazonDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");

        this.state = useState({
            files: [],
            search: "",
            filter: "ALL FILES",
        });

        onWillStart(async () => {
            await this.fetch_data();
        });
    }

    async fetch_data() {
        const result = await this.orm.call(
    "amazon.dashboard",
    "amazon_view_files",
    [[]]   // ✅ REQUIRED
);


        if (!result) {
            return this.notify("Please setup Amazon S3 Access Keys");
        }

        if (result[0] === "e") {
            return this.notify(`Failed to Load Files [ ${result[1]} ]`);
        }

        this.state.files = result.map((f, index) => ({
            index: index + 1,
            name: f[0],
            url: f[1],
            size: f[2],
            date: f[3],
            owner: f[4],
            ext: f[0].split(".").pop().toLowerCase(),
        }));
    }

    notify(message) {
        this.actionService.doAction({
            type: "ir.actions.client",
            tag: "display_notification",
            params: {
                message,
                type: "warning",
            },
        });
    }

    /* ---------- Sorting ---------- */

    sort_name() {
        this.state.files.sort((a, b) => a.name.localeCompare(b.name));
    }

    sort_number() {
        this.state.files.sort((a, b) => a.index - b.index);
    }

    /* ---------- Search & Filter ---------- */

    search_file(ev) {
        this.state.search = ev.target.value.toLowerCase();
    }

    filter_files(ev) {
        this.state.filter = ev.target.value;
    }

    get filteredFiles() {
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

    upload() {
        this.actionService.doAction({
            name: "Upload File",
            type: "ir.actions.act_window",
            res_model: "amazon.upload.file",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }
}

AmazonDashboard.template = "AmazonDashboard";
registry.category("actions").add("amazon_dashboard", AmazonDashboard);
