# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk  (odoo@cybrosys.com)
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
from odoo import models


class AccountMove(models.Model):
    """ Class for cancel and reset the journal entries """
    _inherit = "account.move"

    def cancel_multiple_journal_entry(self):
        """ Return the confirmation window for cancel journal entry """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Multiple Journal Entry Cancel',
            'view_mode': 'form',
            'views': [(self.env.ref('account_move_multi_cancel.'
                                'account_move_cancel_reset_view_form')
                       .id, 'form')],
            'target': 'new',
            'res_model': 'account.move.cancel.reset',
            'context': {
                'active_ids': self._context.get('active_ids')
            }
        }

    def reset_multiple_journal_entry(self):
        """ Return the confirmation window for reset journal entry """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Multiple Journal Entry Reset',
            'view_mode': 'form',
            'views': [(self.env.ref(
                'account_move_multi_cancel.reset_account_move_cancel_reset_view_form')
                       .id, 'form')],
            'target': 'new',
            'res_model': 'account.move.cancel.reset',
            'context': {
                'active_ids': self._context.get('active_ids')
            }
        }
