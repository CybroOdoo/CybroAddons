# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anagha S (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, models


class MachineRepair(models.Model):
    """Machine repair inherited model."""
    _inherit = 'machine.repair'

    @api.model
    def barcode_search(self, args):
        """Repair Product is identified and added to repair order."""
        product = self.env['product.product'].search([('barcode', '=', args[0])])
        if not product:
            return False
        else:
            repair_order = self.browse(args[1])
            if args[2] == 'machine':
                repair_order.write({'machine_id': product.id})
            else:
                consume_part = repair_order.consume_part_id.filtered(
                    lambda rec: rec.machine_id.id == product.id)
                if consume_part:
                    consume_part.write({'qty': consume_part.qty + 1})
                else:
                    consume_part.create({
                        'machine_id': product.id,
                        'consume_id': repair_order.id,
                        'qty': 1})
            return True
