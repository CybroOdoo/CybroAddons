console.log('entered')
/* @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, useState } from "@odoo/owl";
import {registry} from '@web/core/registry';


export class DbRestoreDashboard extends Component {
    setup() {
        super.setup(...arguments);
        this.dbDashboard = useState({
            data: []
        })
        this.orm = useService("orm");
        this.action = useService("action");
        onMounted(async () => {
            await this.loadDashboardData();
        });
    }
    async loadDashboardData() {
        const database_file = await this.orm.call(
            'database.manager',
            'action_import_files',
            []
        );
        if (database_file[0] == 'error') {
            this.action.doAction({
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Failed to Load Files from ' + database_file[2] + ' [ ' + database_file[1] + ' ]',
                    'type': 'warning',
                    'sticky': false,
                }
            });
        } else {
            this.dbDashboard.data = Object.entries(database_file[0]).map(([file_name, values]) => {
                return {
                    'file_name': file_name,
                    'values': values
                };
            });
        }
    }
    //    Function for restore the database
    _onClick_restore(ev) {
        this.action.doAction({
            name: "Restore Database",
            type: 'ir.actions.act_window',
            res_model: 'database.restore',
            view_mode: 'form',
            view_type: 'form',
            views: [
                [false, 'form']
            ],
            context: {
                default_db_file: ev.target.value,
                default_backup_location: ev.target.dataset.location
            },
            target: 'new',
        });
    }
    isValidBackupName(name) {
        return ['Dropbox', 'OneDrive', 'Google Drive', 'Nextcloud', 'AmazonS3'].includes(name)
    }
    //    Filter for location
    _onchange_location(ev) {
        var selectedLocation = ev.target.value;
        var rows = document.querySelectorAll('#db_restore_table tbody tr');

        rows.forEach(function(row) {
            var backupLocation = row.children[2].innerText.trim();

            if (selectedLocation === 'all_backups') {
                row.style.display = ''; // Show all rows
            } else if (backupLocation !== selectedLocation) {
                row.style.display = 'none'; // Hide rows that don't match the filter
            } else {
                row.style.display = ''; // Show rows that match the filter
            }
        });
    }
}
registry.category("actions").add("database_manager_dashboard", DbRestoreDashboard);
DbRestoreDashboard.components = {
    DbRestoreDashboard
};
DbRestoreDashboard.template = 'database_manager_dashboard.DbRestoreDashboard';