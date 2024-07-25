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
from odoo import api, fields, models


class ServicePackage(models.Model):
    """Class to add car service package"""
    _name = "service.package"
    _description = "Service Package"

    name = fields.Char(
        string="Service Name", required=True, help="Enter service package name")
    service_ids = fields.One2many(
        "service.line",
        "service_package_id",
        string="Service Line",
        help="Select the services associated with " "this record.")
    total = fields.Monetary(
        string="Total",
        compute="compute_total",
        store=True,
        help="Service package total amount")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id.id,
        help="Select the company to which this record " "belongs.")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        help="The currency used by the company.")

    @api.depends("service_ids.price")
    def compute_total(self):
        """Function to calculate total of service line"""
        for record in self:
            record.total = sum(self.service_ids.mapped("price"))
