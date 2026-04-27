/** @odoo-module **/
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { onWillStart, onMounted, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
const actionRegistry = registry.category("actions");

export class DropboxDashboard extends Component {
    setup() {
        super.setup(...arguments);
        this.orm = useService('orm');
        this.actionService = useService("action");
        this.rootRef = useRef("root");

        onWillStart(async () => {
            this.files = await this.orm.call('dropbox.dashboard', 'action_import_files', ['']);
        });

        onMounted(() => {
            this.renderFiles();
        });
    }

    /* Renders files in the div#files once the DOM is available */
    renderFiles() {
        const filesContainer = document.getElementById('files');

        if (!filesContainer) {
            console.error("filesContainer not found in the DOM.");
            return;
        }

        if (this.files[0] === 'e') {
            this.actionService.doAction({
                type: 'ir.actions.client',
                tag: 'display_notification',
                params: {
                    message: 'Failed to Load Files [ ' + this.files[1] + ' ]',
                    type: 'warning',
                    sticky: false,
                }
            });
        } else if (!this.files) {
            this.actionService.doAction({
                type: 'ir.actions.client',
                tag: 'display_notification',
                params: {
                    message: 'Please setup Access Token',
                    type: 'warning',
                    sticky: false,
                }
            });
        } else {
            filesContainer.innerHTML = ''; // Empty the container

            const altSrc = 'dropbox_integration/static/src/img/file.png';
            Object.keys(this.files).forEach((name) => {
                const fileElement = `
                    <div class="col-sm-6 card dropbox_card" align="center">
                        <a class="card-image-text dropbox_text" href="${this.files[name]}">
                            <img class="card-img-top drop_box_image" align="center" src="${this.files[name]}" onerror="this.src='${altSrc}'"/>
                            <br/><br/>${name}
                        </a>
                    </div>`;
                filesContainer.insertAdjacentHTML('beforeend', fileElement);
            });
        }
    }

    /* Search console function */
    search_file(ev) {
        const searchInput = document.querySelector('.header-search-input');
        const value = searchInput.value.trim().toLowerCase();  // Remove extra spaces and lowercase
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            const text = card.textContent.trim().toLowerCase();  // Clean up textContent
            // Toggle visibility based on whether the search value is found in the card text
            if (text.includes(value)) {
                card.classList.remove('hidden');  // Show the card
            } else {
                card.classList.add('hidden');  // Hide the card
            }
        });
    }

    /* Calls upload function on click of upload */
    upload(ev) {
        this.actionService.doAction({
            name: "Upload to Dropbox",
            type: 'ir.actions.act_window',
            res_model: 'dropbox.upload',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            target: 'new',
        });
    }
}
DropboxDashboard.template = "DropboxDashboard";
registry.category("actions").add("dropbox_dashboard", DropboxDashboard);
