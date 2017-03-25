from __future__ import absolute_import
from __future__ import unicode_literals

import datetime

from sqlalchemy import (Boolean, BigInteger, Column, DateTime, ForeignKey, Index, Integer,
                        Numeric, String, Table)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from ..extensions.database import Base


class TimestampMixin():
    date_added = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Ebook(Base, TimestampMixin):
    __tablename__ = 'ebooks'

    id = Column(String(32), primary_key=True)
    title = Column(String(500))
    author = Column(String(500))

    rating = Column(Integer)
    publisher = Column(String(500))
    publish_date = Column(DateTime)
    is_non_fiction = Column(Boolean)
    is_curated = Column(Boolean)

    isbn = Column(String(13), index=True)
    isbn13 = Column(String(13), index=True)
    asin = Column(String(10), index=True)
    uri = Column(String(500))
    num_pages = Column(Integer)
    average_rating = Column(Numeric(12, 2))

    raw_tags = Column(String(500))

    source_provider = Column(String(50))
    source_title = Column(String(500))
    source_author = Column(String(500))

    provider_metadata = Column(JSONB)

    versions = relationship(
        'Version',
        foreign_keys='[Version.ebook_id]',
        back_populates='ebook'
    )

    original_version_id = Column(
        UUID,
        ForeignKey('versions.id', ondelete='SET NULL')
    )
    original_version = relationship('Version', foreign_keys=[original_version_id])

    def __repr__(self):
        return '<Ebook>{}:{} - {}'.format(self.id, self.author, self.title)

    def __json__(self):
        return {
            'ebook_id': self.id,
            'title': self.title,
            'author': self.author,
            'rating': self.rating,
            'publisher': self.publisher,
            'publish_date': self.publish_date,
            'is_non_fiction': self.is_non_fiction,
            'is_curated': self.is_curated,
            'isbn': self.isbn,
            'isbn13': self.isbn13,
            'asin': self.asin,
            'uri': self.uri,
            'num_pages': self.num_pages,
            'average_rating': self.average_rating,
            'versions': [v.id for v in self.versions],
            'original_version_id': self.original_version_id,
        }


class Version(Base, TimestampMixin):
    __tablename__ = 'versions'

    id = Column(UUID, primary_key=True)

    ebook_id = Column(String(32), ForeignKey('ebooks.id'))
    ebook = relationship('Ebook', foreign_keys=[ebook_id], back_populates='versions')

    uploader_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    uploader = relationship('User')

    size = Column(Integer)
    popularity = Column(Numeric(12, 2))
    quality = Column(Numeric(12, 2))
    ranking = Column(Numeric(12, 2))
    publish_date = Column(DateTime, default=datetime.datetime.utcnow)
    original_file_hash = Column(String(32), index=True)

    formats = relationship(
        'Format',
        foreign_keys='[Format.version_id]',
        back_populates='version'
    )

    source_format_id = Column(
        String(32),
        ForeignKey('formats.file_hash', onupdate='CASCADE', ondelete='SET NULL'),
        index=True
    )
    source_format = relationship('Format', foreign_keys=[source_format_id])

    __mapper_args__ = {
        'order_by': ranking
    }

    def __repr__(self):
        return '<Version>{}'.format(self.id)

    def __json__(self):
        return {
            'version_id': self.id,
            'ebook_id': self.ebook_id,
            'uploader': self.uploader.username,
            'size': self.size,
            'popularity': self.popularity,
            'quality': self.quality,
            'ranking': self.ranking,
            'publish_date': self.publish_date.isoformat(),
            'original_file_hash': self.original_file_hash,
            'formats': {f.format: f.file_hash for f in self.formats},
            'source_format': self.source_format.format,
        }


# many-to-many owners of formats
formats_owners = Table('formats_owners', Base.metadata,
    Column(
        'file_hash',
        String(32),
        ForeignKey('formats.file_hash', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True
    ),
    Column(
        'user_id',
        Integer,
        ForeignKey('user.id'),
        primary_key=True
    )
)


class Format(Base, TimestampMixin):
    __tablename__ = 'formats'

    file_hash = Column(String(32), primary_key=True)

    version_id = Column(UUID, ForeignKey('versions.id'))
    version = relationship('Version', foreign_keys=[version_id], back_populates='formats')

    uploader_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    uploader = relationship('User')

    owners = relationship('User', secondary=formats_owners)

    format = Column(String(5))
    uploaded = Column(Boolean, default=False, index=True)
    ogreid_tagged = Column(Boolean, default=False)
    dedrm = Column(Boolean)
    s3_filename = Column(String(200))

    def __repr__(self):
        return '<Format>{}:{}'.format(self.file_hash, self.format)

    def __json__(self):
        return {
            'file_hash': self.file_hash,
            'version_id': self.version_id,
            'uploader': self.uploader.username,
            'owners': [u.username for u in self.owners],
            'format': self.format,
            'uploaded': self.uploaded,
            'ogreid_tagged': self.ogreid_tagged,
            'dedrm': self.dedrm,
            's3_filename': self.s3_filename,
        }


class SyncEvent(Base):
    __tablename__ = 'sync_events'

    event_id = Column(BigInteger, primary_key=True)

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    user = relationship('User')

    syncd_books_count = Column(Integer)
    new_books_count = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('user_syncd_books_count_ix', user_id, syncd_books_count),
    )
