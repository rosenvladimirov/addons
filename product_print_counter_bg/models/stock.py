# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import fields, osv, _


class stock_move(osv.osv):
    _inherit = "stock.move"

    def _store_average_cost_price_ex(self, cr, uid, product, average_valuation_price, context=None):
        if average_valuation_price <> product.standard_price:
            product_obj = self.pool.get('product.product')
            msg = _('Computed price must to be:  %s') %  str(average_valuation_price)
            product_obj.message_post(cr, uid, [product.id], body=msg)
            product_obj.write(cr, uid, [product.id], {'print_count': 0}, context=context) 
        return product, average_valuation_price
