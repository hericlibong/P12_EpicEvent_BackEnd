from sqlalchemy import Column, Integer, ForeignKey, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class Contract(Base):
    __tablename__ = 'contracts'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    sales_contact_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(Boolean, default=False)
    amount = Column(Float, nullable=False)
    payment_due = Column(DateTime, nullable=False)
    date_created = Column(DateTime, default=datetime.now)
    date_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relations
    client = relationship('Client', back_populates='contracts')
    sales_contact = relationship('User', back_populates='contracts')
    evnts = relationship('Event', back_populates='contract', cascade='all, delete-orphan')
