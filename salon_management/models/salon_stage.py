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
from odoo import api, fields, models


STAGE_CODES = ['draft', 'open', 'invoiced', 'closed', 'cancelled']


class SalonStage(models.Model):
    """Creates 'salon_stage' to creates new stages dynamically"""
    _name = 'salon.stage'
    _order = 'sequence'
    _description = 'Salon Stage'

    name = fields.Char(required=True, translate=True,
                       help="Name of the stages")
    sequence = fields.Integer(default=1,
                              help="Used to order stages. Lower is first.")

    @api.model
    def _get_stage_id(self, code):
        """Return the id of a default stage from its XML id (never from its
        translatable name). ``code`` is one of draft, open, invoiced,
        closed, cancelled. Returns False when the record doesn't exist."""
        xmlid = 'salon_management.salon_stage_%02d' % STAGE_CODES.index(code)
        return self.env['ir.model.data']._xmlid_to_res_id(
            xmlid, raise_if_not_found=False) or False
