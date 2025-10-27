from flask import Flask, render_template, request
import requests
from dotenv import load_dotenv
import os
import traceback

load_dotenv()
app = Flask(__name__)

API_KEY = os.getenv("API_KEY")  # chave opcional para Currencylayer
CURRENCYLAYER_URL = "http://api.currencylayer.com/live"  # exige access_key
EXCHANGERATE_HOST_CONVERT = "https://api.exchangerate.host/convert"  # fallback (sem key)

def parse_amount(value_str):
    """Converte string para float aceitando vírgula e ponto. Lança ValueError se inválido."""
    if value_str is None:
        raise ValueError("Valor vazio")
    s = value_str.strip().replace(",", ".")
    return float(s)

def try_currencylayer(de, para, amount):
    """
    Tenta usar Currencylayer (base=USD na conta free).
    Retorna (success_bool, message_or_converted_value, debug_dict)
    debug_dict contem status_code, body (str) para logs.
    """
    debug = {}
    if not API_KEY:
        return False, "Sem API_KEY para Currencylayer.", debug

    symbols = f"{de},{para}"
    url = f"{CURRENCYLAYER_URL}?access_key={API_KEY}&currencies={symbols}&source=USD"
    try:
        resp = requests.get(url, timeout=8)
        debug["status_code"] = resp.status_code
        debug["body"] = resp.text[:1000]
        data = resp.json()
    except Exception as e:
        debug["exception"] = str(e)
        return False, f"Erro de conexão com Currencylayer: {e}", debug

    # Checagem de sucesso no retorno da API
    if not data.get("success", False):
        # retorna mensagem específica quando disponível
        err_info = data.get("error", {}).get("info", "Erro desconhecido da Currencylayer.")
        return False, f"Currencylayer: {err_info}", debug

    quotes = data.get("quotes", {})  # ex: {"USDBRL": 5.2, "USDEUR": 0.92, ...}

    # Monta chaves esperadas
    key_usd_de = f"USD{de}"
    key_usd_para = f"USD{para}"

    # Verifica se temos as taxas necessárias. Lida com casos envolvendo USD.
    try:
        if de == "USD" and para == "USD":
            # USD -> USD (mesma moeda)
            converted = amount
            return True, converted, debug

        if de == "USD":
            # USD -> PARA: usar USD->PARA
            if key_usd_para not in quotes:
                return False, f"Taxa USD->{para} não encontrada na Currencylayer.", debug
            rate_usd_para = float(quotes[key_usd_para])  # 1 USD = X PARA
            converted = amount * rate_usd_para
            return True, converted, debug

        if para == "USD":
            # DE -> USD: preciso do USD->DE e inverter
            if key_usd_de not in quotes:
                return False, f"Taxa USD->{de} não encontrada na Currencylayer.", debug
            rate_usd_de = float(quotes[key_usd_de])  # 1 USD = X DE
            # então 1 DE = 1 / (1 USD in DE)
            converted = amount * (1.0 / rate_usd_de)
            return True, converted, debug

        # Caso geral DE != USD e PARA != USD:
        # 1 DE em USD = 1 / (USD -> DE)
        # 1 USD em PARA = (USD -> PARA)
        if key_usd_de not in quotes or key_usd_para not in quotes:
            return False, "Taxas necessárias não encontradas na Currencylayer.", debug

        rate_usd_de = float(quotes[key_usd_de])   # 1 USD = X DE
        rate_usd_para = float(quotes[key_usd_para]) # 1 USD = Y PARA

        # 1 DE em USD = 1 / rate_usd_de
        # taxa DE -> PARA = (1 / rate_usd_de) * rate_usd_para
        taxa_de_para = (1.0 / rate_usd_de) * rate_usd_para
        converted = amount * taxa_de_para
        return True, converted, debug

    except Exception as e:
        debug["exception"] = str(e)
        return False, f"Erro ao processar taxas Currencylayer: {e}", debug

