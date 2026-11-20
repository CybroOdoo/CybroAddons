from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTestimonial(TransactionCase):
    def test_author_image_is_copied_and_cleared(self):
        testimonial = self.env['website.testimonial'].new({
            'user_id': self.env.user.id,
            'testimonial': 'A useful shopping experience.',
        })
        testimonial._onchange_name()
        self.assertEqual(testimonial.image, self.env.user.image_1920)
        testimonial.user_id = False
        testimonial._onchange_name()
        self.assertFalse(testimonial.image)

    def test_testimonial_is_saved(self):
        testimonial = self.env['website.testimonial'].create({
            'user_id': self.env.user.id,
            'testimonial': 'A useful shopping experience.',
        })
        self.assertEqual(testimonial.user_id, self.env.user)
        self.assertEqual(testimonial.testimonial, 'A useful shopping experience.')
