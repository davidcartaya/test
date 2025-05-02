# -*- coding: utf-8 -*-

from odoo import models, _, api, fields
from datetime import date, datetime


class AccountAdvancedPayment(models.Model):
    _inherit = 'account.advanced.payment'

    register_send_mail = fields.Boolean(string='Registro enviado por correo?')

    def action_register_advance(self):
        # funcionalidad del boton validate este hace llamada a las fucniones que realizan los asientos contables'''
        if self.state == 'draft':
            self.validate_amount_advance()
            self.get_move_register()
            self.register_send_mail_template()
        elif self.state == 'posted' or 'available':
            self.validate_invoice_apply()
            self.validate_amount_apply()
            self.resta_amount_available()
            self.get_move_apply()
            self.state = 'paid'
            if self.amount_available > 0:
                self.copy(copy_manual=True)
                self.state = 'paid'
                self.env['account.move'].search([('id', '=', self.invoice_id.id)]).write({'anticipo_ref': self.id})


    def register_send_mail_template(self):
        for record in self:
            template = self.env.ref('initials_mail_template.email_template_initials')
            
            if template:
                template.email_from = self.env.user.email_formatted or ''
                template.send_mail(record.id, force_send=True)
                
                record.register_send_mail = True

