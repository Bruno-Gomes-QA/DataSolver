"""
🔗 ***Módulo para Gerenciar Conexões de Banco de Dados***

📌 **O que faz?**  

Gerencia conexões com múltiplos bancos de dados usando SQLAlchemy.

✅ **Principais recursos:**  

- Suporte a múltiplos bancos de dados 🏦  
- Criação e gerenciamento de conexões simultâneas 🔄  
- Fácil integração com SQLAlchemy 🐍  
- Verificação automática de drivers necessários ⚠️  
- Conexão e transações seguras 🔒  

"""

from importlib import util
from typing import Dict, List, Optional

from pydantic import BaseModel, ValidationError, conint, constr
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.session import Session


class DatabaseConfig(BaseModel):
    """
    ⚙️ **Configuração para Conexão com Banco de Dados**  

    📌 **O que faz?**  
    Define os parâmetros necessários para conectar-se a diferentes bancos de dados.  

    🔥 **Principais recursos:**  
    - Suporte a vários dialetos SQL 🎯  
    - Validação automática de configurações ✅  
    - Fácil integração com SQLAlchemy 🐍  

    **Exemplos de Dialetos:**  
    - 🐘 PostgreSQL: `postgresql+psycopg2`  
    - 🐬 MySQL: `mysql+pymysql`  
    - 🏺 Oracle: `oracle+cx_oracle`  
    - 🏰 SQL Server: `mssql+pyodbc`  
    - 🧪 SQLite: `sqlite://`  

    ⚡ **Instalação de dependências por dialeto:**
    ```bash
    pip install datasolver[postgresql]  # PostgreSQL
    pip install datasolver[mysql]       # MySQL
    pip install datasolver[oracle]      # Oracle
    pip install datasolver[mssql]       # SQL Server
    ```
    """

    name: constr(min_length=3, max_length=50)
    dialect: str
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    host: Optional[str] = None
    port: Optional[conint(gt=0, lt=65536)] = None
    pool_size: conint(gt=0) = 5
    max_overflow: conint(ge=0) = 10


class DatabaseConnectionManager:
    """
    🔌 **Gerenciador de Conexões com Banco de Dados**  

    📌 **O que faz?**  
    Permite criar e gerenciar múltiplas conexões com bancos de dados SQL.  

    ✅ **Principais recursos:**  
    - Suporte a múltiplas conexões simultâneas 🏦  
    - Gerenciamento automático de sessões 🔄  
    - Fechamento seguro de conexões 🔒  
    - Verificação de drivers necessários ⚠️  

    🔥 **Exemplo de uso:**  
    ```python
    config = {
        'name': 'meu_banco',
        'dialect': 'postgresql+psycopg2',
        'username': 'merlin',
        'password': 'abcdefghij',
        'host': 'localhost',
        'database': 'data'
    }

    manager = DatabaseConnectionManager([config])
    with manager.get_session('meu_banco') as sessao:
        sessao.execute('SELECT 1')
    ```
    """

    DIALECT_REQUIREMENTS = {
        'mysql': ['pymysql'],
        'postgresql': ['psycopg2'],
        'oracle': ['cx_oracle'],
        'mssql': ['pyodbc'],
        'sqlite': [],
    }

    def __init__(self, configs: List[Dict]):
        """
        🚀 **Inicializa o gerenciador de conexões**

        🔹 **O que faz?**  
        - Valida as configurações e inicia as conexões com os bancos de dados.

        🛠️ **Parâmetros:**  
        - `configs` (List[Dict]): Lista de configurações de conexão.  

        ⚠️ **Possíveis exceções:**  
        - `ValueError`: Se a configuração estiver incorreta.  
        - `ImportError`: Se o driver necessário não estiver instalado.  

        📝 **Dica:** Para instalar os drivers, use:  
        ```bash
        pip install datasolver[dialeto]
        ```
        """
        self.connections: Dict[str, Dict] = {}
        self.configs: List[DatabaseConfig] = []

        for config in configs:
            try:
                validated_config = DatabaseConfig(**config)
                self.add_connection(validated_config)
            except ValidationError as e:
                raise ValueError(f'⚠️ Configuração inválida: {e}') from e

    def add_connection(self, config: DatabaseConfig):
        """
        ➕ **Adiciona uma nova conexão**

        🛠️ **Parâmetros:**  
        - `config` (DatabaseConfig): Configuração validada do banco de dados.  

        ⚠️ **Possíveis exceções:**  
        - `ImportError`: Se o driver necessário não estiver instalado.  
        - `ValueError`: Se o nome da conexão já existir.  
        """
        if config.name in self.connections:
            raise ValueError(f"⚠️ A conexão '{config.name}' já existe! Escolha outro nome.")

        self._check_driver_installation(config.dialect)
        connection_url = self._build_connection_url(config)
        engine = create_engine(connection_url)

        self.connections[config.name] = {
            'engine': engine,
            'session_factory': scoped_session(sessionmaker(bind=engine)),
        }
        self.configs.append(config)

    def get_session(self, name: str) -> Session:
        """🔄 **Obtém uma sessão ativa para consultas e transações.**"""
        if name not in self.connections:
            raise ValueError(f"⚠️ Conexão '{name}' não encontrada.")
        return self.connections[name]['session_factory']()

    def get_engine(self, name: str) -> Engine:
        """🛠️ **Obtém a engine SQLAlchemy de uma conexão específica.**"""
        if name not in self.connections:
            raise ValueError(f"⚠️ Conexão '{name}' não encontrada.")
        return self.connections[name]['engine']

    def close_all_connections(self):
        """❌ **Fecha todas as conexões abertas de forma segura.**"""
        for name in list(self.connections.keys()):
            self.connections[name]['engine'].dispose()
            self.connections[name]['session_factory'].close_all()
            self.connections[name]['session_factory'].remove()
            del self.connections[name]

    def _build_connection_url(self, config: DatabaseConfig) -> str:
        """🔗 **Constrói a URL de conexão SQLAlchemy.**"""
        return URL.create(
            drivername=config.dialect,
            username=config.username,
            password=config.password,
            host=config.host,
            port=config.port,
            database=config.database,
        )

    def _check_driver_installation(self, dialect: str):
        """
        🔍 **Verifica se os pacotes necessários para o dialeto estão instalados.**

        ⚠️ **Se um driver estiver ausente, sugere o comando de instalação.**
        """
        base_dialect = dialect.split('+')[0].lower()
        required = self.DIALECT_REQUIREMENTS.get(base_dialect, [])

        for package in required:
            if not util.find_spec(package):
                install_cmd = f'pip install datasolver[{base_dialect}]'
                raise ImportError(
                    f"⚠️ Driver necessário: {package}\n"
                    f"💡 Instale com: {install_cmd}\n"
                    f"🛠️ Dialeto usado: {dialect}"
                )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_all_connections()
