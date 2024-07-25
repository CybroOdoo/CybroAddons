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


class ServiceWorksheet(models.Model):
    """Class to add car service worksheet"""
    _name = "service.worksheet"
    _description = "Service Worksheet"
    _rec_name = "model_id"

    service_type_id = fields.Many2one(
        "service.type",
        string="Service Type",
        required=True,
        help="select the service package",
    )
    model_id = fields.Many2one(
        "fleet.vehicle.model",
        string="Vehicle Model",
        domain=[("vehicle_type", "=", "car")],
        help="Select the Car model",
    )
    user_id = fields.Many2one(
        "res.users", string="Assigned to", help="Work assigned person"
    )
    tag_ids = fields.Many2many(
        "worksheet.tag", string="Tags", ondelete="cascade", help="Select tags"
    )
    description = fields.Html(
        string="Description", help="Add any description of the service"
    )
    service_booking_id = fields.Many2one(
        "service.booking",
        string="Service Booking",
        help="Select the service booking " "associated with this record.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id.id,
        help="Select the company to which this record " "belongs.",
    )
    state = fields.Selection(
        selection=[("draft", "Draft"), ("done", "Done")],
        default="draft",
        string="State",
        help="The current state of the record.",
    )

    def action_done(self):
        """Function to change state to done"""
        self.write({"state": "done"})
