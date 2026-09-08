# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Extends Settings with waste sorting basis and inventory location parameters."""
    _inherit = 'res.config.settings'

    use_batch_inspection = fields.Boolean(
        string="Batch Inspection",
        config_parameter='wm_collection.use_batch_inspection',
        help="Enable batch inspection functionality."
    )
    use_quality_grading = fields.Boolean(
        string="Quality Grading",
        config_parameter='wm_collection.use_quality_grading',
        help="Enable quality grading for waste batches."
    )
    use_hazardous_waste = fields.Boolean(
        string="Hazardous Waste Management",
        config_parameter='wm_collection.use_hazardous_waste',
        help="Enable hazardous waste tracking."
    )
    use_batch_labels = fields.Boolean(
        string="Batch Labels",
        config_parameter='wm_collection.use_batch_labels',
        default=False,
        help="Enable batch label printing."
    )
    use_batch_approval = fields.Boolean(
        string="Batch Approval Workflow",
        config_parameter='wm_collection.use_batch_approval',
        help="Require batch inspection approval before receiving into stock."
    )

    wm_sort_based_on = fields.Selection([
        ('material', 'Waste Material'),
        ('category_and_material', 'Waste Category and Material')
    ], string="Sort Based On", config_parameter='wm_collection.wm_sort_based_on', default='material')

    group_sort_by_material = fields.Boolean(
        "Sort by Material Group",
        implied_group='wm_collection.group_sort_by_material'
    )
    group_sort_by_category = fields.Boolean(
        "Sort by Category Group",
        implied_group='wm_collection.group_sort_by_category'
    )

    @api.onchange('wm_sort_based_on')
    def _onchange_wm_sort_based_on(self):
        """
        React to changes in the waste sorting basis setting (by category vs. by
        material) and clear conflicting sort configurations to maintain
        settings consistency.
        """
        if self.wm_sort_based_on == 'material':
            self.group_sort_by_material = True
            self.group_sort_by_category = False
        elif self.wm_sort_based_on == 'category_and_material':
            self.group_sort_by_material = False
            self.group_sort_by_category = True

    @api.model
    def get_values(self):
        """
        Read all inventory-level waste management sorting and stock location
        configuration from ir.config_parameter to populate the Inventory >
        Settings form.
        """
        res = super(ResConfigSettings, self).get_values()
        sort_mode = self.env['ir.config_parameter'].sudo().get_param('wm_collection.wm_sort_based_on', default='material')
        res.update(
            wm_sort_based_on=sort_mode,
            group_sort_by_material=(sort_mode == 'material'),
            group_sort_by_category=(sort_mode == 'category_and_material'),
        )
        return res

    def set_values(self):
        """
        Persist inventory-level waste management settings (sort basis, default
        incoming location, lot tracking preference) to ir.config_parameter on
        form save.
        """
        super(ResConfigSettings, self).set_values()
        group_material = self.env.ref('wm_collection.group_sort_by_material', raise_if_not_found=False)
        group_category = self.env.ref('wm_collection.group_sort_by_category', raise_if_not_found=False)
        group_operator = self.env.ref('wm_base.group_wm_inventory_operator', raise_if_not_found=False)

        if group_operator and group_material and group_category:
            if self.wm_sort_based_on == 'category_and_material':
                group_operator.sudo().write({'implied_ids': [(4, group_category.id), (3, group_material.id)]})
            else:
                group_operator.sudo().write({'implied_ids': [(4, group_material.id), (3, group_category.id)]})

        # Sync menu visibility
        menu_inspection = self.env.ref('wm_collection.menu_wm_batch_inspection', raise_if_not_found=False)
        if menu_inspection:
            menu_inspection.active = self.use_batch_inspection

        report_label = self.env.ref('wm_collection.action_waste_batch_label', raise_if_not_found=False)
        if report_label:
            # We can't toggle active on report easily unless it's ir.actions.report, wait, it is!
            report_label.binding_model_id = self.env['ir.model']._get('waste.batch').id if self.use_batch_labels else False
