# -- coding: utf-8 --
###############################################################################
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
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models
from odoo.fields import Command
from odoo.exceptions import UserError


class ContactsMassUpdate(models.TransientModel):
    """Transient class for wizard to modify multiple partners."""
    _name = "contacts.mass.update"
    _description = "Bulk Partner Assignment"

    @api.model
    def default_get(self, fields_list):
        """Override default_get to modify Pre-fill data using context"""
        res = super().default_get(fields_list)
        context = self.env.context

        # Pre-fill from active partners if called from partner list view
        active_ids = context.get('active_ids', [])
        if active_ids:
            partners = self.env['res.partner'].browse(active_ids)
            # Determine partner type from selected records
            has_customers = any(p.customer_rank > 0 for p in partners)
            has_suppliers = any(p.supplier_rank > 0 for p in partners)
            has_none = any(p.supplier_rank == 0 and p.customer_rank == 0 for p in partners)

            if has_customers and has_suppliers and not has_none:
                res['partner_type'] = 'both'
            elif has_customers and not has_none:
                res['partner_type'] = 'customer'
            elif has_suppliers and not has_none:
                res['partner_type'] = 'supplier'

        return res

    step = fields.Selection([
        ('select', 'Filter Partners'),
        ('confirm', 'Review & Assign Tags')
    ], default='select', string="Step")

    # Step 1: Filter Selection
    partner_type = fields.Selection([
        ('customer', 'Customers'),
        ('supplier', 'Vendors'),
        ('both', 'Both'),
        ('all', 'All')
    ],
        string="Partner Type", required=True, default='all',
        help="Filter partners by type"
    )

    include_inactive = fields.Boolean(
        string="Include Archived Partners",
        help="Include archived/inactive partners in the selection"
    )

    filter_by_location = fields.Boolean(
        string="Filter by Location",
        help="Enable location-based filtering"
    )

    country_ids = fields.Many2many(
        'res.country',
        string="Countries",
        help="Filter partners by specific countries"
    )

    state_ids = fields.Many2many(
        'res.country.state',
        string="States",
        help="Filter partners by specific states"
    )

    # Step 2: Tag Assignment
    tag_ids = fields.Many2many(
        'res.partner.category',
        string="Tags to Assign",
        help="Select tags to assign to filtered partners"
    )

    # sales
    user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        help="Select salesperson to assign to filtered partners"
    )

    property_payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Sales Payment Terms',
        help="Select a sale payment term to assign to filtered partners"
    )

    property_inbound_payment_method_line_id = fields.Many2one(
        'account.payment.method.line',
        string='Sales Payment Method',
        help='Select a sale payment method to assign to filtered partners'
    )

    property_product_pricelist = fields.Many2one(
        'product.pricelist',
        string='Pricelist',
        help='Select a price list to assign to filtered partners'
    )

    # purchase
    property_supplier_payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Purchase Payment Terms',
        help='Select a purchase payment term to assign to filtered partners'
    )

    property_outbound_payment_method_line_id = fields.Many2one(
        'account.payment.method.line',
        string='Purchase Payment Method',
        help='Select a purchase payment method to assign to filtered partners'
    )

    # other
    property_account_position_id = fields.Many2one(
        'account.fiscal.position',
        string='Fiscal Position',
        help='Select a purchase fiscal position to assign to filtered partners'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        help='Select a company to assign to filtered partners'
    )

    replace_tags = fields.Boolean(
        string="Replace Existing Tags",
        help="If checked, removes all existing tags before assigning new ones"
    )

    partner_count = fields.Integer(
        string="Partners Found",
        compute="_compute_partner_count",
        store=False
    )

    preview_partner_ids = fields.Many2many(
        'res.partner',
        context={'active_test': False},
        string="Partners to be Tagged",
        compute="_compute_preview_partners",
        store=False
    )

    @api.depends('partner_type', 'include_inactive', 'filter_by_location',
                 'country_ids', 'state_ids')
    def _compute_partner_count(self):
        """Compute partner count based on filters"""
        for wizard in self:
            partners = wizard._get_partners()
            wizard.partner_count = len(partners)

    @api.depends('partner_type', 'include_inactive', 'filter_by_location',
                 'country_ids', 'state_ids')
    def _compute_preview_partners(self):
        """Fetch partners based on domain for preview"""
        for wizard in self:
            wizard.preview_partner_ids = wizard._get_partners()

    @api.onchange('filter_by_location')
    def _onchange_filter_by_location(self):
        """Clear location fields when filter is disabled"""
        if not self.filter_by_location:
            self.country_ids = False
            self.state_ids = False

    def action_next(self):
        """Move to confirmation step"""
        self.ensure_one()

        if self.partner_count == 0:
            raise UserError("No partners found matching your filters. Please adjust your criteria.")

        self.step = 'confirm'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'contacts.mass.update',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'context': {
                'active_ids': self.preview_partner_ids.ids,
            }
        }

    def action_back(self):
        """Return to selection step"""
        self.ensure_one()
        self.step = 'select'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'contacts.mass.update',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'context': {
                'active_ids': self.preview_partner_ids.ids,
            }
        }

    def action_update_partner(self):
        """Assign new values to filtered partners"""
        self.ensure_one()

        # Get all matching partners
        partners = self._get_partners()

        if not partners:
            raise UserError("No partners found to assign tags.")

        # Assign tags
        for partner in partners:
            if self.tag_ids:
                # Replace all existing tags
                partner.category_id = self.tag_ids.ids if self.replace_tags else [
                    Command.link(tag.id) for tag in self.tag_ids]

            if self.user_id:
                # Replace salesperson
                partner.user_id = self.user_id.id

            if self.property_payment_term_id:
                # Replace sales payment term
                partner.property_payment_term_id = self.property_payment_term_id.id

            if self.property_inbound_payment_method_line_id:
                # Replace sales payment method
                partner.property_inbound_payment_method_line_id = (
                    self.property_inbound_payment_method_line_id.id)

            if self.property_product_pricelist:
                # Replace pricelist
                partner.property_product_pricelist = self.property_product_pricelist.id

            if self.property_supplier_payment_term_id:
                # Replace purchase payment term
                partner.property_supplier_payment_term_id = (
                    self.property_supplier_payment_term_id.id)

            if self.property_outbound_payment_method_line_id:
                # Replace pricelist
                partner.property_outbound_payment_method_line_id = (
                    self.property_outbound_payment_method_line_id.id)

            if self.property_account_position_id:
                # Replace fiscal position
                partner.property_account_position_id = self.property_account_position_id.id

            if self.company_id:
                # Replace company
                partner.company_id = self.company_id.id

        # Prepare success message with counts
        partner_count = len(partners)

        message = f"""
            {partner_count} partner(s) updated !!!
        """

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': message,
                'type': 'success',
                'sticky': False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def _get_partner_domain(self):
        """Build domain based on wizard filters"""
        domain = []

        # If active partners in context
        if self.env.context.get('active_ids'):
            domain.append(('id', 'in', self.env.context.get('active_ids')))

        # Partner type filter
        if self.partner_type == 'customer':
            domain.append(('customer_rank', '>', 0))
        elif self.partner_type == 'supplier':
            domain.append(('supplier_rank', '>', 0))
        elif self.partner_type == 'both':
            domain.append('|')
            domain.append(('customer_rank', '>', 0))
            domain.append(('supplier_rank', '>', 0))

        # Active/Inactive filter
        if self.include_inactive:
            domain.append(('active', 'in', [True, False]))

        # Location filters
        if self.filter_by_location:
            if self.country_ids:
                domain.append(('country_id', 'in', self.country_ids.ids))
            if self.state_ids:
                domain.append(('state_id', 'in', self.state_ids.ids))
        return domain

    def _get_partners(self):
        """Return partners matching the wizard filters, including archived ones when requested."""
        partner_env = self.env['res.partner']
        if self.include_inactive:
            partner_env = partner_env.with_context(active_test=False)
        return partner_env.search(self._get_partner_domain())
