# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    pricelist_id = fields.Many2one(
        comodel_name="product.pricelist",
        string="Pricelist",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.constrains("pricelist_id", "currency_id")
    def _check_currency(self):
        for sel in self.filtered(lambda a: a.pricelist_id and a.is_invoice()):
            if sel.pricelist_id.currency_id != sel.currency_id:
                raise UserError(
                    _("Pricelist and Invoice need to use the same currency.")
                )

    @api.onchange("partner_id", "company_id")
    def _onchange_partner_id_account_invoice_pricelist(self):
        if self.is_invoice():
            if (
                self.partner_id
                and self.move_type in ("out_invoice", "out_refund")
                and self.partner_id.property_product_pricelist
            ):
                self.pricelist_id = self.partner_id.property_product_pricelist
                self._set_pricelist_currency()

    @api.onchange("pricelist_id")
    def _set_pricelist_currency(self):
        if (
            self.is_invoice()
            and self.pricelist_id
            and self.currency_id != self.pricelist_id.currency_id
        ):
            self.currency_id = self.pricelist_id.currency_id

    def button_update_prices_from_pricelist(self):
        for inv in self.filtered(lambda r: r.state == "draft"):
            inv.invoice_line_ids._onchange_product_id_account_invoice_pricelist()
        self.filtered(lambda r: r.state == "draft").with_context(
            check_move_validity=False
        )._move_autocomplete_invoice_lines_values()
        self.filtered(lambda r: r.state == "draft").with_context(
            check_move_validity=False
        )._recompute_tax_lines()

    def _reverse_move_vals(self, default_values, cancel=True):
        move_vals = super(AccountMove, self)._reverse_move_vals(
            default_values, cancel=cancel
        )
        if self.pricelist_id:
            move_vals["pricelist_id"] = self.pricelist_id.id
        return move_vals


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.onchange("product_id", "quantity")
    def _onchange_product_id_account_invoice_pricelist(self):
        for sel in self:
            if not sel.move_id.pricelist_id:
                return
            sel.with_context(check_move_validity=False).update(
                {"price_unit": sel._get_price_with_pricelist()}
            )


    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        PricelistItem = self.env["product.pricelist.item"]
        field_name = "lst_price"
        currency_id = None
        product_currency = product.currency_id
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            while (
                pricelist_item.base == "pricelist"
                and pricelist_item.base_pricelist_id
                and pricelist_item.base_pricelist_id.discount_policy
                == "without_discount"
            ):
                price, rule_id = pricelist_item.base_pricelist_id.with_context(
                    uom=uom.id
                ).get_product_price_rule(product, qty, self.move_id.partner_id)
                pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == "standard_price":
                field_name = "standard_price"
                product_currency = product.cost_currency_id
            elif (
                pricelist_item.base == "pricelist" and pricelist_item.base_pricelist_id
            ):
                field_name = "price"
                product = product.with_context(
                    pricelist=pricelist_item.base_pricelist_id.id
                )
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(
                    product_currency,
                    currency_id,
                    self.company_id or self.env.company,
                    self.move_id.invoice_date or fields.Date.today(),
                )

        product_uom = self.env.context.get("uom") or product.uom_id.id
        if uom and uom.id != product_uom:
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id

    def _calculate_discount(self, base_price, final_price):
        discount = (base_price - final_price) / base_price * 100
        if (discount < 0 and base_price > 0) or (discount > 0 and base_price < 0):
            discount = 0.0
        return discount

    def _get_price_with_pricelist(self):
        price_unit = 0.0
        if self.move_id.pricelist_id and self.product_id and self.move_id.is_invoice():
            product = self.product_id
            qty = self.quantity or 1.0
            date = self.move_id.invoice_date or fields.Date.today()
            uom = self.product_uom_id
            (
                final_price,
                rule_id,
            ) = self.move_id.pricelist_id._get_product_price_rule(
                product,
                qty,
                uom=uom,
                date=date,
            )
            if self.move_id.pricelist_id.discount_policy == "with_discount":
                price_unit = self.env["account.tax"]._fix_tax_included_price_company(
                    final_price,
                    product.taxes_id,
                    self.tax_ids,
                    self.company_id,
                )
                self._set_discount(0.0)
                return price_unit
            else:
                rule_id = self.env["product.pricelist.item"].browse(rule_id)
                while (
                    rule_id.base == "pricelist"
                    and rule_id.base_pricelist_id.discount_policy == "without_discount"
                ):
                    new_rule_id = rule_id.base_pricelist_id._get_product_rule(
                        product, qty, uom=uom, date=date
                    )
                    rule_id = self.env["product.pricelist.item"].browse(new_rule_id)
                base_price = rule_id._compute_base_price(
                    product,
                    qty,
                    uom,
                    date,
                    currency=self.currency_id,
                )
                price_unit = max(base_price, final_price)
                self._set_discount(self._calculate_discount(base_price, final_price))
        return price_unit

    def _set_discount(self, amount):
        if self.env["account.move.line"]._fields.get("discount1", False):
            # OCA/account_invoice_triple_discount is installed
            fname = "discount1"
        else:
            fname = "discount"
        self.with_context(check_move_validity=False)[fname] = amount
        
    def _compute_price_unit(self):
        for rec in self:
            super(AccountMoveLine, rec)._compute_price_unit()
            if rec.move_id.pricelist_id and rec.move_id.is_invoice():
                rec.price_unit = rec._get_price_with_pricelist()

    
class Pricelist(models.Model):
    _inherit = "product.pricelist"
    
    discount_policy = fields.Selection([
            ('with_discount', 'La remise est comprise dans le prix indiqué'),
            ('without_discount', 'Afficher le prix public et la remise au client')],
            default='with_discount', required=True)
