# -- coding: utf-8 --
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import fields, models


class SalonService(models.Model):
    """Creates 'salon.service' to store salon services"""
    _name = 'salon.service'
    _description = 'Salon Service'

    name = fields.Char(string="Name", required=True, help="Name of service")
    currency_id = fields.Many2one(comodel_name='res.currency',
                                  string='Currency', required=True,
                                  default=lambda self: self.env
                                  .user.company_id.currency_id.id,
                                  help="Currency for the service")
    price = fields.Monetary(string="Price", help="Amount for the service",
                            required=True)
    time_taken = fields.Float(string="Time", help="Approximate time required "
                                                  "for this service in Hours")
