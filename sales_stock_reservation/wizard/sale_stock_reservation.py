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
from markupsafe import Markup, escape

from odoo import fields, models
from odoo.exceptions import UserError


class SaleStockReservation(models.TransientModel):
    """
    This model is used to reserve products for a sale order.

    Fields:
    - stock_reservation_ids: A one-to-many relationship to the
      `stock.reservation` model, representing the reservations to be made.
    - sale_order_id: The ID of the sale order for which the products are being
      reserved.
    - partner_id: The customer linked to the sale quotation.
    - mail_notification_ids: A many-to-many relationship to the `res.users`
      model, representing the users who should receive email notifications about
      the reservation.
    """
    _name = "sale.stock.reservation"
    _description = "Stock Reservation"

    stock_reservation_ids = fields.One2many(
        "stock.reservation",
        "stock_reservation_wizard_id",
        string="Order Lines",
        help='This is a One2many field that refers to the reserved stock items '
             'associated with the wizard.')
    sale_order_id = fields.Many2one(
        "sale.order",
        readonly=True,
        help="Many2one field that returns the Sale Order")
    partner_id = fields.Many2one(
        "res.partner", string="Customer",
        related="sale_order_id.partner_id",
        readonly=True,
        help="Customer linked to the sale quotation")
    mail_notification_ids = fields.Many2many(
        "res.users",
        string="Email Notification",
        help='This is a Many2many field that refers to the users '
             'who will receive email notifications.')

    def action_reserve_stock(self):
        self.ensure_one()

        sale_order = self.sale_order_id
        if not sale_order:
            raise UserError(self.env._("No sale order linked to this reservation."))

        # Set reservation state on sale order
        sale_order.state_reservation = "reserved"

        # Get warehouse and picking type
        warehouse = sale_order.warehouse_id
        if not warehouse or not warehouse.lot_stock_id:
            raise UserError(self.env._("Please configure a warehouse with stock location on the sale order."))

        picking_type = warehouse.out_type_id
        if not picking_type:
            raise UserError(self.env._("No outgoing picking type configured on the warehouse."))

        company = sale_order.company_id

        # Determine source and destination locations
        icp = self.env['ir.config_parameter'].sudo()
        source_param = icp.get_param('sales_stock_reservation.source_location_id')
        dest_param = icp.get_param('sales_stock_reservation.destination_location_id')

        source_location = (
            self.env['stock.location'].browse(int(source_param))
            if source_param and str(source_param).isdigit() and self.env['stock.location'].browse(int(source_param)).exists()
            else warehouse.lot_stock_id
        )
        default_customer_loc = (
            self.env.ref('sales_stock_reservation.sale_stock_reservation', raise_if_not_found=False)
            or self.env.ref('stock.stock_location_customers')
        )
        destination_location = (
            self.env['stock.location'].browse(int(dest_param))
            if dest_param and str(dest_param).isdigit() and self.env['stock.location'].browse(int(dest_param)).exists()
            else default_customer_loc
        )

        # Prepare history lines
        history_vals_list = []

        for rec in self.stock_reservation_ids:
            reserve_qty = rec.reserve_quantity
            if reserve_qty <= 0:
                continue

            available_qty = self.env['stock.quant']._get_available_quantity(
                rec.product_id, source_location
            )
            if reserve_qty > available_qty:
                raise UserError(self.env._(
                    "Cannot reserve %(reserve_qty)s units of %(product)s. "
                    "Only %(available_qty)s units available in %(location)s.",
                    reserve_qty=reserve_qty,
                    product=rec.product_id.display_name,
                    available_qty=available_qty,
                    location=source_location.display_name,
                ))

            move_vals = {
                'product_id': rec.product_id.id,
                'product_uom_qty': reserve_qty,
                'product_uom': rec.unit_of_measure_id.id,
                'location_id': source_location.id,
                'location_dest_id': destination_location.id,
                'picking_type_id': picking_type.id,
                'company_id': company.id,
                'date': fields.Datetime.now(),
                'origin': sale_order.name,
            }
            move = self.env['stock.move'].create(move_vals)
            rec.move_id = move.id
            move._action_confirm()
            self.env['stock.move.line'].create({
                'move_id': move.id,
                'product_id': rec.product_id.id,
                'product_uom_id': rec.unit_of_measure_id.id,
                'location_id': source_location.id,
                'location_dest_id': destination_location.id,
                'quantity': reserve_qty,
            })
            history_vals_list.append((0, 0, {
                'order_line_name': rec.order_line_name,
                'product_id': rec.product_id.id,
                'reserved_quantity': reserve_qty,
                'sale_order_id': sale_order.id,
                'status': 'reserved',
                'move_id': move.id,
            }))
        if history_vals_list:
            sale_order.write({'reserved_stock_ids': history_vals_list})

        reserved_lines = sale_order.reserved_stock_ids.filtered(lambda r: r.status == 'reserved')
        if reserved_lines:
            table_rows = Markup("").join(
                Markup("<tr><td style='padding: 8px;'>") +
                escape(line.order_line_name or line.product_id.display_name) +
                Markup("</td><td style='padding: 8px;'>") +
                escape(line.product_id.name) +
                Markup("</td><td style='padding: 8px;'>") +
                escape(str(line.reserved_quantity)) +
                Markup("</td></tr>")
                for line in reserved_lines
            )

            table_html = (
                Markup("<table border='1' cellpadding='8' cellspacing='0' style='border-collapse: collapse; width: 100%; border: 1px solid #dee2e6;'>"
                       "<tr style='background-color: #ededed; text-align: left;'>"
                       "<th style='padding: 8px;'>") + escape(self.env._("Line")) +
                Markup("</th><th style='padding: 8px;'>") + escape(self.env._("Product")) +
                Markup("</th><th style='padding: 8px;'>") + escape(self.env._("Reserved Quantity")) +
                Markup("</th></tr>") + table_rows + Markup("</table>")
            )

            email_from = company.email or self.env.user.email or 'no-reply@yourcompany.com'
            customer = sale_order.partner_id
            customer_email = customer.email or (customer.commercial_partner_id and customer.commercial_partner_id.email) if customer else False

            # Send stock reservation email to the customer (single email via email_to)
            if customer and customer_email:
                customer_message_body = (
                    Markup("<p>") + escape(self.env._("Dear %s,", customer.name)) + Markup("</p>") +
                    Markup("<p>") + escape(self.env._(
                        "We would like to inform you that some item(s) have been reserved for your quotation %s.",
                        sale_order.name
                    )) + Markup("</p>") +
                    table_html +
                    Markup("<p>") + escape(self.env._("Thank you.")) + Markup("</p>")
                )

                customer_mail_values = {
                    'subject': self.env._("Stock Reservation: %s", sale_order.name),
                    'body_html': customer_message_body,
                    'email_from': email_from,
                    'email_to': customer_email,
                }
                self.env['mail.mail'].create(customer_mail_values).send()
            elif customer and not customer_email:
                sale_order.message_post(
                    body=Markup("<p>") + escape(self.env._(
                        "Stock reservation was created, but notification email could not be sent because customer %s has no email address configured.",
                        customer.name
                    )) + Markup("</p>"),
                )

            # Send email notification to selected internal users if specified
            if self.mail_notification_ids:
                user_emails = [u.email or u.login for u in self.mail_notification_ids if (u.email or u.login)]
                if user_emails:
                    user_names = ", ".join(self.mail_notification_ids.mapped('name'))
                    user_intro = self.env._("Dear %s,", user_names)
                    if customer:
                        user_order_info = self.env._(
                            "We would like to inform you that some item(s) have been reserved for %(order)s (Customer: %(customer)s).",
                            order=sale_order.name,
                            customer=customer.name,
                        )
                    else:
                        user_order_info = self.env._(
                            "We would like to inform you that some item(s) have been reserved for %s.",
                            sale_order.name
                        )

                    user_message_body = (
                        Markup("<p>") + escape(user_intro) + Markup("</p>") +
                        Markup("<p>") + escape(user_order_info) + Markup("</p>") +
                        table_html +
                        Markup("<p>") + escape(self.env._("Thank you.")) + Markup("</p>")
                    )

                    users_mail_values = {
                        'subject': self.env._("Stock Reservation Notification: %s", sale_order.name),
                        'body_html': user_message_body,
                        'email_from': email_from,
                        'email_to': ", ".join(user_emails),
                    }
                    self.env['mail.mail'].create(users_mail_values).send()

            # Post a clear, permanent confirmation note in the sale order chatter
            chatter_heading = escape(self.env._("Stock Reservation Confirmed"))
            chatter_subhead = escape(self.env._(
                "The following item(s) have been reserved for quotation %s:",
                sale_order.name
            ))
            chatter_body = (
                Markup("<p><strong>") + chatter_heading + Markup("</strong></p>") +
                Markup("<p>") + chatter_subhead + Markup("</p>") +
                table_html
            )
            if customer and customer_email:
                cust_note = escape(self.env._(
                    "Notification email sent to customer: %(name)s (%(email)s)",
                    name=customer.name,
                    email=customer_email
                ))
                chatter_body += Markup("<p><small class='text-muted'>") + cust_note + Markup("</small></p>")
            if self.mail_notification_ids:
                user_names = ", ".join(self.mail_notification_ids.mapped('name'))
                users_note = escape(self.env._(
                    "Notification email sent to user(s): %s",
                    user_names
                ))
                chatter_body += Markup("<p><small class='text-muted'>") + users_note + Markup("</small></p>")

            sale_order.message_post(
                body=chatter_body,
                subject=self.env._("Stock Reservation: %s", sale_order.name),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )

        return True
