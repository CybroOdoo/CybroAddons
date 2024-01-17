# -*- coding: utf-8 -*-
###############################################################################
#
#  Cybrosys Technologies Pvt. Ltd.
#
#  Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#  Author: Hafeesul Ali (odoo@cybrosys.com)
#
#  You can modify it under the terms of the GNU AFFERO
#  GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#  You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#  (AGPL v3) along with this program.
#  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, models


class AccountJournal(models.Model):
    """This class represents an inherits model for account journals in Odoo.
        It inherits from the 'account.journal' model and adds a method
        """
    _inherit = "account.journal"

    @api.model
    def get_journal(self):
        """Method to get available journals
           Returns:
            dict:A dictionary of journal id and name.
        """
        journal_list = [{"id": journal.id, "name": journal.name} for journal in
                        self.search(['|', ('type', '=', 'bank'),
                                     ('type', '=', 'cash')])]
        return journal_list
