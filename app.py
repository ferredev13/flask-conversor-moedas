# ---------------------------------------------------------------------
# ARQUIVO: app.py
# DESCRIÇÃO: Aplicação Flask para conversão de moedas utilizando a API CurrencyLayer.
# AUTOR: [Márcio Ferre e Bruno Malosti]
# ---------------------------------------------------------------------

from flask import Flask, render_template, request
import requests
import os
import traceback
from dotenv import load_dotenv

# ---------------------------------------------------------------------
# CONFIGURAÇÕES INICIAIS
# ---------------------------------------------------------------------
# Carrega variáveis do arquivo .env
load_dotenv()

app = Flask(__name__)

# Lê a chave da API a partir do arquivo .env
API_KEY = os.getenv("API_KEY")


# ---------------------------------------------------------------------
# FUNÇÃO PARA VALIDAR E CONVERTER VALORES
# ---------------------------------------------------------------------
def parse_amount(valor_raw):
    """
    Converte o valor informado pelo usuário (string) em float,
    aceitando vírgula ou ponto decimal.
    """
    try:
        valor_raw = valor_raw.replace(",", ".")  # aceita vírgula ou ponto
        valor = float(valor_raw)
        return valor
    except ValueError:
        raise ValueError("Valor inválido. Use apenas números e ponto ou vírgula.")


# ---------------------------------------------------------------------
# FUNÇÃO PARA USAR A API CURRENCY LAYER (COM CHAVE)
# ---------------------------------------------------------------------
def convert_currency(from_cur, to_cur, amount):
    """
    Converte um valor de uma moeda para outra utilizando a API CurrencyLayer.

    A API gratuita da CurrencyLayer retorna apenas taxas baseadas no USD.
    Por isso, são tratados três cenários:
      1. USD -> outra moeda
      2. outra moeda -> USD
      3. moeda -> moeda (nenhuma é USD)
    """
    try:
        url = f"http://api.currencylayer.com/live?access_key={API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()

        # Validação de retorno da API
        if not data.get("success"):
            return False, data.get("error", {}).get("info", "Erro desconhecido")

        rates = data["quotes"]

        # ------------------------------
        # CASO 1: USD -> outra moeda
        # ------------------------------
        if from_cur == "USD":
            to_rate = rates.get(f"USD{to_cur}")
            if not to_rate:
                return False, f"Moeda de destino '{to_cur}' não encontrada na API."
            converted = amount * to_rate

        # ------------------------------
        # CASO 2: outra moeda -> USD
        # ------------------------------
        elif to_cur == "USD":
            from_rate = rates.get(f"USD{from_cur}")
            if not from_rate:
                return False, f"Moeda de origem '{from_cur}' não encontrada na API."
            converted = amount / from_rate

        # ------------------------------
        # CASO 3: moeda -> moeda (nenhuma é USD)
        # ------------------------------
        else:
            from_rate = rates.get(f"USD{from_cur}")
            to_rate = rates.get(f"USD{to_cur}")

            if not from_rate or not to_rate:
                return False, "Moeda não encontrada na API."

            # Converte primeiro para USD e depois para a moeda destino
            converted = amount / from_rate * to_rate

        return True, converted

    except Exception as e:
        print("[ERRO INTERNO NA API]", e)
        traceback.print_exc()
        return False, "Erro interno ao acessar a API."


# ---------------------------------------------------------------------
# ROTA PRINCIPAL
# ---------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    """
    Rota principal da aplicação Flask.
    Recebe os dados do formulário, valida as entradas e realiza a conversão.
    """
    resultado = None
    alert_type = None
    valor_input = ""
    moeda_origem_input = ""
    moeda_destino_input = ""

    # Lista de moedas disponíveis no dropdown
    moedas = [
        ("USD", "Dólar (USD)"),
        ("BRL", "Real (BRL)"),
        ("EUR", "Euro (EUR)"),
        ("GBP", "Libra (GBP)"),
        ("JPY", "Iene (JPY)"),
        ("CAD", "Dólar Canadense (CAD)"),
        ("AUD", "Dólar Australiano (AUD)"),
        ("CHF", "Franco Suíço (CHF)"),
    ]

    if request.method == "POST":
        try:
            # ------------------------------
            # LEITURA DOS DADOS DO FORMULÁRIO
            # ------------------------------
            valor_raw = request.form.get("amount", "").strip()
            moeda_origem_input = request.form.get("fromCurrency", "").upper()
            moeda_destino_input = request.form.get("toCurrency", "").upper()
            valor_input = valor_raw

            # ------------------------------
            # VALIDAÇÕES INICIAIS
            # ------------------------------
            if not API_KEY:
                resultado = "Chave de API não configurada. Defina API_KEY no arquivo .env."
                alert_type = "danger"
                raise ValueError(resultado)

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

            # ------------------------------
            # CHAMADA À API
            # ------------------------------
            ok, value_or_msg = convert_currency(moeda_origem_input, moeda_destino_input, valor)

            if ok:
                resultado = f"{valor:.2f} {moeda_origem_input} = {value_or_msg:.2f} {moeda_destino_input}"
                alert_type = "success"
            else:
                resultado = f"Erro ao obter taxa: {value_or_msg}"
                alert_type = "danger"

        except ValueError as e:
            print(f"[VALOR INVÁLIDO] {e}")
        except Exception as e:
            resultado = "Erro inesperado ao processar a conversão. Tente novamente."
            alert_type = "danger"
            print(f"[ERRO INTERNO] {e}")
            traceback.print_exc()

    return render_template("index.html", **locals())


# ---------------------------------------------------------------------
# EXECUÇÃO DO APLICATIVO
# ---------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
