from sqlalchemy import Column, String, BigInteger, Boolean, DateTime
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Customer(Base):
    __tablename__ = 'customer'
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