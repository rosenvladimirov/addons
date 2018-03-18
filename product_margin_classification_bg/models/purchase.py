# -*- coding: utf-8 -*-
#
#
#    Copyright 2017 Rosen Vladimirov
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
#

from openerp import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    margin_classification_id = fields.Many2one(
        comodel_name='product.margin.classification',
        string='Margin Classification',
        readonly=True)

    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
                            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
                            name=False, price_unit=False, state='draft', context=None
                            ):

        vals = super(purchase_order_line, self).onchange_product_id(
            cr, uid, ids, pricelist_id, product_id, qty, uom_id, partner_id, date_order=date_order,
            fiscal_position_id=fiscal_position_id, date_planned=date_planned,name=name, price_unit=price_unit,
            state=state, context=context
        )

        if not product_id:
            return vals
        product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
        #call name_get() with partner in the context to eventually match name and description in the seller_ids field
        if product:
            vals['value'].update({'margin_classification_id': product.product_tmpl_id.margin_classification_id})
        return vals

#    @api.model
#    def _check_product_template(self):
#        lines = []
#        for line in self.order_line:
#            template = False
#            tmpl = line.product_id.product_tmpl_id
#            if tmpl.margin_state in ('cheap', 'expensive'):
#            if not template:
#                lines.append((0, 0, {
#                    'product_tmpl_id': tmpl.id,
#                }))
#        return lines
#
#    @api.multi
#    def purchase_confirm(self):
#        self.ensure_one()
#        super(PurchaseOrder, self).purchase_confirm()
#        lines_for_update = self._check_product_template()
#        if lines_for_update:
#            ctx = {'default_wizard_line_ids': lines_for_update}
#            pmc_checker_form = self.env.ref(
#                'product_margin_classification_bg.'
#                'view_product_template_mc_check_form', False)
#            return {
#                'name': _("There is probably a changed cost price. Please check for possible consequences for final customer prices."),
#                'type': 'ir.actions.act_window',
#                'view_mode': 'form',
#                'res_model': 'product.margin.classification.check',
#                'views': [(pmc_checker_form.id, 'form')],
#                'view_id': pmc_checker_form.id,
#                'target': 'new',
#                'context': ctx,
#            }
#        else:
#            self.signal_workflow('purchase_confirm')
