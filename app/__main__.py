import asyncio
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
from db.models import Customer, Base

logging.config.dictConfig(dict_config)

config: Config = load_config()
engine = create_async_engine(
    f'postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}/{config.db.db_name}',
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
    future=True,
)

async_session = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

client = TelegramClient('some_user', config.api.id, config.api.hash)

def datetime_from_utc_to_local(utc_datetime):
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset
    
async def get_data_from_csv(filename):
    fieldnames = [
        'Имя пользователя',
        'Имя',
        'Фамилия',
        'Номер телефона',
        'Отправлено',
    ]
    new_fieldnames = fieldnames + [
        'ID сообщения',
        'Время отправки',
        'ID пользователя',
    ]
    with open(filename, newline='') as csvfile:    
        reader = csv.DictReader(csvfile, fieldnames=new_fieldnames)
        next(reader)
        async with async_session() as session:
            for u in reader:
                username = u['Имя пользователя']
                phone_number = u['Номер телефона']
                first_name = u['Имя'] or None
                last_name = u['Фамилия'] or None
                message_id = int(u['ID сообщения']) if u['ID сообщения'] else None
                received = str(u['Отправлено']).lower() in ['true', 't', '1', 'y']
                received_timestamp = datetime.strptime(u['Время отправки'], '%d/%m/%Y, %H:%M:%S') if u['Время отправки'] else None
                id_user = int(u['ID пользователя']) if u['ID пользователя'] else None
                try:
                    await session.merge(
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
                    await session.commit()
                    logging.info(f'Added to database <{username}>.')
                except Exception as e:
                    print(e)
                    logging.error(f'<{username or phone_number}> is already in database!')


@dataclass
class PeerId:
    user_id: int

@dataclass
class MockStatus:
    id: int
    out: bool
    date: datetime
    peer_id: PeerId
            

async def spam():
    logging.error('The notorious Spam is started!')
    async with engine.begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
            )    
    if input('Would you like to input customers in database? [N/y]: ', ).lower() in ['y', 'yes', 'ye', '+']:
        await get_data_from_csv(input('Input filename: '))
    client.flood_sleep_threshold = 60 * 3
    message_to_sent = "message_to_sent"
    count = 1
    async with async_session() as session:
        q = await session.execute(select(Customer).where(Customer.received==False))
        customers = q.scalars()
        for u in customers:
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
                logging.warning(f'{count}) Sent message to <{u.username}>.')
                count += 1
                await session.merge(u)
                await session.commit()
                logging.warning(f'Sleeping for {config.sleep_time} sec. Zzz..')
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
        else:
            logging.error('Sending has been successfully ended.')
    await asyncio.sleep(5)

async def main():
    aiolog.start()
    try:
        await spam()
    finally:
        asyncio.ensure_future(aiolog.stop(), loop=asyncio.get_event_loop())


if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())