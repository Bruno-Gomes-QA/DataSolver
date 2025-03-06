# MVP

A primeira versão do **DataSolver** deve permitir que um usuário consiga **resolver um problema de otimização simples** **a partir de um banco de dados**, sem precisar lidar diretamente com o **PuLP**.

### **🛠️ Funcionalidades mínimas para o MVP**

✅ **Conexão com banco de dados** (MySQL, PostgreSQL, SQLite)

✅ **Definição de variáveis de decisão** (baseadas em colunas do banco)

✅ **Definição de objetivo** (**maximizar ou minimizar uma variável**)

✅ **Definição de restrições** (**baseadas em colunas do banco**)

✅ **Execução da otimização via PuLP**

✅ **Retorno da solução em formato estruturado (dicionário)**

---

### **📝 MVP na prática**

O usuário deve ser capaz de fazer algo como:

```python
from datasolver import DataSolver

# Conectar ao banco
solver = DataSolver(config={
    "host": "localhost",
    "user": "root",
    "password": "senha",
    "database": "estoque"
})

# Definir variável de decisão
estoque = solver.add_variable("estoque", min_value=0)

# Definir objetivo
solver.set_objective("minimize", "estoque")

# Adicionar restrições
solver.add_constraint("estoque >= previsao_venda")
solver.add_constraint("estoque * custo <= orçamento")

# Resolver o problema
solution = solver.solve()

# Exibir solução
print(solution)
```

---

### **🔗 Estrutura de Objetos e Responsabilidades para o MVP**

1️⃣ **`DataSolver`** → Gerencia toda a lógica da otimização

- 📌 Conectar ao banco de dados
- 📌 Criar variáveis de decisão
- 📌 Definir objetivos (max/min)
- 📌 Adicionar restrições
- 📌 Resolver o modelo

2️⃣ **`DatabaseConnector`** → Faz a comunicação com o banco

- 📌 Conecta ao banco
- 📌 Executa queries para buscar dados

3️⃣ **`Variable`** → Representa uma variável de decisão

- 📌 Nome, valor mínimo/máximo

4️⃣ **`Constraint`** → Representa uma restrição

- 📌 Expressão matemática baseada no banco

5️⃣ **`SolverEngine`** → Faz a integração com o PuLP

- 📌 Converte as definições para o formato PuLP
- 📌 Executa a otimização