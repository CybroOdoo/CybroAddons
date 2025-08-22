from odoo import models, fields , api


class MailMessage(models.Model):
    _inherit = "mail.message"

    is_read = fields.Boolean(string="Read", default=False)

    @api.model
    def compute_read_message(self, datas):
        print(datas)
        try:
            messages = self.env['mail.message'].search([
                ('model', '=', 'discuss.channel'),
                ('res_id', '=', datas),
                ('is_read', '=', False)
            ])
            for message in messages:
                if message.is_read is False:
                    message.write({'is_read': True})
                    print(f"Marked messages as read: {message.ids}")
                else:
                    print("No unread messages found.")
        except Exception as e:
            print(f"An error occurred: {str(e)}")




