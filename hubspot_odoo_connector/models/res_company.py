# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
from odoo import fields, models


class ResCompany(models.Model):
    """ Adding new fields related to hubspot import/export in Company """
    _inherit = 'res.company'

    hs_object_id = fields.Char(string="Hubspot ID",
                               help="Hubspot ID associated with this record.")
    sync_mode = fields.Selection(
        selection=[('import', 'HS Imported'), ('export', 'HS Exported')],
        string='Sync Mode',
        help="Sync mode for the record. 'HS Imported' indicates the record was"
             " imported from Hubspot, while 'HS Exported' indicates the record"
             " was exported to Hubspot.")
