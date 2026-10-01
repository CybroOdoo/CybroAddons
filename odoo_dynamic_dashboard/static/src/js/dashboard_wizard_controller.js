/** @odoo-module **/

/**
 * Cybrosys Technologies Pvt. Ltd.
 *
 * Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
 * Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
 *
 * This program is under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
 * (AGPL v3), Version 3.
 */


import { formView } from '@web/views/form/form_view';
import { registry } from '@web/core/registry';
import { onMounted, useComponent } from '@odoo/owl';

// 1. Define your custom controller
export class DashboardWizardController extends formView.Controller {
    setup() {
        super.setup();

        // 2. After the component is mounted in the DOM...
        onMounted(() => {
            const modalContent = this.rootRef.el.closest('.modal-content')

                if (modalContent) {
                modalContent.classList.add('advanced-dashboard-wizard-modal-content');
            }
        });
    }
}

// 3. Register the controller with a unique name
registry.category('views').add('advanced_dashboard_wizard', {
    ...formView,
    Controller: DashboardWizardController,
});