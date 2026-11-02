# -*- coding: utf-8 -*-
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
from odoo import models
from odoo.exceptions import ValidationError


class HrExpense(models.Model):
    """Extends 'hr.expense' to post the journal entries of several approved
    expenses at once."""
    _inherit = 'hr.expense'

    def action_post_entries(self):
        """Post the journal entries of the selected approved expenses.

        Approving an expense creates its journal entry as a draft. An approved
        expense without one, e.g. an imported one, gets it created here first.
        All the draft entries are then posted together.
        """
        if any(expense.state != 'approved' for expense in self):
            raise ValidationError(
                self.env._("You can only post the journal entries of "
                           "approved expenses."))
        self.filtered(lambda expense: not expense.account_move_id)._create_move()
        self.account_move_id.filtered(
            lambda move: move.state == 'draft').action_post()
