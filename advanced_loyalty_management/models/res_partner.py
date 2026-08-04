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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models, fields


class ResPartner(models.Model):
    """Extends the core 'res.partner' model to expose loyalty redemption history
    and POS order data directly from the customer's form view.

    This extension makes it possible for POS operators and back-office users
    to review a customer's complete redemption activity without leaving the
    partner record, and provides a smart-button shortcut to the filtered
    loyalty history list.

    Additional Fields:
        pos_order_ids (One2many): All POS orders linked to this partner.
            Used to load order data into the POS session and to look up
            redemption activity via order lines.
    """
    _inherit = 'res.partner'

    pos_order_ids = fields.One2many('pos.order', 'partner_id')

    def _load_pos_data_fields(self, config_id):
        """Extend the list of fields loaded for the POS session.

        Overrides the parent method to include 'pos_order_ids' so that
        the customer's POS order history is available on the frontend,
        enabling redemption frequency checks and history display.

        Args:
            config_id (int): The ID of the active POS configuration.

        Returns:
            list: A list of field names to be loaded for 'res.partner'
                in the POS session data.
        """
        result = super()._load_pos_data_fields(config_id)
        result += ['pos_order_ids']
        return result

    def action_view_redemption_history(self):
        """Open the loyalty history list filtered for this customer.

        Returns an action that navigates to the 'loyalty.history' list and
        form views, pre-filtered to show only history entries associated with
        loyalty cards belonging to the current partner. The view is opened
        in read-only mode (create is disabled via context).

        Returns:
            dict: An Odoo action dictionary of type 'ir.actions.act_window'
                that opens the filtered 'loyalty.history' views.
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Redemption History',
            'view_mode': 'list,form',
            'res_model': 'loyalty.history',
            'domain': [('card_id.partner_id', '=', self.id)],
            'context': "{'create': False}"
        }

    @api.model
    def check_redemption(self, pid):
        """Retrieve the order IDs and dates on which a partner redeemed rewards.

        Searches for all POS orders associated with the given partner and
        then filters the order lines to those that correspond to redemption
        reward types. Returns the matching order IDs and their creation dates
        so the POS frontend can determine whether the customer has already
        claimed a redemption reward within the configured frequency window.

        Args:
            pid (list): A single-element list containing the partner ID (int)
                whose redemption history is to be checked.

        Returns:
            tuple[list[int], list[date]]: A two-element tuple where:
                - The first element is a list of POS order IDs (int) on
                  which a redemption reward was applied.
                - The second element is the corresponding list of creation
                  dates (datetime.date) for those order lines.
        """
        order = self.env['pos.order'].search([('partner_id', '=', pid[0])])
        data = []
        date = []
        order_line = self.env['pos.order.line'].search(
            [('reward_id.reward_type', '=', 'redemption'), ('order_id', 'in', order.ids)])
        for line in order_line:
            data.append(line.order_id.id)
            date.append(line.create_date.date())
        return data, date
