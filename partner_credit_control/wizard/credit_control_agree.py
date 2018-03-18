# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from openerp import models, fields, api, _

_logger = logging.getLogger('credit.control.agree')

class CreditControlAgree(models.TransientModel):

    _name = 'credit.control.agree'
    _description = 'Add agreement in credit control lines'
    _rec_name = 'partner_id'

    @api.model
    def _get_default_currency(self):
        currency_id = False
        if self._context.get('default_partner_id', False):
            partner = self.env['res.partner'].browse(self._context['default_partner_id'])
            currency_id = partner.property_product_pricelist.currency_id
        return currency_id

    @api.model
    def _get_company(self):
        company_obj = self.env['res.company']
        return company_obj._company_default_get('credit.control.policy')

    @api.model
    def _get_policies(self):
        return self.env['credit.control.policy'].search([])

    @api.model
    def _get_line_ids(self):
        if self._context.get('default_partner_id', False):
            partner = self.env['res.partner'].browse(self._context['default_partner_id'])
            line_obj = self.env['credit.control.line']
            lines = line_obj.search([('partner_id', '=', self._context['default_partner_id']), ('last_date', '=', partner.last_credit_control_date)])
            _logger.info("lines %s:%s" % (lines, partner.last_credit_control_date))
            return lines

    @api.model
    def _compute_credit_due(self):
        _logger.info("Get %s" % self._context.get('default_partner_id', False))
        if self._context.get('default_partner_id', False):
            partner = self.env['res.partner'].browse(self._context['default_partner_id'])
            _logger.info("Get due %s" % partner)
            return partner.credit_limit - (partner.credit - partner.debit)

    partner_id = fields.Many2one('res.partner', 'Partner',
                                  required=True,
                                  default=lambda self, *a: self._context.get('default_partner_id') and self._context['default_partner_id'])
    last_credit_control_date = fields.Datetime(comodel_name="res.partner", string="Last date control", related="partner_id.last_credit_control_date", readonly=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self, *a: self._context.get('default_currency_id') and slef._context['default_currency_id'] or self._get_default_currency())
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 default=_get_company,
                                 required=True)

    credit_control_line_ids = fields.Many2many('credit.control.line',
                                string='Credit Control Lines',
                                default=_get_line_ids)

    policy_id = fields.Many2one(
                                'credit.control.policy',
                                string='Policies',
                                required=True
                                )

    user_id = fields.Many2one('res.users',
                              default=lambda self: self.env.user,
                              string='User')
    total_invoiced = fields.Float(string='Total Invoiced',
                                  compute='_compute_total', store=False)
    total_due = fields.Float(string='Total Due',
                             compute='_compute_total', store=False)

    credit_limit_due = fields.Float(string='Due Credit limit',
                             default=_compute_credit_due)
    amount_due = fields.Float(string='Due Amount Tax incl.',
                              required=True)


    @api.model
    def _get_total(self):
        amount_field = 'credit_control_line_ids.amount_due'
        return sum(self.mapped(amount_field))

    @api.model
    def _get_total_due(self):
        balance_field = 'credit_control_line_ids.balance_due'
        return sum(self.mapped(balance_field))

    @api.one
    @api.depends('credit_control_line_ids',
                 'credit_control_line_ids.amount_due',
                 'credit_control_line_ids.balance_due')

    def _compute_total(self):
        self.total_invoiced = self._get_total()
        self.total_due = self._get_total_due()

    @api.model
    def _create_account_move(self, dt, ref, journal_id, company_id):
        local_context = dict(self._context or {}, company_id=company_id)
        start_at_datetime = datetime.strptime(dt, tools.DEFAULT_SERVER_DATETIME_FORMAT)
        date_tz_user = fields.datetime.context_timestamp(cr, uid, start_at_datetime, context=context)
        date_tz_user = date_tz_user.strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
        period_id = self.env['account.period'].find(dt=date_tz_user)
        return self.env['account.move'].create({'ref': ref, 'journal_id': journal_id, 'period_id': period_id[0]})

    @api.model
    def _create_account_move_line(self, date, ref, partner_id, vals, move_id=None):
        credit_control_agree_journal_setting = safe_eval(self.env['ir.config_parameter'].
                                                        get_param('credit_control_agree_journal_setting',
                                                        default="False"))
        property_obj = self.env['ir.property']
        account_period_obj = self.env['account.period']
        account_move_obj = self.env['account.move']
        cur_obj = self.env['res.currency']
        partner = self.env['res.partner'].browse(partner_id)
        account_def = property_obj.get('property_account_receivable', 'res.partner')
        order_account = partner and \
                        partner.property_account_receivable and \
                        partner.property_account_receivable.id or \
                        account_def and account_def.id
        move_id = self._create_account_move(date, ref, credit_control_agree_journal_setting, self.company_id.id)
        move = account_move_obj.browse(move_id)
        amount_total = 0.0
        for inx, vl in enumerate(vals):
            amount_total += vl[2]['credit'] - vl[2]['debit']
            vals[inx]['partner_id'] = partner_id,
            vals[inx]['journal_id'] = credit_control_agree_journal_setting
            vals[inx]['period_id'] = move.period_id.id
            vals[inx]['move_id'] = move_id
            vals[inx]['company_id'] = self.company_id.id

        vals.append((0, False, {
                    'date': date,
                    'ref': date,
                    'name': _("Agree temporary permit"),
                    'account_id': order_account,
                    'credit': ((amount_total < 0) and -amount_total) or 0.0,
                    'debit': ((amount_total > 0) and amount_total) or 0.0,
                    'partner_id': partner_id,
                    'journal_id': credit_control_agree_journal_setting,
                    'period_id': move.period_id.id,
                    'move_id' : move_id,
                    'company_id': self.company_id.id,
                }))

        move.write({'line_id': vals})
        return move_id

    #@api.one
    #def action_cancel(self):
    #    return {'type': 'ir.actions.act_window_close'}

    @api.one
    def action_next(self):
        credit_line_obj = self.env['credit.control.line']
        controlling_date = self._context['default_date']
        partner_id = self._context['default_partner_id']
        ref = self._context['active_id']
        if not self.policy_id.account_ids:
            raise api.Warning(
                _('You can only use a policy set on '
                  'account \n'
                  'Please choose one of the following '
                  'policies:\n')
            )
            return {'type': 'ir.actions.act_window_close'}

        vals = []
        amount_total = self._context['default_amount_due']
        all_amount_total = 0.0
        for account in self.policy_id.account_ids:
            all_amount_total += amount_total
            vals.append((0, False, {
                        'date': controlling_date,
                        'ref': ref,
                        'name': _("Agree temporary permit"),
                        'account_id': account.id,
                        'credit': ((amount_total < 0) and -amount_total) or 0.0,
                        'debit': ((amount_total > 0) and amount_total) or 0.0,
                        }))
        move_id = self._create_account_move_line(controlling_date, ref, partner_id, all_amount_total, vals)
        amount_due = sum([x.amount_due for x in self.credit_control_line_ids])
        create = credit_line_obj.create_or_update_from_mv_lines
        generated_lines = create(move_id,
                                 self.new_policy_level_id,
                                 controlling_date,
                                 check_tolerance=False)
        generated_lines.write({'amount_due': -amount_due, 'state': 'temporary_permit'})
        #self._set_so_policy(self.move_line_ids, self.new_policy_id)
        return {'type': 'ir.actions.act_window_close'}
