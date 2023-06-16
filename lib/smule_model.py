# coding: utf-8
from sqlalchemy import Boolean, Column, Date, DateTime, Integer, Numeric, String, Table, text
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, server_default=text("NULL"))
    sid = Column(String(255), nullable=False, server_default=text("NULL"))
    comments = Column(String(1024), server_default=text("NULL"))
    updated_at = Column(Date, server_default=text("NULL"))


class Love(Base):
    __tablename__ = 'loves'

    sid = Column(String(255), primary_key=True, nullable=False)
    user = Column(String(255), primary_key=True, nullable=False)
    updated_at = Column(Date)


class Performance(Base):
    __tablename__ = 'performances'

    id = Column(Integer, primary_key=True, server_default=text("'=0'"))
    sid = Column(String(255), nullable=False, server_default=text("NULL"))
    title = Column(String(255), server_default=text("NULL"))
    stitle = Column(String(255), index=True, server_default=text("NULL"))
    avatar = Column(String(255), server_default=text("NULL"))
    href = Column(String(255), server_default=text("NULL"))
    record_by = Column(String(255), index=True, server_default=text("NULL"))
    isfav = Column(Numeric, server_default=text("NULL"))
    oldfav = Column(Numeric, server_default=text("NULL"))
    orig_city = Column(String(255), server_default=text("NULL"))
    listens = Column(Integer, server_default=text("'=0'"))
    loves = Column(Integer, server_default=text("'=0'"))
    gifts = Column(Integer, server_default=text("'=0'"))
    psecs = Column(Integer, server_default=text("'=0'"))
    stars = Column(Integer, server_default=text("'=0'"))
    created = Column(DateTime, server_default=text("NULL"))
    updated_at = Column(DateTime, server_default=text("NULL"))
    song_info_url = Column(String(255), index=True, server_default=text("NULL"))
    other_city = Column(String(255), server_default=text("NULL"))
    message = Column(String(255))
    deleted = Column(Boolean)
    expire_at = Column(DateTime)
    latlong = Column(String(255))
    latlong_2 = Column(String(255))
    record_by_ids = Column(String(255))
    parent_sid = Column(String(255), index=True)
    perf_tags = Column(String(255))
    song_info_id = Column(Integer)


t_schema_info = Table(
    'schema_info', metadata,
    Column('version', Integer, nullable=False, server_default=text("0"))
)


class Singer(Base):
    __tablename__ = 'singers'

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer)
    name = Column(String(255), nullable=False)
    avatar = Column(String(255))
    following = Column(String(255))
    follower = Column(String(255))
    alias = Column(String(255))
    updated_at = Column(Date)


class SongInfo(Base):
    __tablename__ = 'song_infos'

    id = Column(Integer, primary_key=True)
    song_info_url = Column(String(255))
    stitle = Column(String(255))
    author = Column(String(255))
    singer = Column(String(255))
    tags = Column(String(255))
    updated_at = Column(Date)


t_sqlite_sequence = Table(
    'sqlite_sequence', metadata,
    Column('name', NullType),
    Column('seq', NullType)
)
