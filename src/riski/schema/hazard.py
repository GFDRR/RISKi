from sqlalchemy import (Column, String, Integer, Date, Enum, Float, Boolean,
                        DateTime, Interval, String, Text, ForeignKey, VARCHAR)

from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from .base import Base, LiberalBoolean

from .common import ComponentEnum


# Schema Tables
class EventSet(Base):
    __tablename__ = 'event_set'
    __table_args__ = ({"schema": "hazard"})

    id = Column('id', Integer, primary_key=True)

    the_geom = Column(Geometry('POLYGON'), nullable=False)
    geographic_area_name = Column(String, nullable=False)
    creation_date = Column(Date, nullable=False)
    hazard_type = Column(String, nullable=False)
    time_start = Column(DateTime)
    time_end = Column(DateTime)
    time_duration = Column(Interval)
    description = Column(Text)
    bibliography = Column(Text)  # to be moved to contribution table
    is_prob = Column(LiberalBoolean, nullable=False)

    children = relationship("Event")


class Event(Base):
    __tablename__ = 'event'
    __table_args__ = ({"schema": "hazard"})

    id = Column('id', Integer, primary_key=True)
    event_set_id = Column(Integer, ForeignKey('hazard.event_set.id'))

    calculation_method = Column(Enum("INF", "SIM", "OBS", 
                                     name="calc_method_enum", 
                                     create_type=True),
                                nullable=False)
    frequency = Column(Float)
    occurence_probability = Column(Float)
    occurrence_time_start = Column(DateTime(timezone=False))
    occurrence_time_end = Column(DateTime(timezone=False))
    occurrence_time_span = Column(Interval)
    trigger_hazard_type = Column(VARCHAR, ForeignKey("common.hazard_type.code"))
    trigger_process_type = Column(VARCHAR, ForeignKey("common.process_type.code"))
    trigger_event_id = Column(Integer)
    description = Column(Text)

    children = relationship("FootprintSet")


class FootprintSet(Base):
    __tablename__ = 'footprint_set'
    __table_args__ = ({"schema": "hazard"})

    id = Column('id', Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('hazard.event.id'))

    process_type = Column(VARCHAR, nullable=False)
    imt = Column(VARCHAR, ForeignKey('common.imt.im_code'))
    data_uncertainty = Column(VARCHAR)

    children = relationship("Footprint")


class Footprint(Base):
    __tablename__ = 'footprint'
    __table_args__ = ({"schema": "hazard"})

    id = Column('id', Integer, primary_key=True)
    footprint_set_id = Column(Integer, ForeignKey('hazard.footprint_set.id'))
    uncertainty_2nd_moment = Column(Float)
    trigger_footprint_id = Column(Integer)

    children = relationship("FootprintData")


class FootprintData(Base):
    __tablename__ = 'footprint_data'
    __table_args__ = ({"schema": "hazard"})

    id = Column('id', Integer, primary_key=True)
    footprint_id = Column(Integer, ForeignKey('hazard.footprint.id'))
    file_location = Column(VARCHAR, nullable=False)
