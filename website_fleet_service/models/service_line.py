# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Raneesha MK (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class ServiceLine(models.Model):
    """Class to add related field"""

    _name = "service.line"
    _description = "Service Line"

    service_package_id = fields.Many2one(
        "service.package", string="service Package",
        help="Select service package")
    service_type_id = fields.Many2one(
        "service.type",
        string="Service Type",
        help="Add service type include " "in this package",
        required=True)
    price = fields.Monetary(
        string="Price", related="service_type_id.amount",
        help="Service type price")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id.id,
        help="Select the company to which this record belongs.")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        help="The currency used by the company.")
