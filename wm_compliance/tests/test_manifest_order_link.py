from datetime import datetime, time

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_compliance')
class TestManifestOrderLink(TransactionCase):
    """Manifest lines link to the collection order they came from."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Order Link Generator'})
        cls.category = cls.env['wm.waste.category'].create({
            'name': 'Order Link Plastic', 'code': 'OLPL', 'price': 1.0})
        cls.env['wm.disposal.facility'].create({'name': 'Order Link Plant', 'facility_type': 'landfill'})

    def _order(self, weight, hour=9):
        start = datetime.combine(fields.Date.today(), time(hour, 0))
        order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'scheduled_start': start,
            'scheduled_end': start.replace(hour=hour + 1),
            'order_line_ids': [(0, 0, {'category_id': self.category.id, 'weight': weight})],
        })
        order.sudo().with_context(programmatic_state_change=True).write({'state': 'completed'})
        return order

    def _lines(self, order):
        return self.env['wm.compliance.manifest.line'].search([('collection_order_id', '=', order.id)])

    def test_lines_link_to_their_order(self):
        order1, order2 = self._order(50.0), self._order(30.0, hour=12)
        order1._automate_compliance_manifest()
        order2._automate_compliance_manifest()
        self.assertEqual(self._lines(order1).mapped('quantity'), [50.0])
        self.assertEqual(self._lines(order2).mapped('quantity'), [30.0])
        self.assertIn('Collection Order: %s' % order1.name, self._lines(order1).notes)

    def test_editing_notes_does_not_duplicate_lines(self):
        """The duplicate guard follows the link, not the free-text notes."""
        order = self._order(40.0)
        order._automate_compliance_manifest()
        line = self._lines(order)
        self.assertEqual(len(line), 1)
        line.sudo().write({'notes': 'edited by the compliance officer'})
        order._automate_compliance_manifest()
        self.assertEqual(self._lines(order), line)

    def test_link_not_copied_and_cleared_on_order_delete(self):
        order = self._order(40.0)
        order._automate_compliance_manifest()
        line = self._lines(order)
        self.assertFalse(line.copy_data()[0].get('collection_order_id'))
        manifest_line_id = line.id
        order.sudo().with_context(programmatic_state_change=True).write({'state': 'draft'})
        order.sudo().unlink()
        remaining = self.env['wm.compliance.manifest.line'].browse(manifest_line_id).exists()
        self.assertTrue(remaining)
        self.assertFalse(remaining.collection_order_id)
