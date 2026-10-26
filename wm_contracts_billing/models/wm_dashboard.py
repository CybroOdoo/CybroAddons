#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models


class WmDashboard(models.AbstractModel):
    """Dashboard revenue: orders settled by a billing run without an invoice."""
    _inherit = 'wm.dashboard'

    @api.model
    def _get_order_revenue_exclusion_domain(self):
        """
        Orders settled by a monthly billing run without an invoice (weight
        covered by the subscription allowance) are billed: they are not
        unbilled order revenue either.
        """
        domain = super()._get_order_revenue_exclusion_domain()
        settled = [('billing_run_line_id.invoice_not_required', '=', True)]
        if not domain:
            return ['!'] + settled
        # super() returns NOT (posted links...): extend the OR inside the NOT
        return ['!', '|'] + settled + domain[1:]
