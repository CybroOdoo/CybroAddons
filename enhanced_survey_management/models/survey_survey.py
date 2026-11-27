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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class Survey(models.Model):
    """Inherited model to configure portal visibility and XLSX export."""

    _inherit = 'survey.survey'

    access_mode = fields.Selection(
        selection_add=[('website', 'Website')],
        ondelete={'website': 'cascade'},
    )
    visibility = fields.Boolean(
        string='Portal Visibility',
        help="Portal visibility of this survey.",
    )

    def action_answer_report_download(self):
        """Return URL action to download the survey XLSX report."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/xlsx_report/{self.id}',
        }
