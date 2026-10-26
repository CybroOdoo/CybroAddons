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
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class PosSession(models.Model):
    """Inherit pos.session to load POS order data in session."""
    _inherit = 'pos.session'

    @api.model
    def get_all_order_config(self):
        """Retrieves the configuration parameters related to POS all orders."""
        icp = self.env['ir.config_parameter'].sudo()
        return {
            'config': icp.get_str('pos_all_orders.pos_all_order') or False,
            'n_days': icp.get_int('pos_all_orders.n_days') or 0,
        }

    @api.model
    def get_all_order(self, session_id=None):
        """Retrieves POS orders based on the provided session ID and optional number of days."""
        domain = [('state', '!=', 'cancel')]
        session_val = None
        n_days_val = None

        if isinstance(session_id, dict):
            session_val = session_id.get('session')
            n_days_val = session_id.get('n_days')
        elif isinstance(session_id, (int, float)):
            session_val = int(session_id)
        elif isinstance(session_id, list) and session_id:
            if isinstance(session_id[0], dict):
                session_val = session_id[0].get('session')
                n_days_val = session_id[0].get('n_days')
            elif isinstance(session_id[0], (int, float)):
                session_val = int(session_id[0])

        if n_days_val:
            date_to = fields.Datetime.now() - relativedelta(days=int(n_days_val))
            domain.append(('date_order', '>=', date_to))
        elif session_val:
            domain.append(('session_id', '=', session_val))

        orders = self.env['pos.order'].search(domain, order='date_order desc, id desc')
        return [{
            'id': rec.id,
            'name': rec.name or '',
            'date_order': fields.Datetime.to_string(rec.date_order) if rec.date_order else '',
            'pos_reference': rec.pos_reference or '',
            'partner_id': rec.partner_id.name or '',
            'total': rec.amount_total or 0.0,
            'state': rec.state or '',
            'session': rec.session_id.name or 'current_session',
        } for rec in orders]

    @api.model
    def get_all_past_orders(self, session_id=None):
        """Get all past orders up to the current date."""
        del session_id
        current_date = fields.Datetime.now()
        domain = [
            ('date_order', '<=', current_date),
            ('state', '!=', 'cancel'),
        ]
        orders = self.env['pos.order'].search(domain, order='date_order desc, id desc')
        return [{
            'id': rec.id,
            'name': rec.name or '',
            'date_order': fields.Datetime.to_string(rec.date_order) if rec.date_order else '',
            'pos_reference': rec.pos_reference or '',
            'partner_id': rec.partner_id.name or '',
            'total': rec.amount_total or 0.0,
            'state': rec.state or '',
            'session': rec.session_id.name or 'past_order',
        } for rec in orders]

    @api.model
    def get_default_all_orders(self, session_id=None):
        """Retrieves all POS orders."""
        del session_id
        domain = [('state', '!=', 'cancel')]
        orders = self.env['pos.order'].search(domain, order='date_order desc, id desc')
        return [{
            'id': rec.id,
            'name': rec.name or '',
            'date_order': fields.Datetime.to_string(rec.date_order) if rec.date_order else '',
            'pos_reference': rec.pos_reference or '',
            'partner_id': rec.partner_id.name or '',
            'total': rec.amount_total or 0.0,
            'state': rec.state or '',
            'session': rec.session_id.name or '',
        } for rec in orders]

    @api.model
    def get_pos_all_orders(self, session_id=None):
        """Unified method to load orders according to the pos_all_orders configuration."""
        config_data = self.get_all_order_config()
        config_type = config_data.get('config')
        n_days = config_data.get('n_days') or 0

        session_val = None
        if isinstance(session_id, dict):
            session_val = session_id.get('session')
        elif isinstance(session_id, (int, float)):
            session_val = int(session_id)
        elif isinstance(session_id, list) and session_id:
            if isinstance(session_id[0], dict):
                session_val = session_id[0].get('session')
            elif isinstance(session_id[0], (int, float)):
                session_val = int(session_id[0])

        if config_type == 'current_session':
            return self.get_all_order({'session': session_val})
        if config_type == 'past_order':
            return self.get_all_past_orders({'session': session_val})
        if config_type == 'last_n':
            return self.get_all_order({'session': session_val, 'n_days': n_days})
        return self.get_default_all_orders({'session': session_val})
