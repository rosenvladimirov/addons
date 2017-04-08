# -*- encoding: utf-8 -*-
##############################################################################
#
#    Purchase - Computed Purchase Order Module for Odoo
#    Copyright (C) 2013-Today GRAP (http://www.grap.coop)
#    @author Julien WESTE
#    @author Sylvain LE GAL (https://twitter.com/legalsylvain)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api, fields
import openerp.addons.decimal_precision as dp

class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Private section
    @api.model
    @api.one
    # Later, we may want to implement other valid_psi options
    def _valid_psi(self, method):
        if method == 'first':
            return self._first_valid_psi()
        elif method == 'all':
            return self._all_valid_psi()
        else:
            return False

    @api.model
    @api.one
    def _all_valid_psi(self):
        today = fields.Date.today()
        if not self.product_tmpl_id.seller_ids:
            return False
        valid_si = self.product_tmpl_id.seller_ids.filtered(
            lambda si, t=today: ((not si.date_start or si.date_start <= t) and
                                 (not si.date_end or si.date_end >= t)))
        return valid_si

    @api.model
    @api.one
    def _first_valid_psi(self):
        if not self.product_tmpl_id.seller_ids:
            return False
        valid_si = self._all_valid_psi()[0]
        seq = min([si.sequence for si in valid_si])
        return valid_si.filtered(lambda si, seq=seq: si.sequence == seq)

class PricelistPartnerinfo(models.Model):
    _inherit = 'product.supplierinfo'

    @api.multi
    def _calc_qty(self):
        for supplier_info in self:
            qty = supplier_info.min_qty
            self.qty = qty

    @api.multi
    def _calc_diff_price(self):
        for pricelist_supplierinfo in self:
            diff_price = pricelist_supplierinfo.suppinfo_id.price - pricelist_supplierinfo.price

    @api.one
    def _compute_unit_price_cmp(self):
        #for supplierinfo in self:
        if len(self.pricelist_ids) == 0:
            self.unit_price = 0
            self.unit_price_note = '-'
        else:
            txt = '('
            size = len(self.pricelist_ids)
            uom_precision = self.product_tmpl_id.uom_id.rounding
            for i in range(size - 1):
                txt += '%s - %s : %s\n' % (
                    self.pricelist_ids[i].min_quantity,
                    (self.pricelist_ids[i + 1].min_quantity -
                     uom_precision),
                    self.pricelist_ids[i].price)
            txt += '>=%s : %s' % (
                self.pricelist_ids[size - 1].min_quantity,
                self.pricelist_ids[size - 1].price)
            txt += ')'
            self.unit_price = self.pricelist_ids[0].price
            self.unit_price_note = txt

    diff_price = fields.Float(string='Difference of price', compute=_calc_diff_price, store=False,  multi="diff_price", help="This is a difference of price between last payed price and contracted")
    unit_price_note = fields.Char(compute='_compute_unit_price_cmp', multi='unit_price', string='Unit Price')
    unit_price = fields.Float(
        compute='_compute_unit_price_cmp', multi='unit_price',
        store=False,
        digits_compute=dp.get_precision('Product Price'),
        help="""Purchase Price of the product for this supplier. \n If many"""
        """ prices are defined, The price will be the price associated with"""
        """ the smallest quantity.""",
        default=False)

    qty = fields.Float(string='Quantity', compute=_calc_qty, store=True,  multi="qty", help="This is a quantity which is converted into Default Unit of Measure.")
    #price = fields.Float(string='Price', required=True, digits_compute=dp.get_precision('Product Price'), default=0.0, help="The price to purchase a product")
    #currency_id = fields.Many2one(string='Currency', comodel_name='res.currency', required=True)
    date_start = fields.Date(string='Start Date', help="Start date for this vendor price")
    date_end = fields.Date(string='End Date', help="End date for this vendor price")
    package_qty = fields.Float('Package Qty', digits_compute=dp.get_precision('Product UoM'), 
                                help="""The quantity of products in the supplier package."""
                                     """ You will always have to buy a multiple of this quantity.""",
                                default=1)

