# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technogies @cybrosys(odoo@cybrosys.com)
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
#############################################################################
from odoo import api, fields, models


class CarRentalChecklist(models.Model):
    """Model to add the checklist of rental"""
    _name = 'car.rental.checklist'

    name = fields.Many2one('car.tools', string="Name")
    checklist_active = fields.Boolean(string="Available", default=True)
    checklist_number = fields.Many2one('car.rental.contract',
                                       string="Checklist Number")
    price = fields.Float(string="Price")

    @api.onchange('name')
    def onchange_name(self):
        """
           Update the price based on the selected name.
        """
        self.price = self.name.price
