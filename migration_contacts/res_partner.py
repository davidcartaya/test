from odoo import fields, models, api, _
import xmlrpc.client
import logging
logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    old_id = fields.Integer('Old ID')

    def action_migrate(self):
        user = 'operacionescto@robinhoodasociados.es'
        password = '21071964alvJ#*'
        host = 'https://gestion-robin-hood-asociados.odoo.com/'
        db = 'groblesonmi-gestion-robin-hood-asociados-main-11273134'

        # Conectar con el servidor remoto
        common = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/common')
        uid = common.authenticate(db, user, password, {})
        models = xmlrpc.client.ServerProxy(f'{host}/xmlrpc/2/object')

        # Obtener IDs ya migrados para evitar duplicados
        existing_ids = self.env['res.partner'].search([('old_id', '!=', False)]).mapped('old_id')

        partner_fields = [
            'avatar_1024', 'avatar_128', 'avatar_1920',
            'avatar_256', 'avatar_512', 'barcode',
            'city', 'color', 'comment', 'commercial_company_name',
            'company_type', 'complete_name', 'contact_address', 'contact_address_inline',
            'country_code',
            'customer_rank', 'date',
            'email',
            'function',
            'im_status',
            'image_1024', 'image_128', 'image_1920', 'image_256', 'image_512',
            'is_company', 'is_public', 'is_published',
            'mobile',
            'name',
            'parent_name',
            'payment_token_count',
            'phone',
            'ref',
            'signup_expiration', 'signup_token', 'signup_type',
            'signup_url', 'signup_valid', 'street', 'street2',
            'supplier_invoice_count', 'supplier_rank', 'title',
            'trust', 'type', 'tz', 'tz_offset', 'ubl_cii_format',
            'vat', 'vies_valid', 'vies_vat_to_check',
            'website', 'website_published',
            'website_url', 'zip',

            'commercial_name_1',  # Nombre Comercial
            'monthly_fee',  # Cuota Mensual
            'birthday_date',  # Fecha Nacimiento
            # 'employee_id',  # Empleado
            # 'internal_user_id',  # Usuario
            'customer_type',  # Tipo Cliente
            'customer_state',  # Estado
            'add_user_date',  # Fecha de Alta
            'birthday_date_1',  # Fecha de Cumpleaños
            'usuario_registros',  # Usuario Registros
            'economic_study',  # Estudio económico
            'loan_to_apply_for',  # Préstamo a solicitar
            'total_income',  # Ingresos Mensuales
            # 'contract_type',  # Tipo Contrato
            'total_debts',  # Total Deuda
            'total_delinquency',  # Total Morosidad
            'do_you_wish_to_consult_with_a_lawyer',  # ¿Deseas consultar con un abogado?
            'posee_vivienda_propia',  # ¿Posee vivienda propia?
            'posee_vivienda_propia1',  # ¿Posee vivienda propia? (duplicado en XML)
            'percentage_of_housing_owned',  # Porcentaje de vivienda que posee
            'deseas_reunificar_tus_deudas1',  # ¿Deseas reunificar tus deudas?
            'listed_in_any_delinquency_file1',  # ¿Está en algún Fichero de Morosidad?
            'te_ha_invitado_un_afiliado',  # ¿Te ha invitado un afiliado?
            'quiero_recibir_novedades_en_mi_e_mail',  # Quiero recibir novedades en mi E-Mail
            'incumplimiento1',  # Incumplimiento
            'devoluciones1',  # Devoluciones
            'financial_institution_1', 'financial_institution_2', 'financial_institution_3',
            'financial_institution_4', 'financial_institution_5', 'financial_institution_6',
            'financial_institution_7', 'financial_institution_8', 'financial_institution_9',
            'financial_institution_10', 'financial_institution_11', 'financial_institution_12',
            'demanded_debt_1', 'demanded_debt_2', 'demanded_debt_3', 'demanded_debt_4',
            'demanded_debt_5', 'demanded_debt_6', 'demanded_debt_7', 'demanded_debt_8',
            'demanded_debt_9', 'demanded_debt_10', 'demanded_debt_11', 'demanded_debt_12',
            'payment_start_date',  # Fecha de Inicio de Pagos
            'fecha_de_fin_de_pagos',  # Fecha de fin de Pagos
            'total_amount_of_debts',  # Importe Total de sus Deudas
            'total_to_pay',  # Total a Pagar
            'installments',  # Cuotas
            'amount_per_installment',  # Importe por Cuota
            'requested_capital_1', 'requested_capital_2', 'requested_capital_3',
            'requested_capital_4', 'requested_capital_5', 'requested_capital_6',
            'requested_capital_7', 'requested_capital_8', 'requested_capital_9',
            'paid_capital_1', 'paid_capital_2', 'paid_capital_3',
            'paid_capital_4', 'paid_capital_5', 'paid_capital_6',
            'paid_capital_7', 'paid_capital_8', 'paid_capital_9',
            'estado_de_informes'  # Estatus de informes
        ]


        remote_partners = models.execute_kw(db, uid, password, 'res.partner', 'search_read', 
            [[['id', 'not in', existing_ids]]], 
            {'fields': partner_fields, 'limit': 200}
        )

        logger.info(f'Se encontraron {len(remote_partners)} contactos para migrar.')

        count = 0

        
        
        for partner in remote_partners:
            try:
                if self.env['res.partner'].search([('old_id', '=', partner['id'])], limit=1):
                    continue

                # Función para obtener el primer valor de una lista si existe
                def get_valid_id(field_value):
                    return field_value[0] if isinstance(field_value, list) and field_value else False

                state_id = get_valid_id(partner.get('state_id'))
                country_id = get_valid_id(partner.get('country_id'))

                state = self.env['res.country.state'].browse(state_id) if state_id else False
                country = self.env['res.country'].browse(country_id) if country_id else False
                

                vals = {}
                for field in partner_fields:
                    value = partner.get(field)

                    if isinstance(value, str):
                        vals[field] = value.strip()

                    elif isinstance(value, (int, float)):
                        vals[field] = value

                    elif isinstance(value, list) and value:
                        vals[field] = value[0]

                    else:
                        vals[field] = False

                vals.update({
                    'state_id': state.id if state else False,
                    'country_id': country.id if country else False,
                    'old_id': partner['id'],
                })

                new_partner = self.env['res.partner'].create(vals)

                logger.info(f'Migrado contacto: {new_partner.name} (ID remoto: {partner["id"]})')

                count += 1
                self.env.cr.commit()

            except Exception as e:
                logger.error(f'Error al migrar el contacto {partner["id"]}: {str(e)}')
                continue

        logger.info(f'Migración completada: {count} contactos importados.')

