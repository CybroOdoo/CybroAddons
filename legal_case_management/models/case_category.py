# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CaseCategory(models.Model):
    """Create case category"""
    _name = 'case.category'
    _description = 'Case Category'

    name = fields.Char("Case Category", required=True,
                       help='Name of the case category')

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft_or_cancel(self):
        """ Prevent the deletion of a case category if it is used in any
         cases. """
        cases = self.sudo().env['case.registration'].search_count([
            ('case_category_id', 'in', self.ids),
            ('state', 'not in', ['draft'])
        ])
        if cases:
            raise UserError(_("You can not delete a case category,"
                              " because it is used in case"))
