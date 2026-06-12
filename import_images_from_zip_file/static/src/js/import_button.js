/** @odoo-module **/

import { ListController } from '@web/views/list/list_controller';
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { _t } from 'web.core';

/**
 * Custom ListController to add a new "Import Images" button
 * and open a modal form view (wizard) when clicked.
 */
export class ImportWizard extends ListController {
    /**
     * Setup method called during component initialization.
     * You can use this to initialize custom variables or logic.
     */
    setup() {
        super.setup();
        // Additional setup logic (if needed) can go here
    }

    /**
     * Handler for the "Import Images" button click event.
     * Triggers a new window action to open a form view of 'import.image'.
     */
    onClickImportImages() {
        console.log(this);  // For debugging: log the controller instance

        this.actionService.doAction({
            _name: _t('View Wizard'), // Translatable name for the action
            type: 'ir.actions.act_window', // Indicates opening a form view in a modal
            res_model: 'import.image', // Model to use in the form
            views: [[false, 'form']], // Default view: form
            view_mode: 'form', // Only show form view
            context: {
                // Set default context values for the form
                default_model_template: this.model.rootParams.resModel,
            },
            target: 'new', // Open the form as a modal dialog
        });
    }
}

/**
 * Register the custom list view with extended controller
 * and button template for showing the "Import Images" button.
 */
registry.category("views").add("import_button_in_tree", {
    ...listView,
    Controller: ImportWizard,
    buttonTemplate: "import_images_from_zip_file.ListView.Buttons",
});
