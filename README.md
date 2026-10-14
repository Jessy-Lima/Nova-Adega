# 🍷 Nova Adega

**Sistema de gerenciamento de adega com controle de estoque e ponto de venda (PDV).**

Uma aplicação web desenvolvida com Python e FastAPI para facilitar o gerenciamento de produtos, clientes, categorias, movimentações de estoque e vendas.

---

## 📌 Sobre o projeto

O **Nova Adega** é um sistema de ponto de venda desenvolvido para centralizar as principais tarefas de gerenciamento de uma adega em uma única aplicação.

O sistema permite organizar os produtos, acompanhar o estoque, cadastrar clientes e registrar vendas, tornando o processo de gerenciamento mais prático e organizado.

## ✨ Funcionalidades

- 🔐 **Autenticação:** acesso ao sistema por meio de login.
- 📦 **Produtos:** cadastro, consulta e gerenciamento de produtos.
- 🗂️ **Categorias:** organização dos produtos por categoria.
- 📊 **Controle de estoque:** acompanhamento das quantidades e registro de entradas e saídas.
- 👥 **Clientes:** cadastro e gerenciamento de clientes.
- 🛒 **Ponto de venda (PDV):** seleção de produtos e finalização de vendas.
- 💳 **Formas de pagamento:** possibilidade de utilizar uma ou duas formas de pagamento na mesma venda.
- 🏷️ **Descontos:** aplicação de descontos em valor fixo ou porcentagem.
- 🧾 **Histórico de vendas:** consulta das vendas registradas no sistema.

---

## 🛠️ Tecnologias utilizadas

| Tecnologia | Utilização |
|---|---|
| Python | Linguagem principal do projeto |
| FastAPI | Desenvolvimento das rotas e funcionalidades |
| SQLAlchemy | Comunicação com o banco de dados |
| Alembic | Controle de alterações na estrutura do banco |
| SQLite | Armazenamento dos dados na configuração local |
| Jinja2 | Renderização das páginas HTML |
| HTML5 | Estrutura das páginas |
| CSS3 | Estilização da interface |
| Uvicorn | Execução do servidor da aplicação |
| Pytest | Testes automatizados |

---

## 📋 Pré-requisitos

Antes de executar o projeto, verifique se você possui os seguintes programas instalados:

- Python 3.10 ou superior.
- Git, para clonar o repositório.
- Visual Studio Code ou outro editor de código.

Para verificar se o Python está instalado, execute no terminal:

```bash
python --version
```

Caso o comando não funcione no Windows, tente:

```bash
py --version
```

---

## 🚀 Como executar o projeto

### 1. Clonar o repositório

Abra o terminal e execute:

```bash
git clone https://github.com/Jessy-Lima/Nova-Adega.git
```

Entre na pasta do projeto:

```bash
cd Nova-Adega
```

Se você já baixou o projeto em formato ZIP, extraia os arquivos e abra a pasta principal no terminal ou no Visual Studio Code.

### 2. Criar o ambiente virtual

O ambiente virtual permite instalar as dependências do projeto sem misturá-las com as de outros projetos Python.

No Windows, execute:

```bash
python -m venv .venv
```

Depois, ative o ambiente virtual:

```bash
.venv\Scripts\activate
```

Caso utilize o comando `py` para executar o Python, você também pode criar o ambiente com:

```bash
py -m venv .venv
```

No Linux ou macOS, utilize:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Após a ativação, o terminal normalmente exibirá `(.venv)` no início da linha.

### 3. Instalar as dependências

Com o ambiente virtual ativado, execute:

```bash
python -m pip install --upgrade pip
```

Em seguida, instale as bibliotecas necessárias:

```bash
pip install -r requirements.txt
```

O arquivo `requirements.txt` contém as dependências utilizadas pela aplicação.

### 4. Configurar as variáveis de ambiente

Na pasta principal do projeto, crie um arquivo chamado `.env`.

Para a configuração local com SQLite, adicione:

```env
DATABASE_URL=sqlite:///./banco.db
```

Salve o arquivo antes de continuar.

> **Importante:** confira se essa configuração corresponde à utilizada no projeto. Caso já exista um arquivo `.env` com outras configurações, preserve os valores necessários. Não compartilhe senhas ou credenciais no GitHub.

### 5. Preparar o banco de dados

O projeto utiliza o Alembic para controlar as alterações na estrutura do banco de dados.

Como a estrutura de migrações já faz parte do projeto, não é necessário inicializar o Alembic novamente.

