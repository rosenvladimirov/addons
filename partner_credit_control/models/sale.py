# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange('amount_total')
    def onchange_amount_total(self):
        if self.partner_id and self.partner_id.credit_limit_due < self.amount_total:
            mod_obj = self.env['ir.model.data']

            view_rec = self.env['ir.model.data'].get_object_reference(
                    'partner_credit_control', 'credit_control_agree_form')
            view_id = view_rec and view_rec[1] or False

            return {
                'view_type': 'form',
                'view_id': [view_id],
                'view_mode': 'form',
                'res_model': 'credit.control.agree',
                'res_id': self.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': dict(self.env.context, default_partner_id=active_id),
            }
