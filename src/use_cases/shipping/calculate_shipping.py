from decimal import Decimal

from src.schemas.shipping_schema import ShippingQuoteResponse


class CalculateShippingUseCase:
    _SOUTHEAST_STATES = {"SP", "RJ", "MG", "ES"}
    _SOUTH_STATES = {"PR", "SC", "RS"}
    _BASE_RATES = {
        "SP": Decimal("18.00"),
        "RJ": Decimal("22.00"),
        "MG": Decimal("22.00"),
        "ES": Decimal("24.00"),
        "PR": Decimal("28.00"),
        "SC": Decimal("28.00"),
        "RS": Decimal("30.00"),
    }
    _DEFAULT_RATE = Decimal("35.00")
    _EXTRA_ITEM_FEE = Decimal("8.00")

    @staticmethod
    def _normalize_cep(cep: str) -> str:
        return cep.replace("-", "").strip()

    def _resolve_state_from_cep(self, cep: str) -> str | None:
        prefix = cep[:2]
        cep_state_map = {
            "01": "SP",
            "02": "SP",
            "03": "SP",
            "04": "SP",
            "05": "SP",
            "06": "SP",
            "07": "SP",
            "08": "SP",
            "09": "SP",
            "10": "SP",
            "11": "SP",
            "12": "SP",
            "13": "SP",
            "14": "SP",
            "15": "SP",
            "16": "SP",
            "17": "SP",
            "18": "SP",
            "19": "SP",
            "20": "RJ",
            "21": "RJ",
            "22": "RJ",
            "23": "RJ",
            "24": "RJ",
            "25": "RJ",
            "26": "RJ",
            "27": "RJ",
            "28": "RJ",
            "29": "ES",
            "30": "MG",
            "31": "MG",
            "32": "MG",
            "33": "MG",
            "34": "MG",
            "35": "MG",
            "36": "MG",
            "37": "MG",
            "38": "MG",
            "39": "MG",
            "40": "BA",
            "41": "BA",
            "42": "BA",
            "43": "BA",
            "44": "BA",
            "45": "BA",
            "46": "BA",
            "47": "BA",
            "48": "BA",
            "49": "SE",
            "50": "PE",
            "51": "PE",
            "52": "PE",
            "53": "PE",
            "54": "PE",
            "55": "PE",
            "56": "PE",
            "57": "AL",
            "58": "PB",
            "59": "RN",
            "60": "CE",
            "61": "CE",
            "62": "CE",
            "63": "CE",
            "64": "GO",
            "65": "GO",
            "66": "GO",
            "67": "GO",
            "68": "PA",
            "69": "AM",
            "70": "DF",
            "71": "DF",
            "72": "GO",
            "73": "BA",
            "74": "GO",
            "75": "GO",
            "76": "GO",
            "77": "TO",
            "78": "MT",
            "79": "MS",
            "80": "PR",
            "81": "PR",
            "82": "PR",
            "83": "PR",
            "84": "PR",
            "85": "PR",
            "86": "PR",
            "87": "PR",
            "88": "SC",
            "89": "SC",
            "90": "RS",
            "91": "RS",
            "92": "RS",
            "93": "RS",
            "94": "RS",
            "95": "RS",
            "96": "RS",
            "97": "RS",
            "98": "RS",
            "99": "RS",
        }
        return cep_state_map.get(prefix)

    def execute(
        self,
        cep: str,
        shipping_method: str,
        item_count: int,
        state: str | None = None,
    ) -> ShippingQuoteResponse:
        if shipping_method == "RETIRADA":
            return ShippingQuoteResponse(
                shipping_method=shipping_method,
                frete=Decimal("0"),
                label="Retirada/combinar com a loja",
            )

        normalized_cep = self._normalize_cep(cep)
        if len(normalized_cep) != 8:
            raise ValueError("CEP inválido")

        resolved_state = (state or self._resolve_state_from_cep(normalized_cep) or "").upper()
        base_rate = self._BASE_RATES.get(resolved_state, self._DEFAULT_RATE)

        extra_items = max(item_count - 1, 0)
        frete = base_rate + (self._EXTRA_ITEM_FEE * extra_items)

        return ShippingQuoteResponse(
            shipping_method=shipping_method,
            frete=frete,
            label=f"Entrega — {resolved_state or 'Brasil'}",
        )
