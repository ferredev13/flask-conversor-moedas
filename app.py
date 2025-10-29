from flask import Flask, render_template, request
import requests
import os
import traceback

app = Flask(__name__)

# ---------------------------------------------------------------------
# CONFIGURAÇÕES
# ---------------------------------------------------------------------
API_KEY = os.getenv("CURRENCY_API_KEY")  # Pega a chave da variável de ambiente (se existir)

# ---------------------------------------------------------------------
# FUNÇÃO PARA VALIDAR E CONVERTER VALORES
# ---------------------------------------------------------------------
def parse_amount(valor_raw):
    try:
        valor_raw = valor_raw.replace(",", ".")  # aceita vírgula ou ponto
        valor = float(valor_raw)
        return valor
    except ValueError:
        raise ValueError("Valor inválido. Use apenas números e ponto ou vírgula.")


# ---------------------------------------------------------------------
# FUNÇÃO PARA TENTAR USAR A API CURRENCY LAYER (caso tenha API_KEY)
# ---------------------------------------------------------------------
def try_currencylayer(from_cur, to_cur, amount):
    try:
        url = f"http://api.currencylayer.com/live?access_key={API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Verifica status HTTP
        data = response.json()

        if not isinstance(data, dict):
            return False, "Resposta inesperada da API.", "CurrencyLayer - formato inválido"

        if not data.get("success"):
            return False, data.get("error", {}).get("info", "Erro desconhecido"), "CurrencyLayer falhou"

        rates = data.get("quotes", {})
        from_rate = rates.get(f"USD{from_cur}")
        to_rate = rates.get(f"USD{to_cur}")

        if not from_rate or not to_rate:
            return False, "Moeda não encontrada na API.", "CurrencyLayer - Moeda inválida"

        converted = amount / from_rate * to_rate
        return True, converted, "CurrencyLayer OK"

    except requests.exceptions.RequestException as e:
        return False, f"Erro de conexão com a API: {e}", "CurrencyLayer - conexão falhou"
    except Exception as e:
        return False, f"Erro interno: {e}", "CurrencyLayer - exceção geral"


# ---------------------------------------------------------------------
# FUNÇÃO PARA TENTAR USAR exchangerate.host (sem chave)
# ---------------------------------------------------------------------
def try_exchangerate_host(from_cur, to_cur, amount):
    try:
        url = f"https://api.exchangerate.host/convert?from={from_cur}&to={to_cur}&amount={amount}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict):
            return False, "Resposta inesperada da API.", "exchangerate.host - formato inválido"

        if not data.get("success"):
            return False, "Erro na API exchangerate.host", "exchangerate.host falhou"

        converted = data.get("result")
        if converted is None:
            return False, "Não foi possível obter o valor convertido.", "exchangerate.host - sem resultado"

        return True, converted, "exchangerate.host OK"

    except requests.exceptions.RequestException as e:
        return False, f"Erro de conexão com a API: {e}", "exchangerate.host - conexão falhou"
    except Exception as e:
        return False, f"Erro interno: {e}", "exchangerate.host - exceção geral"


# ---------------------------------------------------------------------
# ROTA PRINCIPAL
# ---------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    alert_type = None
    valor_input = None
    moeda_origem_input = ""
    moeda_destino_input = ""

    if request.method == "POST":
        try:
            # Lê campos do formulário
            valor_raw = request.form.get("amount", "").strip()
            moeda_origem_input = request.form.get("fromCurrency", "").upper()
            moeda_destino_input = request.form.get("toCurrency", "").upper()

            valor_input = valor_raw

            # =======================
            # Validações básicas
            # =======================
            if not valor_raw or not moeda_origem_input or not moeda_destino_input:
                resultado = "Preencha todos os campos."
                alert_type = "warning"
                raise ValueError(resultado)

            valor = parse_amount(valor_raw)

            if valor <= 0:
                resultado = "Informe um valor maior que zero."
                alert_type = "warning"
                raise ValueError(resultado)

            if moeda_origem_input == moeda_destino_input:
                resultado = "Escolha moedas diferentes para conversão."
                alert_type = "warning"
                raise ValueError(resultado)

            # =======================
            # 1️⃣ Tenta Currencylayer (se tiver API_KEY)
            # =======================
            if API_KEY:
                ok, value_or_msg, debug = try_currencylayer(moeda_origem_input, moeda_destino_input, valor)
                print("Currencylayer attempt:", debug)
                if ok:
                    converted = value_or_msg
                    resultado = f"{valor:.2f} {moeda_origem_input} = {converted:.2f} {moeda_destino_input}"
                    alert_type = "success"
                    return render_template("index.html", **locals())
                else:
                    print("Currencylayer falhou:", value_or_msg)

            # =======================
            # 2️⃣ Fallback: exchangerate.host
            # =======================
            ok2, value_or_msg2, debug2 = try_exchangerate_host(moeda_origem_input, moeda_destino_input, valor)
            print("exchangerate.host attempt:", debug2)
            if ok2:
                converted = value_or_msg2
                resultado = f"{valor:.2f} {moeda_origem_input} = {converted:.2f} {moeda_destino_input}"
                alert_type = "success"
            else:
                resultado = f"Erro ao obter taxa: {value_or_msg2}"
                alert_type = "danger"

        except ValueError as e:
            # Erros esperados (como valor inválido)
            print(f"[VALOR INVÁLIDO] {e}")
        except Exception as e:
            # Erros inesperados — loga e mostra mensagem genérica
            resultado = "Erro inesperado ao processar a conversão. Tente novamente."
            alert_type = "danger"
            print(f"[ERRO INTERNO] {e}")
            traceback.print_exc()

    return render_template("index.html", **locals())


# ---------------------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
