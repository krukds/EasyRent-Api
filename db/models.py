from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, DECIMAL, UniqueConstraint, \
    CheckConstraint, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserModel(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    patronymic = Column(String, nullable=True)
    birth_date = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    photo_url = Column(String)
    role = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    passport_path = Column(String)


class SessionModel(Base):
    __tablename__ = "session"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    access_token = Column(String, nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class ListingTypeModel(Base):
    __tablename__ = "listing_type"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


class HeatingTypeModel(Base):
    __tablename__ = "heating_type"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


class ListingStatusModel(Base):
    __tablename__ = "listing_status"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


class ListingModel(Base):
    __tablename__ = "listing"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Integer, nullable=False)
    city_id = Column(Integer, ForeignKey("city.id", ondelete="SET NULL"), nullable=True)
    street_id = Column(Integer, ForeignKey("street.id", ondelete="SET NULL"), nullable=True)
    building = Column(String, nullable=False)
    flat = Column(Integer)
    floor = Column(Integer, nullable=False)
    all_floors = Column(Integer, nullable=False)
    rooms = Column(Integer, nullable=False)
    bathrooms = Column(Integer)
    square = Column(Integer, nullable=False)
    communal = Column(Integer, nullable=False)
    owner_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    heating_type_id = Column(Integer, ForeignKey("heating_type.id", ondelete="SET NULL"))
    listing_type_id = Column(Integer, ForeignKey("listing_type.id", ondelete="SET NULL"))
    listing_status_id = Column(Integer, ForeignKey("listing_status.id", ondelete="SET NULL"))
    discard_reason = Column(String)
    document_ownership_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("UserModel", backref="listings", foreign_keys=[owner_id])
    heating_type = relationship("HeatingTypeModel")
    listing_type = relationship("ListingTypeModel")
    listing_status = relationship("ListingStatusModel")
    images = relationship("ImageModel", back_populates="listing", cascade="all, delete")
    tags = relationship("ListingTagModel", secondary="listing_tag_listing", backref="listings")
    city = relationship("CityModel", back_populates="listings")
    street = relationship("StreetModel", back_populates="listings")



class ImageModel(Base):
    __tablename__ = "image"
    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("listing.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String, nullable=False)

    listing = relationship("ListingModel", back_populates="images")


class ReviewStatusModel(Base):
    __tablename__ = "review_status"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


class ReviewModel(Base):
    __tablename__ = "review"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    owner_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    rating = Column(DECIMAL(2, 1), CheckConstraint("rating BETWEEN 0.0 AND 5.0"), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    review_status_id = Column(Integer, ForeignKey("review_status.id", ondelete="SET NULL"))

    review_status = relationship("ReviewStatusModel", backref="reviews")
    tags = relationship("ReviewTagModel", secondary="review_tag_review", backref="reviews")
    owner = relationship("UserModel", foreign_keys=[owner_id], backref="reviews_about_me")
    user = relationship("UserModel", foreign_keys=[user_id], backref="my_written_reviews")

    __table_args__ = (UniqueConstraint('user_id', 'owner_id', name='uq_user_owner_review'),)


class ReviewTagModel(Base):
    __tablename__ = "review_tag"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


class ReviewTagReviewModel(Base):
    __tablename__ = "review_tag_review"
    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey("review.id", ondelete="CASCADE"), nullable=False)
    review_tag_id = Column(Integer, ForeignKey("review_tag.id", ondelete="CASCADE"))


class FavoritesModel(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    listing_id = Column(Integer, ForeignKey("listing.id", ondelete="CASCADE"), nullable=False)


class ListingTagCategoryModel(Base):
    __tablename__ = "listing_tag_category"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


class ListingTagModel(Base):
    __tablename__ = "listing_tag"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    listing_tag_category_id = Column(Integer, ForeignKey("listing_tag_category.id", ondelete="CASCADE"), nullable=False)

    category = relationship("ListingTagCategoryModel", backref="tags")


class ListingTagListingModel(Base):
    __tablename__ = "listing_tag_listing"
    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("listing.id", ondelete="CASCADE"), nullable=False)
    listing_tag_id = Column(Integer, ForeignKey("listing_tag.id", ondelete="CASCADE"), nullable=False)


class CityModel(Base):
    __tablename__ = "city"
    id = Column(Integer, primary_key=True)
    name_ukr = Column(String, nullable=False)
    name_eng = Column(String)
    region = Column(String)
    oblast = Column(String)
    oblast_eng = Column(String)

    streets = relationship("StreetModel", back_populates="city")
    listings = relationship("ListingModel", back_populates="city")


class StreetModel(Base):
    __tablename__ = "street"
    id = Column(Integer, primary_key=True)
    name_ukr = Column(String, nullable=False)
    name_eng = Column(String)
    city_id = Column(Integer, ForeignKey("city.id", ondelete="CASCADE"), nullable=False)

    city = relationship("CityModel", back_populates="streets")
    listings = relationship("ListingModel", back_populates="street")
