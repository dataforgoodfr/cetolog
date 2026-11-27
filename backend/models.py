from sqlalchemy import Column, Date, ForeignKey, Integer, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Individual(Base):
    __tablename__ = "individuals"

    id = Column(Integer, primary_key=True)
    code = Column(Text, unique=True)  # TUTR0025


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True)
    delivery = Column(Text)  # livraison : catalogue_20261029_miraceti
    original_filename = Column(Text)  # fichier_origine
    individual_id = Column(Integer, ForeignKey("individuals.id"))  # individu
    side = Column(Text)  # cote : D ou G
    date = Column(Date)  # date nom_fichier OU date exif
    site = Column(Text)
    sha256 = Column(Text)
