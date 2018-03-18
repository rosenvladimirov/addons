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

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class ComputedPurchaseOrderLine(models.Model):
    _description = 'Computed Purchase Order Line'
    _name = 'computed.purchase.order.line'
    _order = 'sequence'

    _STATE = [
        ('new', 'New'),
        ('up_to_date', 'Up to date'),
        ('updated', 'Updated'),
    ]

    # Columns section
    computed_purchase_order_id = fields.Many2one(
        'computed.purchase.order', 'Order Reference', required=True,
        ondelete='cascade')
    state = fields.Selection(
        _STATE, 'State', required=True, readonly=True, default='new',
        help="Shows if the product's information has been updated")
    sequence = fields.Integer(
        'Sequence',
        help="""Gives the sequence order when displaying a list of"""
        """ purchase order lines.""")
    taxes_id = fields.Many2many(string='Taxes', comodel_name='account.tax', relation='computed_purchase_order_taxe', column1='ord_id', column2='tax_id', domain=['|', ('active', '=', False), ('active', '=', True)])
    product_id = fields.Many2one(
        'product.product', 'Product', required=True)
    uom_id = fields.Many2one(
        related='product_id.uom_id', string="UoM", readonly='True')
    product_code = fields.Char('Supplier Product Code',)
    product_code_inv = fields.Char(
        compute='_get_product_information', inverse='_set_product_code',
        string='Supplier Product Code', multi='product_code_name_price',
        help="""This supplier's product code will be used when printing"""
        """ a request for quotation. Keep empty to use the internal"""
        """ one.""")
    product_name = fields.Char('Supplier Product Name',)
    product_name_inv = fields.Char(
        compute='_get_product_information', inverse='_set_product_name',
        string='Supplier Product Name', multi='product_code_name_price',
        help="""This supplier's product name will be used when printing"""
        """ a request for quotation. Keep empty to use the internal"""
        """ one.""")
    product_price = fields.Float(
        'Supplier Product Price',
        digits_compute=dp.get_precision('Product Price'))
    diff_price_vat = fields.Boolean('is have VAT price', help="If unchecked, it will allow to work with two price one for sale/purchase and one for VAT calculations.")
    product_price_inv = fields.Float(
        compute='_get_product_information', inverse='_set_product_price',
        string='Supplier Product Price', multi='product_code_name_price',)
    price_policy = fields.Selection(
        [('uom', 'per UOM'), ('package', 'per Package')], "Price Policy",
        default='uom', required=True)
    product_price_inv_eq = fields.Float(
        compute='_compute_product_price_inv_eq',
        string='Supplier Product Price per Uom',)
    subtotal = fields.Float(
        'Subtotal', compute='_compute_subtotal_price',
        digits_compute=dp.get_precision('Product Price'))
    package_qty = fields.Float('Package quantity')
    package_qty_inv = fields.Float(
        compute='_get_product_information', inverse='_set_package_qty',
        string='Package quantity', multi='product_code_name_price',)
    weight = fields.Float(
        related='product_id.weight', string='Net Weight', readonly='True')
    uom_po_id = fields.Many2one('product.uom', 'UoM', required=True)

    average_consumption = fields.Float(
        compute="_compute_average_consumption", digits=(12, 3))
    displayed_average_consumption = fields.Float(
        'Average Consumption', digits=(12, 3))
    consumption_range = fields.Integer(
        'Range (days)', help="""Range (in days) used to display the average
        consumption""")
    stock_duration = fields.Float(
        compute='_compute_stock_duration', string='Stock Duration (Days)',
        readonly='True', help="Number of days the stock should last.")
    virtual_duration = fields.Float(
        compute='_compute_stock_duration', string='Virtual Duration (Days)',
        readonly='True', help="""Number of days the stock should last after"""
        """ the purchase.""")
    purchase_qty_package = fields.Float(
        'Number of packages', help="""The number of packages you'll buy.""")
    purchase_qty = fields.Float(
        'Quantity to purchase', required=True, default=0,
        help="The quantity you should purchase.")
    manual_input_output_qty = fields.Float(
        string='Manual variation', default=0,
        help="""Write here some extra quantity depending of some"""
        """ input or output of products not entered in the software\n"""
        """- negative quantity : extra output ; \n"""
        """- positive quantity : extra input.""")
    qty_available = fields.Float(
        compute='_get_qty', string='Quantity On Hand', multi='get_qty',
        help="The available quantity on hand for this product")
    incoming_qty = fields.Float(
        compute='_get_qty', string='Incoming Quantity',
        help="Virtual incoming entries", multi='get_qty',)
    outgoing_qty = fields.Float(
        compute='_get_qty', string='Outgoing Quantity',
        help="Virtual outgoing entries", multi='get_qty',)
    virtual_qty = fields.Float(
        compute='_get_qty', string='Virtual Quantity',
        help="Quantity on hand + Virtual incoming and outgoing entries",
        multi='get_qty',)
    computed_qty = fields.Float(
        compute='_get_computed_qty', string='Stock',
        help="The sum of all quantities selected.",
        digits_compute=dp.get_precision('Product UoM'),)

    # Constraints section
    _sql_constraints = [(
        'product_id_uniq', 'unique(computed_purchase_order_id,product_id)',
        'Product must be unique by computed purchase order!'),
    ]

    # Columns section
    @api.multi
    def _calc_line_base_price(self, line):
        """Return the base price of the line to be used for tax calculation.

        This function can be extended by other modules to modify this base
        price (adding a discount, for example).
        """
        return line.product_price

    @api.multi
    def _calc_line_quantity(self, line):
        if line.price_policy == 'package':
            qty = line.package_qty_inv and line.purchase_qty / line.package_qty_inv or 0
        else:
            qty = line.purchase_qty
        return qty

    @api.multi
    @api.onchange('purchase_qty')
    def onchange_purchase_qty(self):
        for cpol in self:
            if cpol.package_qty_inv:
                cpol.purchase_qty_package = cpol.purchase_qty /\
                    cpol.package_qty_inv

    @api.multi
    @api.onchange('purchase_qty_package', 'package_qty_inv')
    def onchange_purchase_qty_package(self):
        for cpol in self:
            if cpol.purchase_qty_package == int(cpol.purchase_qty_package):
                cpol.purchase_qty = cpol.package_qty_inv *\
                    cpol.purchase_qty_package

    @api.multi
    @api.onchange('package_qty_inv', 'product_price_inv', 'price_policy')
    def _compute_product_price_inv_eq(self):
        for line in self:
            if line.price_policy == 'package':
                if line.package_qty_inv:
                    line.product_price_inv_eq = line.product_price_inv /\
                        line.package_qty_inv
                else:
                    line.product_price_inv_eq = 0
            else:
                line.product_price_inv_eq = line.product_price_inv

    @api.depends(
        'purchase_qty', 'product_price', 'product_price_inv', 'price_policy',
        'package_qty_inv')
    @api.multi
    def _compute_subtotal_price(self):
        #cur_obj = self.env['res.currency']
        tax_obj = self.env['account.tax']
        for line in self:
            if line.price_policy == 'package':
                line_qty = line.package_qty_inv and line.purchase_qty / line.package_qty_inv or 0
            else:
                # line.subtotal = line.purchase_qty * line.product_price_inv
                line_price = line.product_price_inv
                line_qty = line.purchase_qty
            taxes = tax_obj.compute_all(line_price,
                                        line_qty, line.product_id,
                                        line.computed_purchase_order_id.partner_id, price_unit_vat=0.0)
            #cur = line.computed_purchase_order_id.pricelist_id.currency_id
            line.subtotal = taxes['total']
            #_logger.debug("Compute suptotal %s:%s" % (taxes['total'], line.subtotal))

    @api.onchange('displayed_average_consumption', 'consumption_range')
    @api.multi
    def _compute_average_consumption(self):
        for line in self:
            line.average_consumption = line.consumption_range and\
                line.displayed_average_consumption / line.consumption_range\
                or 0

    # Fields Function section
    @api.depends('product_id')
    @api.multi
    def _get_qty(self):
        for cpol in self:
            cpol.qty_available = cpol.product_id.qty_available
            cpol.incoming_qty = cpol.product_id.incoming_qty
            cpol.outgoing_qty = cpol.product_id.outgoing_qty
            cpol.virtual_qty = cpol.qty_available + cpol.incoming_qty - \
                cpol.outgoing_qty

    @api.multi
    def _get_computed_qty(self):
        use_pending_qties = False
        for cpol in self:
            if cpol.computed_purchase_order_id.compute_pending_quantity:
                use_pending_qties = True
            if use_pending_qties:
                break

        for cpol in self:
            q = cpol.qty_available
            if use_pending_qties:
                q += cpol.incoming_qty - cpol.outgoing_qty
            cpol.computed_qty = q

    @api.multi
    def _get_product_information(self):
        psi_obj = self.env['product.supplierinfo']
        for cpol in self:
            if not cpol.product_id:
                cpol.product_code_inv = None
                cpol.product_name_inv = None
                cpol.product_price_inv = 0.0
                #cpol.price_policy = 'uom'
                cpol.package_qty_inv = 0.0
            elif cpol.state in ('updated', 'new'):
                cpol.product_code_inv = cpol.product_code
                cpol.product_name_inv = cpol.product_name
                cpol.product_price_inv = cpol.product_price
                cpol.package_qty_inv = cpol.package_qty
            else:
                psi = psi_obj.search([
                    ('name', '=',
                        cpol.computed_purchase_order_id.partner_id.id),
                    ('product_tmpl_id', '=',
                        cpol.product_id.product_tmpl_id.id)])
                if len(psi):
                    psi = psi[0]
                    qty_price_val = psi.unit_price
