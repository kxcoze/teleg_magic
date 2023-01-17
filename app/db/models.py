from sqlalchemy import Column, String, BigInteger, Boolean, DateTime, Integer
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Customer(Base):
    __tablename__ = "customer"
    username = Column(String(32), primary_key=True)
    phone_number = Column(String(32), primary_key=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    received = Column(Boolean, default=False)
    message_id = Column(BigInteger, nullable=True)
    id_user = Column(BigInteger, nullable=True)
    received_timestamp = Column(DateTime, nullable=True)

    def __str__(self):
        return self.username or self.phone_number

    def __repr__(self):
        return f"Customer <{self.__str__()}>"


class TgClient(Base):
    __tablename__ = "tgclient"
    session = Column(String(32), primary_key=True)
    api_id = Column(Integer)
    api_hash = Column(String(64))
    has_proxy = Column(Boolean)
    proxy_type = Column(String(10))
    proxy_addr = Column(String(16))
    proxy_port = Column(Integer)
    proxy_username = Column(String(64))
    proxy_password = Column(String(64))
    proxy_rdns = Column(Boolean)
