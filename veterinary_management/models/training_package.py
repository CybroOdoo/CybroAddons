# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Shalfa P (odoo@cybrosys.com)
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


class TrainingPackage(models.Model):
    """
    Model to store Training Packages Types in veterinary management system.
    """
    _name = 'training.package'
    _description = 'Training Package'
    _inherit = 'mail.thread'

    name = fields.Char(string="Package Name", help="Name of the training package")
    pet_type_id = fields.Many2one(string="Pet Type", comodel_name="animal.types", help="Type of pet for this training package")
    service_type = fields.Selection([('at_home', 'At Home'), ('at_center', 'At Center')], default="at_center",
                                    help="Type of service for the training package")
    inclusion_ids = fields.Many2many(string="Inclusion", comodel_name="training.inclusion", help="Items included in the training package")
    days = fields.Integer(string="Days", help="Number of days for the training package")
    currency_id = fields.Many2one(comodel_name="res.currency",
                                  default=lambda self: self.env.company.currency_id.id)
    charge = fields.Monetary(string="Charge", help="Cost charged for the training package")
    exclusion_ids = fields.Many2many(string="Exclusion", comodel_name="training.exclusion", help="Items excluded from the training package")
