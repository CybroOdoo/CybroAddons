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
from contextlib import contextmanager

from psycopg2.errors import CheckViolation

from odoo import _, models
from odoo.exceptions import UserError

# account.move.line constraint violated when no income account can be found
# for an invoice line (no product/category income account and no Default
# Income Account on the sales journal, e.g. a company without a chart of
# accounts).
MISSING_ACCOUNT_CONSTRAINT = 'account_move_line_check_accountable_required_fields'


class ResCompany(models.Model):
    _inherit = 'res.company'

    @contextmanager
    def _wm_invoicing_guard(self):
        """Wrap invoice creation for this company: turn the raw database error
        raised when an invoice line has no income account into a clear
        UserError. The work is done in a savepoint so the cursor stays usable.
        """
        self.ensure_one()
        try:
            with self.env.cr.savepoint():
                yield
        except CheckViolation as e:
            if e.diag.constraint_name != MISSING_ACCOUNT_CONSTRAINT:
                raise
            raise UserError(_(
                "The invoice could not be created: no income account was found for "
                "company %(company)s. Install a chart of accounts (Accounting > "
                "Configuration > Settings > Fiscal Localization), or set a Default "
                "Income Account on its Sales journal, then try again.",
                company=self.display_name,
            )) from None
