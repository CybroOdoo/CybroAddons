# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    """
    Extend system settings to manage POS print template functionality.

    This configuration enables or disables custom POS receipt templates.
    When enabled:
    - The current user is added to the POS template access group.
    - A default POS print template is automatically created if none exists.
    """
    _inherit = "res.config.settings"

    enable_pos_templates = fields.Boolean(
        string="Enable POS Print Templates",
        config_parameter="direct_print_pos.enable_pos_templates",
    )

    def set_values(self):
        res = super().set_values()

        group = self.env.ref("direct_print_pos.group_pos_print_template",
                             raise_if_not_found=False)
        if self.enable_pos_templates:
            if group and group not in self.env.user.group_ids:
                self.env.user.group_ids = [(4, group.id)]
            self._create_default_pos_template()
        elif group and group in self.env.user.group_ids:
            self.env.user.group_ids = [(3, group.id)]
        return res

    def _create_default_pos_template(self):
        Template = self.env["pos.print.template"].sudo()

        if Template.search_count([("is_default", "=", True)]) > 0:
            return

        report = self.env.ref(
            "direct_print_pos.action_report_pos_receipt_direct_print",
            raise_if_not_found=False,
        )
        if not report:
            return

        Template.create({
            "name": "Default POS Receipt",
            "report_id": report.id,
            "is_default": True,
        })
