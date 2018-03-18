# -*- coding: utf-8 -*-
# @author: Rosen Vladimirov (vladimirov.rosen@gmail.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import api, models, fields, exceptions, tools, _
import openerp.addons.decimal_precision as dp
_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.one
    def _compute_pricelist_dp_discount(self):
        dp_discount = self.pricelist_discount and self.pricelist_discount*100 or False
        self.pricelist_display_discount = '(%s)' % dp_discount and dp_discount or ''


    # possible to add all fields from pricelist need for compute the price
    pricelist_discount = fields.Float(string="Pricelist discount", digits= dp.get_precision('Discount'),
        help="Show margin from pricelist", states={'draft': [('readonly', False)]}, default=0.0)
    pricelist_display_discount = fields.Char(string="Discount", readonly=True, compute='_compute_pricelist_dp_discount',
        multi="pricelist_display_discount", store=False, help="Show margin from pricelist")
    pricelist_base_price = fields.Float(string="Pricelist Base price", digits=dp.get_precision('Account'),
        help="Show base price from pricelist", states={'draft': [('readonly', False)]}, default=0.0)


    @api.v7
    def product_id_change_ex(self, cr, uid, ids, pitstop, context=None):
        pitstop = super(SaleOrderLine, self).product_id_change_ex(cr, uid, ids, pitstop, context=context)
        if pitstop['result']:
            pitstop['result'].update({'pricelist_discount': pitstop['price_attr']['price_discount'] and pitstop['price_attr']['price_discount'] or 0.0,
                                      'pricelist_base_price': pitstop['price_attr']['base_price'] and pitstop['price_attr']['base_price'] or 0.0})
        _logger.info("Discount pricelist %s" % (pitstop))
        return pitstop
