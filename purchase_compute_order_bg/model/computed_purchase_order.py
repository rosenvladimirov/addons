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

from math import ceil
from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class ComputedPurchaseOrder(models.Model):
    _description = 'Computed Purchase Order'
    _name = 'computed.purchase.order'
    _order = 'id desc'

    # Constant Values
    _DEFAULT_NAME = _('New')

    _STATE = [
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('canceled', 'Canceled'),
    ]

    _TARGET_TYPE = [
        ('product_price_inv_eq', 'Currency'),
        ('time', 'days'),
        ('weight', 'kg'),
    ]

    _VALID_PSI = [
        ('first', 'Consider only the first supplier on the product'),
        ('all', 'Consider all the suppliers registered on the product'),
    ]
    READONLY_STATES = {
        'confirmed': [('readonly', True)],
        'approved': [('readonly', True)],
        'done': [('readonly', True)]
    }

    # Columns section
    name = fields.Char(
        'Computed Purchase Order Reference', size=64, required=True,
        readonly=True, default=_DEFAULT_NAME,
        help="""Unique number of the automated purchase order, computed"""
        """ automatically when the computed purchase order is created.""")
    company_id = fields.Many2one(
        'res.company', 'Company', readonly=True, required=True,
        help="""When you will validate this item, this will create a"""
        """ purchase order for this company.""",
        default=lambda self: self.env.user.company_id,)
    active = fields.Boolean(
        'Active', default=True,
        help="""By unchecking the active field, you may hide this item"""
        """ without deleting it.""")
    state = fields.Selection(_STATE, 'State', required=True, default='draft')
    incoming_date = fields.Date(
        'Wished Incoming Date',
        help="Wished date for products delivery.")
    partner_id = fields.Many2one(
        'res.partner', 'Supplier', required=True,
        domain=[('supplier', '=', True)],
        help="Supplier of the purchase order.")
    pricelist_id = fields.Many2one(
        'product.pricelist', 'Pricelist', required=True, 
        states=READONLY_STATES, 
        help="The pricelist sets the currency used for this purchase order. It also computes the supplier price for the selected products/quantities.")
    currency_id = fields.Many2one(
        'res.currency','Currency', required=True, 
        states=READONLY_STATES)
    fiscal_position = fields.Many2one(
        'account.fiscal.position', 'Fiscal Position')
    line_ids = fields.One2many(
        comodel_name='computed.purchase.order.line',
        inverse_name='computed_purchase_order_id',
        string='Order Lines', help="Products to order.")
    # this is to be able to display the line_ids on 2 tabs of the view
    stock_line_ids = fields.One2many(
        compute='_get_stock_line_ids',
        comodel_name='computed.purchase.order.line',
        inverse_name='computed_purchase_order_id',
        help="Products to order.")
    compute_pending_quantity = fields.Boolean(
        'Pending quantity taken in account', default=True)
    purchase_order_id = fields.Many2one(
        'purchase.order', 'Purchase Order', readonly=True)
    purchase_target = fields.Integer('Purchase Target', default=0)
    target_type = fields.Selection(
        _TARGET_TYPE, 'Target Type', required=True,
        default='product_price_inv_eq',
        help="""This defines the amount of products you want to"""
        """ purchase. \n"""
        """The system will compute a purchase order based on the stock"""
        """ you have and the average consumption of each product."""
        """ * Target type 'Currency': computed purchase order will cost at"""
        """ least the amount specified\n"""
        """ * Target type 'days': computed purchase order will last"""
        """ at least the number of days specified (according to current"""
        """ average consumption)\n"""
        """ * Target type 'kg': computed purchase order will weight at"""
        """ least the weight specified""")
    valid_psi = fields.Selection(
        _VALID_PSI, 'Supplier choice', required=True,
        default='first',
        help="""Method of selection of suppliers""")
    computed_amount = fields.Float(
        compute='_get_computed_amount_duration',
        digits_compute=dp.get_precision('Product Price'),
        string='Amount of the computed order',
        multi='computed_amount_duration')
    computed_amount_tax = fields.Float(
        compute='_get_computed_amount_duration',
        digits_compute=dp.get_precision('Product Price'),
        string='Amount taxes of the computed order',
        multi='computed_amount_duration')
    computed_duration = fields.Integer(
        compute='_get_computed_amount_duration',
        string='Minimum duration after order',
        multi='computed_amount_duration')
    products_updated = fields.Boolean(
        compute='_get_products_updated',
        string='Indicate if there were any products updated in the list')

    # Fields Function section
    @api.onchange('line_ids')
    def _get_stock_line_ids(self):
        for spo in self:
            self.stock_line_ids = self.line_ids

    @api.multi
    def _get_computed_amount_duration(self):
        cur_obj=self.env['res.currency']
        line_obj = self.env['computed.purchase.order.line']
        val1 = val_credit = val_payable = val_tax_advpayable = 0.0
        #cur = self.pricelist_id.currency_id
        for cpo in self:
            min_duration = 999
            amount = 0
            for line in cpo.line_ids:
                if line.average_consumption != 0:
                    duration = (line.computed_qty + line.purchase_qty)\
                        / line.average_consumption
                    min_duration = min(duration, min_duration)
                #val1 += line.subtotal
                line_price = line_obj._calc_line_base_price(line)
                line_qty = line_obj._calc_line_quantity(line)
                total = self.env['account.tax'].compute_all(line_price, line_qty,
                                                          line.product_id, self.partner_id, price_unit_vat=0.0)
                val1 += total['total']
                for c in total['taxes']:
                    val_credit += c.get('amount', 0.0)*c.get('tax_parent_sign', 0.0) if c.get('tax_credit_payable') == 'taxcredit' else 0.0
                    val_payable += c.get('amount', 0.0)*c.get('tax_parent_sign', 0.0) if c.get('tax_credit_payable') == 'taxpay' else 0.0
                    val_tax_advpayable += c.get('amount', 0.0)*c.get('tax_parent_sign', 0.0) if c.get('tax_credit_payable') == 'taxadvpay' else 0.0

                #amount += line.subtotal
            #cpo.computed_amount = amount
            cpo.computed_amount_tax = cur_obj.round(val_credit + val_payable)
            cpo.computed_amount = cur_obj.round(val1)+cpo.computed_amount_tax
            cpo.computed_duration = min_duration

    @api.multi
    def _get_products_updated(self):
        for cpo in self:
            updated = False
            for line in cpo.line_ids:
                if line.state == 'updated':
                    updated = True
                    break
            cpo.products_updated = updated

    @api.onchange('pricelist_id')
    def onchange_pricelist(self):
        if self.pricelist_id:
            _logger.info("Get pricelist %s" % self.pricelist_id.id)
            self.currency_id = self.env['product.pricelist'].browse(self.pricelist_id.id).currency_id.id

    # View Section
    @api.onchange('partner_id','company_id')
    def onchange_partner_id(self):
        # TODO: create a wizard to validate the change
        fp = self.env['account.fiscal.position']
        self.purchase_target = 0
        self.target_type = 'product_price_inv_eq'
        if self.partner_id:
            #supplier = partner.browse(self.partner_id)
            self.fiscal_position = fp.get_fiscal_position(self.company_id.id, self.partner_id.id)
            self.pricelist_id = self.partner_id.property_product_pricelist_purchase.id
            self.currency_id = self.env['product.pricelist'].browse(self.pricelist_id.id).currency_id.id
            self.purchase_target = self.partner_id.purchase_target
            self.target_type = self.partner_id.target_type
            _logger.debug("On change partner %s:%s:%s:%s" % (self.company_id, self.partner_id, self.pricelist_id, self.currency_id))
        self.line_ids = map(lambda x: (2, x.id, False), self.line_ids)

    # Overload Section
    @api.model
    def create(self, vals):
        if vals.get('name', self._DEFAULT_NAME) == self._DEFAULT_NAME:
            vals['name'] = self.env['ir.sequence'].get(
                'computed.purchase.order') or '/'
        _logger.info("Create %s" % vals)
        order = super(ComputedPurchaseOrder, self).create(vals)
        return order

    @api.multi
    def write(self, vals):
        cpo_id = super(ComputedPurchaseOrder, self).write(vals)
        if self.update_sorting(vals):
            self._sort_lines()
        return cpo_id

    @api.multi
    def update_sorting(self, vals):
        for cpo in self:
            try:
                line_ids = vals.get('line_ids', False)
                if not line_ids:
                    return False
                # this context check will allow you to change the field list
                # without overriding the whole function
                need_sorting_fields = self.env.context.get(
                    'need_sorting_fields', False)
                if not need_sorting_fields:
                    need_sorting_fields = [
                        'average_consumption',
                        'computed_qty',
                        'stock_duration',
                        'manual_input_output_qty',
                    ]
                for value in line_ids:
                    if len(value) > 2 and value[2] and isinstance(
                            value[2], dict) and (set(
                            need_sorting_fields) & set(value[2].keys())):
                        return True
                return False
            except:
                return False

    # Private Section
    @api.multi
    def _sort_lines(self):
        cpol_obj = self.env['computed.purchase.order.line']
        for cpo in self:
            lines = cpol_obj.browse([x.id for x in cpo.line_ids]).read(
                ['stock_duration', 'average_consumption'])
            lines = sorted(
                lines, key=lambda line: line['average_consumption'],
                reverse=True)
            lines = sorted(lines, key=lambda line: line['stock_duration'])

            id_index_list = {}
            for i in lines:
                id_index_list[i['id']] = lines.index(i)
            for line_id in id_index_list.keys():
                cpol_obj.browse(line_id).write(
                    {'sequence': id_index_list[line_id]})

    @api.model
    def _make_po_lines(self):
        all_lines = []
        for line in self.line_ids:
            if line.purchase_qty != 0:
                line_values = {
                    'name': "%s%s" % (
                        line.product_code_inv and
                            '[' + line.product_code_inv + '] ' or '',
                        line.product_name_inv or
                            line.product_id.name_template),
                    'product_qty': line.purchase_qty,
                    'product_qty_package': (
                        line.purchase_qty / line.package_qty),
                    #'price_policy': line.price_policy,
                    'date_planned': (
                        self.incoming_date or fields.Date.context_today(self)),
                    'product_uom': line.product_id.uom_po_id.id,
                    'product_id': line.product_id.id,
                    'price_unit': line.product_price_inv,
                    'taxes_id' : line.taxes_id.id,
                    #'taxes_id': [(
                    #    6, 0,
                    #    [x.id for x in line.product_id.supplier_taxes_id])],
                }
                all_lines.append((0, 0, line_values),)
        return all_lines

    @api.multi
    def _compute_purchase_quantities_days(self):
        for cpo in self:
            days = cpo.purchase_target
            for line in cpo.line_ids:
                if line.average_consumption:
                    quantity = max(
                        days * line.average_consumption *
                        line.uom_po_id.factor / line.uom_id.factor -
                        line.computed_qty, 0)
                    if line.package_qty \
                            and quantity % line.package_qty:
                        quantity = ceil(quantity / line.package_qty) *\
                            line.package_qty
                elif line.computed_qty == 0:
                    quantity = line.package_qty or 0
                else:
                    quantity = 0
                line.purchase_qty = quantity
                line.purchase_qty_package = quantity / line.package_qty

    @api.multi
    def _compute_purchase_quantities_other(self, field):
        #_logger.info("Start compute %s" % field)
        for cpo in self:
            cpol_obj = self.env['computed.purchase.order.line']
            if not cpo.line_ids:
                return False
            target = cpo.purchase_target
            ok = False
            days = -1
            field_list = cpol_obj.browse(
                [x.id for x in cpo.line_ids]).read([field])
            field_list_dict = {}
            for i in field_list:
                field_list_dict[i['id']] = i[field]

            while not ok:
                days += 1
                qty_tmp = {}
                for line in cpo.line_ids:
                    if line.average_consumption:
                        quantity = max(
                            days * line.average_consumption *
                            line.uom_po_id.factor / line.uom_id.factor -
                            line.computed_qty, 0)
                        if line.package_qty and\
                                quantity % line.package_qty:
                            quantity = ceil(quantity / line.package_qty)\
                                * line.package_qty
                    elif line.computed_qty == 0:
                        quantity = line.package_qty or 0
                    else:
                        quantity = 0
                    qty_tmp[line.id] = quantity
                    #_logger.info("Line %s:%s:%s:%s" % (line.average_consumption, line.computed_qty, quantity, days))
                ok = cpo._check_purchase_qty(target, field_list_dict, qty_tmp)
                #_logger.info("Other copute %s:%s:%s:%s" % (ok, target, field_list, qty_tmp))
            for line in cpo.line_ids:
                line.purchase_qty = qty_tmp[line.id]
                line.purchase_qty_package = qty_tmp[line.id] / line.package_qty

    @api.model
    def _check_purchase_qty(self, target=0, field_list=None, qty_tmp=None):
        if not target or field_list is None or qty_tmp is None:
            return True
        total = 0
        price = 0
        for key in field_list.keys():
            total += field_list[key] * qty_tmp[key]
            price += field_list[key]
        if price == 0.0:
            return True
        return total >= target

    # Action section
    @api.multi
    def compute_active_product_stock(self):
        psi_obj = self.env['product.supplierinfo']
        for cpo in self:
            cpol_list = []
            # TMP delete all rows,
            # TODO : depends on further request to avoid user data to be lost
            cpo.line_ids.unlink()

            # Get product_product and compute stock
            for psi in psi_obj.search([('name', '=', cpo.partner_id.id)]):
                for pp in psi.product_tmpl_id.filtered(
                        lambda pt: pt.state not in ('end', 'obsolete')
                ).product_variant_ids:
                    valid_psi = pp._valid_psi(cpo.valid_psi)
                    if valid_psi and psi in valid_psi[0]:
                        cpol_list.append((0, 0, {
                            'product_id': pp.id,
                            'state': 'up_to_date',
                            'product_code': psi.product_code,
                            'product_name': psi.product_name,
                            'product_price': psi.unit_price,
                            #'price_policy': psi.price_policy,
                            'package_qty': psi.package_qty or psi.min_qty,
                            'displayed_average_consumption':
                            pp.displayed_average_consumption,
                            'consumption_range': pp.display_range,
                            'uom_po_id': psi.product_uom.id,
                        }))
            # update line_ids
            self.line_ids = cpol_list

    @api.multi
    def compute_purchase_quantities(self):
        for cpo in self:
            if any([line.average_consumption for line in cpo.line_ids]):
                if cpo.target_type == 'time':
                    return cpo._compute_purchase_quantities_days()
                else:
                    return cpo._compute_purchase_quantities_other(
                        field=cpo.target_type)

    @api.multi
    def make_order(self):
        for cpo in self:
            po_lines = cpo._make_po_lines()
            if not po_lines:
                raise ValidationError(
                    _('All purchase quantities are set to 0!'))

            po_obj = self.env['purchase.order']
            po_values = {
                'origin': cpo.name,
                'partner_id': cpo.partner_id.id,
                'fiscal_position': cpo.fiscal_position.id,
                'pricelist_id': cpo.pricelist_id.id,
                'currency_id': cpo.currency_id and cpo.currency_id.id or self.env['product.pricelist'].browse(cpo.pricelist_id.id).currency_id.id,
                'location_id': self.env['res.users'].browse(
                    self.env.uid).company_id.partner_id
                .property_stock_customer.id,
                'order_line': po_lines,
                'date_approve': (
                    cpo.incoming_date or fields.Date.context_today(self)),
            }
            #_logger.debug("New order %s:%s:%s:%s:%s" % (po_values, cpo.partner_id.property_product_pricelist_purchase.id, cpo.pricelist_id, cpo.currency_id.id, self.env['product.pricelist'].browse(cpo.pricelist_id.id).currency_id.id))
            po_id = po_obj.create(po_values)
            cpo.state = 'done'
            cpo.purchase_order_id = po_id

            mod_obj = self.env['ir.model.data']
            res = mod_obj.get_object_reference(
                'purchase', 'purchase_order_form')
            res_id = res and res[1] or False
            return {
                'name': _('Purchase Order'),
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(res_id, 'form')],
                'view_id': [res_id],
                'res_model': 'purchase.order',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
                'res_id': po_id.id or False,
            }
