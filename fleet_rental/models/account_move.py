#############################################################################
#
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
#############################################################################
from odoo import fields, models


class AccountMove(models.Model):
    """Inherit account.move to add extra field """
    _inherit = 'account.move'

    fleet_rent_id = fields.Many2one(comodel_name='car.rental.contract',
                                    string='Rental',
                                    help='Invoice related to which '
                                         'rental record')

    is_first_invoice = fields.Boolean(string='Is First Rental Invoice', default=False,
                                      help='Is First Rental Invoice')

    def button_cancel(self):
        """
            Override the base method button_cancel to handle additional logic
            for 'car.rental.contract' model based on 'fleet_rent_id'.
        """
        res = super().button_cancel()
        fleet_model = self.env['car.rental.contract'].search(
            [('id', '=', self.fleet_rent_id.id)])
        if fleet_model.state == 'running':
            fleet_model.state = 'running'
            fleet_model.first_invoice_created = False
        else:
            fleet_model.state = 'checking'
        return res
