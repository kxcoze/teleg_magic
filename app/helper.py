import time
import datetime
import csv

import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import load_config, Config
from db.models import TgClient, Customer, Base

config: Config = load_config()

engine = create_engine(
    f"postgresql+psycopg2://{config.db.user}:{config.db.password}@{config.db.host}/{config.db.db_name}"
)
Session = sessionmaker(engine)


@click.group()
def cli():
    pass


@cli.command(name="initdb", help="create database tables.")
def initdb():
    Base.metadata.create_all(engine)
    click.echo("Database tables has been created.")


@cli.command(name="truncdb", help="truncate database.")
def truncatedb():
    Base.metadata.drop_all(engine)
    click.echo("Database tables has been dropped")


@cli.command(name="csvtodb", help="parse a csv file and insert found data into db.")
@click.option(
    "--filename", prompt="input .csv filename to read", help="CSV file from to read."
)
def get_data_from_csv(filename):
    def datetime_from_utc_to_local(utc_datetime):
        now_timestamp = time.time()
        offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(
            now_timestamp
        )
        return utc_datetime + offset

    fieldnames = [
        "Имя пользователя",
        "Имя",
        "Фамилия",
        "Номер телефона",
        "Отправлено",
    ]
    new_fieldnames = fieldnames + [
        "ID сообщения",
        "Время отправки",
        "ID пользователя",
    ]
    with open(filename, newline="") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=new_fieldnames)
        next(reader)
        with Session() as session:
            for u in reader:
                username = u["Имя пользователя"]
                phone_number = u["Номер телефона"]
                first_name = u["Имя"] or None
                last_name = u["Фамилия"] or None
                message_id = int(u["ID сообщения"]) if u["ID сообщения"] else None
                received = str(u["Отправлено"]).lower() in ["true", "t", "1", "y"]
                received_timestamp = (
                    datetime.strptime(u["Время отправки"], "%d/%m/%Y, %H:%M:%S")
                    if u["Время отправки"]
                    else None
                )
                id_user = int(u["ID пользователя"]) if u["ID пользователя"] else None
                try:
                    session.merge(
                        Customer(
                            username=username,
                            phone_number=phone_number,
                            first_name=first_name,
                            last_name=last_name,
                            message_id=message_id,
                            received=received,
                            received_timestamp=received_timestamp,
                            id_user=id_user,
                        )
                    )
                    session.commit()
                    click.echo(f"Added to database <{username}>.")
                except Exception as e:
                    click.echo(e)
                    click.echo(f"<{username or phone_number}> is already in database!")


@cli.command(
    name="tgclient", help="give credentials for a telegram client and insert add db."
)
@click.option(
    "--session_name", prompt="Session name", help="session name for tg client"
)
@click.option("--api_id", prompt="API Id", help="api_id for tg client")
@click.option("--api_hash", prompt="API Hash", help="api hash for tg client")
@click.option(
    "--proxy", prompt="Has Proxy?", default="Y", help="does tg client has proxy?"
)
def create_tgclient(session_name, api_id, api_hash, proxy):
    proxy_type = None
    proxy_addr = None
    proxy_port = None
    proxy_username = None
    proxy_password = None
    proxy_rdns = None
    proxy = proxy.lower().strip() not in {"no", "n"}
    if proxy:
        proxy_type = click.prompt("Proxy Type")
        proxy_addr = click.prompt("Proxy Address")
        proxy_port = click.prompt("Proxy Port")
        proxy_username = click.prompt("Proxy Username")
        proxy_password = click.prompt("Proxy Password")
        proxy_rdns = bool(click.prompt("Proxy RDNS"))
    with Session() as session:
        session.merge(
            TgClient(
                session=session_name,
                api_id=api_id,
                api_hash=api_hash,
                has_proxy=proxy,
                proxy_type=proxy_type,
                proxy_addr=proxy_addr,
                proxy_port=proxy_port,
                proxy_username=proxy_username,
                proxy_password=proxy_password,
                proxy_rdns=proxy_rdns,
            )
        )
        session.commit()


if __name__ == "__main__":
    cli()
