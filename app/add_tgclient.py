from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import click

from config import load_config, Config
from db.models import TgClient, Base

config: Config = load_config()

engine = create_engine(f'postgresql+psycopg2://{config.db.user}:{config.db.password}@{config.db.host}/{config.db.db_name}')
Session = sessionmaker(engine)

@click.command()
@click.option('--session_name', prompt='Session name', help='session name for tg client')
@click.option('--api_id', prompt='API Id', help='api_id for tg client')
@click.option('--api_hash', prompt='API Hash', help='api hash for tg client')
@click.option('--proxy', prompt='Has Proxy?', default='Y', help='does tg client has proxy?')
def create_tgclient(session_name, api_id, api_hash, proxy):
    # Creating database tables
    Base.metadata.create_all(engine)

    proxy_type = ''
    proxy_addr = ''
    proxy_port = ''
    proxy_username = ''
    proxy_password = ''
    proxy_rdns = ''
    if proxy.lower().strip() not in {'no', 'n'}:
        proxy_type = click.prompt('Proxy Type')
        proxy_addr = click.prompt('Proxy Address')
        proxy_port = click.prompt('Proxy Port')
        proxy_username = click.prompt('Proxy Username')
        proxy_password = click.prompt('Proxy Password')
        proxy_rdns = bool(click.prompt('Proxy RDNS'))
    with Session() as session:
        session.merge(
            TgClient(
                session=session_name,
                api_id=api_id,
                api_hash=api_hash,
                proxy_type=proxy_type,
                proxy_addr=proxy_addr,
                proxy_port=proxy_port,
                proxy_username=proxy_username,
                proxy_password=proxy_password,
                proxy_rdns=proxy_rdns,
            )
        )
        session.commit()

if __name__ == '__main__':
    create_tgclient()