#                    qty_price_val = psi.price
                    if psi:
                        cpol.product_code_inv = psi.product_code
                        cpol.product_name_inv = psi.product_name
                        cpol.product_price_inv = qty_price_val
                        cpol.package_qty_inv = psi.package_qty
                        #cpol.price_policy = psi.price_policy

    @api.depends('product_code_inv')
    def _set_product_code(self):
        self.product_code = self.product_code_inv
        if self.state == 'up_to_date':
            self.state = 'updated'

    @api.depends('product_name_inv')
    def _set_product_name(self):
        self.product_name = self.product_name_inv
        if self.state == 'up_to_date':
            self.state = 'updated'

    @api.depends('product_price_inv')
    def _set_product_price(self):
        self.product_price = self.product_price_inv
        if self.state == 'up_to_date':
            self.state = 'updated'

    @api.onchange('package_qty_inv')
    def _set_package_qty(self):
        self.package_qty = self.package_qty_inv
        if self.state == 'up_to_date':
            self.state = 'updated'

    @api.multi
    @api.depends('purchase_qty')
    def _compute_stock_duration(self):
        for cpol in self:
            if cpol.product_id:
                if cpol.average_consumption != 0:
                    cpol.stock_duration = (
                        cpol.computed_qty + cpol.manual_input_output_qty)\
                        / cpol.average_consumption
                    cpol.virtual_duration = (
                        cpol.computed_qty + cpol.manual_input_output_qty +
                        cpol.purchase_qty) / cpol.average_consumption

    # View Section
    @api.onchange(
        'product_code_inv', 'product_name_inv', 'product_price_inv',
        'package_qty_inv', 'price_policy')
    def onchange_product_info(self):
        self.state = 'updated'

    @api.onchange(
        'computed_purchase_order_id', 'product_id',
    )
    def onchange_product_id(self):
        fiscal_obj = self.pool.get('account.fiscal.position')
        vals = {
            'state': 'new',
            'purchase_qty': 0,
            'manual_input_output_qty': 0,
        }
        if self.product_id:
            psi_obj = self.env['product.supplierinfo']
            pp = self.product_id
            computed_qty = pp.qty_available

            if self.computed_purchase_order_id:
                cpo = self.computed_purchase_order_id
                # Check if the product is already in the list.
                products = [x.product_id.id for x in cpo.line_ids]
                if self.product_id.id in products:
                    raise ValidationError(
                        _('This product is already in the list!'))
                if cpo.compute_pending_quantity:
                    computed_qty += pp.incoming_qty - pp.outgoing_qty
            vals.update({
                'qty_available': pp.qty_available,
                'incoming_qty': pp.incoming_qty,
                'outgoing_qty': pp.outgoing_qty,
                'computed_qty': computed_qty,
                'weight': pp.weight,
                'uom_po_id': pp.uom_id.id,
                'product_price_inv': 0,
                'price_policy': 'uom',
                'package_qty_inv': 0,
                'average_consumption': pp.displayed_average_consumption,
                'consumption_range': pp.display_range,
                'taxes_id': [[6, 0, fiscal_obj.map_tax(cr, uid, False, self.product_id.taxes_id, context=self._context)]],
            })

            # If product is in the supplierinfo,
            # retrieve values and set state up_to_date
            psi_id = psi_obj.search([
                ('name', '=', self.computed_purchase_order_id.partner_id.id),
                ('product_tmpl_id', '=', pp.product_tmpl_id.id)])
            if psi_id:
                psi = psi_id[0]
                qty_price_val = psi.price
                for qty_price in psi.pricelist_ids:
                    if vals['computed_qty'] >= qty_price.min_quantity:
                        qty_price_val = qty_price.price

                vals.update({
                    'product_code_inv': psi.product_code,
                    'product_name_inv': psi.product_name,
                    'product_price_inv': qty_price_val,
                    #'price_policy': psi.price_policy,
                    'package_qty_inv': psi.package_qty,
                    'uom_po_id': psi.product_uom.id,
                    'state': 'up_to_date',
                })
            self.qty_available = vals['qty_available']
            self.incoming_qty = vals['incoming_qty']
            self.outgoing_qty = vals['outgoing_qty']
            self.computed_qty = vals['computed_qty']
            self.weight = vals['weight']
            self.uom_po_id = vals['uom_po_id']
            self.product_price_inv = vals['product_price_inv']
            #self.price_policy = vals['price_policy']
            self.package_qty_inv = vals['package_qty_inv']
            self.average_consumption = vals['average_consumption']
            self.consumption_range = vals['consumption_range']

    @api.multi
    def unlink_psi(self):
        psi_obj = self.env["product.supplierinfo"]
        for cpol in self:
            cpo = cpol.computed_purchase_order_id
            partner_id = cpo.partner_id.id
            product_tmpl_id = cpol.product_id.product_tmpl_id.id
            psi_ids = psi_obj.search([
                ('name', '=', partner_id),
                ('product_tmpl_id', '=', product_tmpl_id)])
            psi_ids.unlink()
            cpol.unlink()

    @api.multi
    def create_psi(self):
        psi_obj = self.env['product.supplierinfo']
        for cpol in self:
            cpo = cpol.computed_purchase_order_id
            partner_id = cpo.partner_id.id
            product_tmpl_id = cpol.product_id.product_tmpl_id.id
            vals = {
                'name': partner_id,
                'product_name': cpol.product_name,
                'product_code': cpol.product_code,
                'product_uom': cpol.uom_po_id.id,
                'package_qty': cpol.package_qty_inv,
                'min_qty': cpol.package_qty,
                'product_id': product_tmpl_id,
                'pricelist_ids': [(0, 0, {
                    'min_quantity': 0, 
                    'price': cpol.product_price_inv})],
                'price_policy': cpol.price_policy,
            }
            psi_id = psi_obj.create(vals)
            cpol.state = 'up_to_date'
        return psi_id
