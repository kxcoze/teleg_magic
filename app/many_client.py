import asyncio
import random
import json
import time
import csv
import logging
import logging.config
from datetime import datetime
from dataclasses import dataclass

import aiolog
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from telethon import TelegramClient

from config import load_config, Config, dict_config
from db.models import Customer, TgClient, Base

logging.config.dictConfig(dict_config)

config: Config = load_config()
engine = create_async_engine(
    f'postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}/{config.db.db_name}',
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
    future=True,
)

async_session = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

@dataclass
class PeerId:
    user_id: int

@dataclass
class MockStatus:
    id: int
    out: bool
    date: datetime
    peer_id: PeerId
            
async def preparing_to_spam(client, name):
    logging.warning(f'STARTED as {name}')
    async with client:
        await spam_one_client(client, name)
    logging.warning(f'{name}: has just ended his job.')

async def spam_one_client(client, name):
    client.flood_sleep_threshold = 60 * 3
    message_to_sent = f"hello from {name}."
    count = 1
    async with async_session() as session:
        q = await session.execute(select(Customer).where(Customer.received==False))
        u = q.first()
        if not u is None:
            u = u[-1]
        while u:
            try:
                user = u.username or u.phone_number
                status = await client.send_message(user, message_to_sent)
                # status = MockStatus(
                #     id=random.randint(500000, 1000000),
                #     out=random.choice([True, False]),
                #     date=datetime.now(),
                #     peer_id=PeerId(user_id=random.randint(123456789, 987654321))
                # )
                u.message_id = status.id
                u.received = status.out
                # u.received_timestamp = datetime_from_utc_to_local(status.date).strftime("%d/%m/%Y, %H:%M:%S")
                u.received_timestamp = datetime.now()
                u.id_user = status.peer_id.user_id
                logging.warning(f'{name}: {count}) Sent message to <{u.username}>.')
                count += 1
                await session.merge(u)
                await session.commit()
                logging.warning(f'{name}: Sleeping for {config.sleep_time} sec. Zzz..')
                await asyncio.sleep(config.sleep_time)
            except Exception as e:
                u.message_id = None
                u.received = False
                u.received_timestamp = None
                u.id_user = None
                logging.error(
                        f"Cannot sent message to <{u.username}>.")
                logging.error(f'Also this error is occured. {e}\n')
                await session.merge(u)
                await session.commit()
                break
            q = await session.execute(select(Customer).where(Customer.received==False))
            u = q.first()
            if not u is None:
                u = u[-1]
    await asyncio.sleep(5)

async def main():
    async with engine.begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
            )    
    aiolog.start()
    # Get clients from db
    # clients = [TelegramClient('1', config.api.id, config.api.hash), TelegramClient('2', config.api.id, config.api.hash)]
    async with async_session() as session:
        q = await session.execute(select(TgClient))
        clients = [
            (client.session,
            TelegramClient(
                f'sessions/{client.session}', 
                api_id=client.api_id, 
                api_hash=client.api_hash,
                proxy={
                    'proxy_type': client.proxy_type,
                    'addr': client.proxy_addr,
                    'port': client.proxy_port,
                    'username': client.proxy_username,
                    'password': client.proxy_password,
                    'rdns': client.proxy_rdns,
                }
            )) for client in q.scalars() ]
    logging.info(f'Succesfully found {len(clients)} in db.')
    background_tasks = set()
    for session_name, client in clients:
        task = asyncio.create_task(preparing_to_spam(client, f'Client <{session_name}>'))
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
        await asyncio.sleep(10)
    await asyncio.gather(*background_tasks)
    logging.error('Sending has been successfully ended.')
    asyncio.ensure_future(aiolog.stop(), loop=asyncio.get_event_loop())



if __name__ == '__main__':
    asyncio.run(main())