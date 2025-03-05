"""
Módulo para gerenciar as Conexões

Gerencie as conexões com múltiplos bancos de dados.
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
    Configuração para Conexão com Banco de Dados

    Crie configurações para conectar-se a diferentes bancos de dados.:

    Args:
        name: Um nome único para sua conexão (ex: 'meu_banco_heroi')
        dialect: Dialeto SQLAlchemy + driver (ex: 'mysql+pymysql', 'postgresql+psycopg2')
        database: Nome do banco de dados
        username: Seu usuário (não necessário para SQLite)
        password: Senha (não necessário para SQLite)
        host: Endereço do servidor (não necessário para SQLite)
        port: Porta de acesso (1-65535, não necessário para SQLite)
        pool_size: Quantidade de conexões simultâneas (padrão: 5)
        max_overflow: Conexões extras para momentos de pico (padrão: 10)

    Exemplos de Dialetos:
        - 🐘 PostgreSQL: postgresql+psycopg2
        - 🐬 MySQL: mysql+pymysql
        - 🏺 Oracle: oracle+cx_oracle
        - 🏰 SQL Server: mssql+pyodbc
        - 🧪 SQLite: sqlite (não precisa de driver)

    Para cada dialeto deve ser feita a instalação do driver correspondente. Disponibilizamos grupos de dependências para facilitar a instalação:
    
    ```bash
    pip install datasolver[postgresql]
    pip install datasolver[mysql]
    pip install datasolver[oracle]
    pip install datasolver[mssql]
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
    Gerenciador de Conexões - Gerencia múltiplos bancos de dados.

    Args:
        connections: Dicionário de conexões ativas
        configs: Lista de configurações validadas

    Exemplo:

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
        Inicia a classe, com as conexões fornecidas

        Args:
            configs: Lista de configurações de conexão

        Raises:
            ValueError: Se alguma configuração estiver incorreta
            ImportError: Se faltar algum driver necessário

        Dica: Instale grupos de dependências com pip install datasolver[dialeto]
        """
        self.connections: Dict[str, Dict] = {}
        self.configs: List[DatabaseConfig] = []

        for config in configs:
            try:
                validated_config = DatabaseConfig(**config)
                self.add_connection(validated_config)
            except ValidationError as e:
                raise ValueError(f'Configuração inválida: {e}') from e

    def add_connection(self, config: DatabaseConfig):
        """
        Adiciona uma nova conexão

        Args:
            config: Configuração validada do banco de dados

        Raises:
            ImportError: Se o driver necessário não estiver instalado
            ValueError: Se o nome da conexão já existir
        """
        if config.name in self.connections:
            raise ValueError(
                f"A conexão '{config.name}' já existe! Escolha outro nome"
            )

        self._check_driver_installation(config.dialect)
        connection_url = self._build_connection_url(config)
        engine = create_engine(connection_url)

        self.connections[config.name] = {
            'engine': engine,
            'session_factory': scoped_session(sessionmaker(bind=engine)),
        }
        self.configs.append(config)

    def get_session(self, name: str) -> Session:
        """Retorna uma sessão ativa para consultas e transações."""
        if name not in self.connections:
            raise ValueError(f"Conexão '{name}' não encontrada")
        return self.connections[name]['session_factory']()

    def get_engine(self, name: str) -> Engine:
        """Retorna a engine SQLAlchemy de uma conexão específica."""
        if name not in self.connections:
            raise ValueError(f"Conexão '{name}' não encontrada")
        return self.connections[name]['engine']

    def close_all_connections(self):
        """Fecha todas as conexões abertas."""
        for name in list(self.connections.keys()):
            self.connections[name]['engine'].dispose()
            self.connections[name]['session_factory'].close_all()
            self.connections[name]['session_factory'].remove()
            del self.connections[name]

    def _build_connection_url(self, config: DatabaseConfig) -> str:
        """Constrói a URL de conexão SQLAlchemy."""
        return URL.create(
            drivername=config.dialect,
            username=config.username,
            password=config.password,
            host=config.host,
            port=config.port,
            database=config.database,
        )

    def _check_driver_installation(self, dialect: str):
        """Verifica se os pacotes necessários estão instalados."""
        base_dialect = dialect.split('+')[0].lower()
        required = self.DIALECT_REQUIREMENTS.get(base_dialect, [])

        for package in required:
            if not util.find_spec(package):
                install_cmd = f'pip install datasolver[{base_dialect}]'
                raise ImportError(
                    f'Driver necessário: {package}\n'
                    f'Fórmula de instalação: {install_cmd}\n'
                    f'Dialeto usado: {dialect}'
                )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_all_connections()