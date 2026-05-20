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
#############################################################################

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class DeliveryCarrier(models.Model):
    """
    Extends 'delivery.carrier' to support oil and gas pipeline operations.
    Enforces that a pipeline operator is assigned if the carrier is a pipeline.
    """
    _inherit = "delivery.carrier"

    is_oil_gas_pipeline = fields.Boolean(
        string="Oil and Gas Pipeline",
        default=False,
        help="Enable this delivery method for oil and gas pipeline operations.",
    )
    pipeline_operator = fields.Many2one(
        "res.partner",
        string="Pipeline Operator",
        help="Business partner responsible for operating this pipeline delivery method.",
    )

    @api.constrains("pipeline_operator", "is_oil_gas_pipeline")
    def _check_oil_pipeline_values(self):
        """
        Validates that a pipeline operator is set if the carrier is marked as a pipeline.
        """
        for carrier in self:
            if carrier.is_oil_gas_pipeline and not carrier.pipeline_operator:
                raise ValidationError(_("Pipeline operator is required for oil and gas pipeline delivery methods."))
