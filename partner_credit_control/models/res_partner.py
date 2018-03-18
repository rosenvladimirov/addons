# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, fields, api
from openerp.exceptions import Warning, ValidationError

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.one
    @api.depends('credit_control_line_ids')
    def _credit_control_line_due(self):
        try:
            due_left_sum = [(x.balance_due, x.amount_due) for x in self.credit_control_line_ids if x.last_date == self.last_credit_control_date]
            due_left = sum(x[1] for x in due_left_sum)
            self.credit_control_line_due = due_left
        except:
            self.credit_control_line_due = 0

    @api.one
    @api.depends('credit_control_line_ids','credit', 'debit')
    def _credit_limit_due(self):
        try:
            due_left_sum = [(x.balance_due, x.amount_due) for x in self.credit_control_line_ids if x.last_date == self.last_credit_control_date]
            due_left = sum(x[1] for x in due_left_sum)
            self.credit_limit_due = due_left == 0.0 and self.credit_limit - (self.credit - self.debit) or 0.0
        except:
            self.credit_control_line_due = 0

    credit_control_line_due = fields.Float(
        compute='_credit_control_line_due', store=False,
        string="# Due left", readonly=True, help="Calculate rest of due left credit control")

    credit_limit_due = fields.Float(
        compute='_credit_limit_due', store=False,
        string="Due left credit", readonly=True, help="Calculate rest of due left based on credit limit")

    last_credit_control_date = fields.Datetime(string='Last Credit Control Date')