from database import Base, engine
from sqlalchemy import text, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False)
    email = Column(String(250), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=text("now()"))
    links = relationship("Link", back_populates="owner")


class Link(Base):
    __tablename__ = "links"
    id = Column(Integer, primary_key=True)
    short_code = Column(String(10), unique=True, nullable=False, index=True)
    long_url = Column(String(2024), nullable=False)
    created_at = Column(DateTime, server_default=text("now()"))
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )  # <-- allowing unregistered users to have links left when they are unregistered
    owner = relationship("User", back_populates="links")
    clicks = relationship("Click", back_populates="link", cascade="all, delete-orphan")


class Click(Base):
    __tablename__ = "clicks"
    id = Column(Integer, primary_key=True)
    # we have to delete clicks for a link if deleted
    link_id = Column(
        Integer, ForeignKey("links.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, server_default=text("now()"))
    ip_hash = Column(String(100))
    referrer = Column(String(250))
    link = relationship("Link", back_populates="clicks")
