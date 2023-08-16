# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class BaseDocumentLayout(models.TransientModel):
    """Inherited base document layout for adding fields"""
    _inherit = 'base.document.layout'

    signature = fields.Binary(string='Signature',
                              related='company_id.signature',
                              help='Attach the signature here')
    signed_user_id = fields.Many2one(string='Signed By',
                                     related='company_id.signed_user_id',
                                     help='Person who signed')
    job_id = fields.Many2one(string='Designation',
                             related='company_id.job_id',
                             help='Designation of signed person')
    signed_time = fields.Datetime(string='Signed On',
                                  related='company_id.signed_time',
                                  help='Signed date')
