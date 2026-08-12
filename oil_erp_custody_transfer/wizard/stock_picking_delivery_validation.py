# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
# ############################################################################

from odoo import api, models

class StockPickingDeliveryValidationWizard(models.TransientModel):
    """Auto-populate measurement fields from the linked custody transfer."""
    _inherit = "stock.picking.delivery.validation.wizard"

    @api.model
    def default_get(self, fields_list):
        """Executes the 'default get' process within the operational workflow."""
        res = super().default_get(fields_list)
        picking = self.env["stock.picking"].browse(
            self.env.context.get("default_picking_id"))
        if picking and picking.custody_transfer_id:
            res.update(picking.custody_transfer_id._get_wizard_measurement_defaults())
        return res
