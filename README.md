<p align="center">
  <img src="assets/banner-conversor.png" alt="Banner do Projeto" width="100%" />
</p>

# 💱 Conversor de Moedas — Flask + CurrencyLayer

Aplicação desenvolvida com **Flask** para conversão de moedas em tempo real utilizando a API **CurrencyLayer**.  
A interface é responsiva, moderna e permite alternância entre tema claro e escuro.

---

## 🚀 Tecnologias Utilizadas

- Python 3.13+
- Flask
- Requests
- Bootstrap 5
- HTML + Jinja2
- API CurrencyLayer
- python-dotenv

---

## 📂 Estrutura do Projeto

```
conversor_moedas/
├── app.py
├── requirements.txt
├── .gitignore
├── .env (não versionado)
├── templates/
│   └── index.html
└── README.md
```

---

## ⚙️ Como Executar o Projeto

### 🔹 Criar o ambiente virtual

```bash
python -m venv venv
```

### 🔹 Ativar o ambiente virtual

Windows:
```bash
venv\Scripts\activate
```

Linux/macOS:
```bash
source venv/bin/activate
```

### 🔹 Instalar dependências

```bash
pip install -r requirements.txt
```

### 🔹 Criar o arquivo `.env`

```env
API_KEY=SUA_CHAVE_DO_CURRENCYLAYER
```

### 🔹 Executar o servidor

```bash
flask run
```

A aplicação estará disponível em:  
👉 http://127.0.0.1:5000

---

## ✨ Funcionalidades

- Conversão entre diversas moedas  
- Interface moderna e responsiva  
- Tema claro/escuro  
- Integração com API externa  
- Tratamento de erros  
- Configuração via `.env`  

---

## 🔧 Melhorias Futuras (Roadmap)

- [ ] Histórico de conversões  
- [ ] Testes unitários (pytest)  
- [ ] Versão PWA  
- [ ] Suporte offline  
- [ ] Dockerfile  
- [ ] API própria para abstração da CurrencyLayer  

---

## 👨‍💻 Autor

**Márcio Ferre Pereira**  
Desenvolvedor Backend & Full-Stack em evolução  
GitHub: https://github.com/ferredev13

---

## 📝 Licença

Projeto sob licença **MIT**.