def try_exchangerate_host(de, para, amount):
    """
    Usa exchangerate.host (sem chave) endpoint convert.
    Retorna (success_bool, converted_value_or_message, debug_dict)
    """
    debug = {}
    params = {"from": de, "to": para, "amount": amount}
    try:
        resp = requests.get(EXCHANGERATE_HOST_CONVERT, params=params, timeout=8)
        debug["status_code"] = resp.status_code
        debug["body"] = resp.text[:1000]
        data = resp.json()
        # exchangerate.host retorna 'result' com valor convertido
        if resp.status_code == 200 and data.get("result") is not None:
            return True, float(data["result"]), debug
        else:
            # tente extrair mensagem de erro
            msg = data.get("error") or data.get("info") or "Resposta inválida da exchangerate.host"
            return False, f"exchangerate.host: {msg}", debug
    except Exception as e:
        debug["exception"] = str(e)
        return False, f"Erro de conexão com exchangerate.host: {e}", debug

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    alert_type = None
    valor_input = None
    moeda_origem_input = ""
    moeda_destino_input = ""

    if request.method == "POST":
        # Lê campos com os nomes que o seu HTML usa
        valor_raw = request.form.get("amount", "").strip()
        moeda_origem_input = request.form.get("fromCurrency", "").upper()
        moeda_destino_input = request.form.get("toCurrency", "").upper()

        # Mantém o valor digitado para reapresentar no form
        valor_input = valor_raw

        # Validações básicas
        if not valor_raw or not moeda_origem_input or not moeda_destino_input:
            resultado = "Preencha todos os campos."
            alert_type = "warning"
            return render_template("index.html",
                                   resultado=resultado,
                                   alert_type=alert_type,
                                   valor_input=valor_input,
                                   moeda_origem_input=moeda_origem_input,
                                   moeda_destino_input=moeda_destino_input)

        try:
            valor = parse_amount(valor_raw)
        except ValueError:
            resultado = "Valor inválido. Use números (ex: 100.50 ou 100,50)."
            alert_type = "danger"
            return render_template("index.html",
                                   resultado=resultado,
                                   alert_type=alert_type,
                                   valor_input=valor_input,
                                   moeda_origem_input=moeda_origem_input,
                                   moeda_destino_input=moeda_destino_input)

        if valor <= 0:
            resultado = "Informe um valor maior que zero."
            alert_type = "warning"
            return render_template("index.html",
                                   resultado=resultado,
                                   alert_type=alert_type,
                                   valor_input=valor_input,
                                   moeda_origem_input=moeda_origem_input,
                                   moeda_destino_input=moeda_destino_input)

        if moeda_origem_input == moeda_destino_input:
            resultado = "Escolha moedas diferentes para conversão."
            alert_type = "warning"
            return render_template("index.html",
                                   resultado=resultado,
                                   alert_type=alert_type,
                                   valor_input=valor_input,
                                   moeda_origem_input=moeda_origem_input,
                                   moeda_destino_input=moeda_destino_input)

        # 1) Tentar Currencylayer se houver API_KEY
        if API_KEY:
            try:
                ok, value_or_msg, debug = try_currencylayer(moeda_origem_input, moeda_destino_input, valor)
                # Log para debug
                print("Currencylayer attempt debug:", debug)
                if ok:
                    converted = value_or_msg
                    resultado = f"{valor:.2f} {moeda_origem_input} = {converted:.2f} {moeda_destino_input}"
                    alert_type = "success"
                    return render_template("index.html",
                                           resultado=resultado,
                                           alert_type=alert_type,
                                           valor_input=valor_input,
                                           moeda_origem_input=moeda_origem_input,
                                           moeda_destino_input=moeda_destino_input)
                else:
                    # currencylayer devolveu erro (msg em value_or_msg) — vamos tentar fallback
                    print("Currencylayer failed:", value_or_msg)
            except Exception as e:
                print("Exceção ao usar Currencylayer:", e)
                traceback.print_exc()

        # 2) Fallback -> exchangerate.host (sem chave)
        try:
            ok2, value_or_msg2, debug2 = try_exchangerate_host(moeda_origem_input, moeda_destino_input, valor)
            print("exchangerate.host attempt debug:", debug2)
            if ok2:
                converted = value_or_msg2
                resultado = f"{valor:.2f} {moeda_origem_input} = {converted:.2f} {moeda_destino_input}"
                alert_type = "success"
            else:
                # ambos falharam ou exchangerate retornou erro
                resultado = f"Erro ao obter taxa: {value_or_msg2}"
                alert_type = "danger"
        except Exception as e:
            print("Exceção no fallback exchangerate.host:", e)
            traceback.print_exc()
            resultado = "Erro interno ao processar a conversão. Verifique os logs do servidor."
            alert_type = "danger"

    # GET ou após POST com contexto
    return render_template("index.html",
                           resultado=resultado,
                           alert_type=alert_type,
                           valor_input=valor_input,
                           moeda_origem_input=moeda_origem_input,
                           moeda_destino_input=moeda_destino_input)

if __name__ == "__main__":
    app.run(debug=True)