Na pasta principal, execute:

```bash
python -m alembic upgrade head
```

Esse comando aplica as migrações disponíveis e atualiza a estrutura do banco de dados.

#### Criando uma nova migração

Quando houver alterações nos modelos do banco de dados, uma nova migração poderá ser gerada com:

```bash
python -m alembic revision --autogenerate -m "descricao_da_alteracao"
```

Depois de conferir o arquivo gerado, aplique a migração:

```bash
python -m alembic upgrade head
```

> **Atenção:** revise sempre o arquivo de migração antes de aplicá-lo. A geração automática não garante que todas as alterações estejam corretas.

### 6. Executar a aplicação

Com as dependências instaladas e o banco configurado, inicie o servidor:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Se tudo estiver configurado corretamente, a aplicação ficará disponível no endereço:

**http://127.0.0.1:8000**

Abra esse endereço no navegador para acessar o sistema.

O parâmetro `--reload` permite reiniciar automaticamente o servidor quando arquivos Python forem alterados durante o desenvolvimento.

Para encerrar a execução, volte ao terminal e pressione `Ctrl + C`.

---

## 🧪 Como executar os testes

O projeto utiliza o Pytest para executar testes automatizados.

Com o ambiente virtual ativado, execute:

```bash
python -m pytest
```

Para visualizar os testes individualmente:

```bash
python -m pytest -v
```

Caso o Pytest ou alguma dependência necessária aos testes não esteja instalada, confira o arquivo `requirements.txt`. Se necessário, instale:

```bash
python -m pip install pytest httpx
```

Os testes podem verificar o comportamento das rotas e das funcionalidades do sistema, incluindo operações de cadastro, movimentações e vendas.

Se algum teste falhar, verifique a mensagem apresentada no terminal para identificar a causa.

---

## 📁 Estrutura do projeto

A organização principal do projeto segue a estrutura abaixo:

```text
Nova-Adega/
│
├── app/
│   ├── controllers/      # Rotas e funcionalidades do sistema
│   ├── models/           # Modelos e entidades do banco de dados
│   ├── static/           # Arquivos CSS, imagens e outros recursos
│   ├── templates/        # Páginas HTML com Jinja2
│   ├── auth.py           # Funções relacionadas à autenticação
│   ├── database.py       # Configuração do banco de dados
│   └── main.py           # Inicialização da aplicação
│
├── migrations/
│   ├── versions/         # Arquivos de migração
│   └── env.py            # Configuração do Alembic
│
├── tests/                # Testes automatizados
│
├── .env                  # Variáveis de ambiente locais
├── alembic.ini           # Configuração do Alembic
├── requirements.txt      # Dependências do projeto
└── README.md             # Documentação do projeto
```

---

## 🌐 Endereços úteis

Depois de iniciar o servidor, os seguintes endereços poderão ser utilizados:

| Endereço | Descrição |
|---|---|
| http://127.0.0.1:8000 | Acesso à aplicação |
| http://127.0.0.1:8000/docs | Documentação interativa do FastAPI |
| http://127.0.0.1:8000/redoc | Documentação alternativa do FastAPI |

As páginas de gerenciamento e do PDV podem exigir que o usuário esteja autenticado.

---

## ⚠️ Problemas comuns

### O comando `python` não funciona

No Windows, tente utilizar `py` no lugar de `python`.

### O sistema informa que uma biblioteca não foi encontrada

Confira se o ambiente virtual está ativado e execute:

```bash
pip install -r requirements.txt
```

### O banco de dados apresenta erro

Confira se o arquivo `.env` está na pasta principal e se a variável `DATABASE_URL` está configurada corretamente.

### O comando do Alembic apresenta erro

Verifique se você está na pasta principal do projeto, se o ambiente virtual está ativado e se a pasta `migrations/` e o arquivo `alembic.ini` existem.

### A página não abre no navegador

Confira se o servidor foi iniciado sem erros e se você está acessando:

```text
http://127.0.0.1:8000
```

---

## 👥 Objetivo do projeto

O Nova Adega tem como objetivo aplicar conhecimentos de desenvolvimento web, banco de dados, organização de código, autenticação e testes automatizados na construção de um sistema de gerenciamento e ponto de venda.

O projeto também permite praticar o desenvolvimento colaborativo e a implementação de melhorias em funcionalidades existentes.

---

<div align="center">

**🍷 Nova Adega**

*Organização e praticidade para o dia a dia da adega.*

</div>