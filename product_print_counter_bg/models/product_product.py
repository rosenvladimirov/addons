# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    print_count = fields.Integer(
        string='Times of printing label',
        help="Counter for printing labels")

    @api.model
    def create(self, vals):
        product = super(ProductProduct, self).create(vals)
        template_vals = {}
        if 'print_count' not in vals:
            template_vals['print_count'] = 0
        if template_vals:
            product.write(template_vals)
        return product