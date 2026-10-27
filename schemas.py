import re
from datetime import date,datetime,timezone
from pydantic import BaseModel,Field,field_validator,model_validator
from .countries import COUNTRY_CODES
class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=24)
    password: str = Field(min_length=8, max_length=128)

class Signup(Credentials):
    email: str = Field(max_length=254)
    birth_date: date
    country: str

    @field_validator('email')
    @classmethod
    def validate_gmail(cls,value):
        value=value.strip().lower()
        if not re.fullmatch(r'[a-z0-9][a-z0-9.+]*@gmail\.com',value):raise ValueError('Enter a valid Gmail address ending in @gmail.com.')
        if '..' in value.split('@')[0] or value.split('@')[0].endswith('.'):raise ValueError('Enter a valid Gmail address.')
        return value

    @field_validator('birth_date')
    @classmethod
    def validate_birth_date(cls,value):
        if value>date.today() or value<date(1900,1,1):raise ValueError('Enter a birth date between 1900 and today.')
        return value

    @field_validator('country')
    @classmethod
    def validate_country(cls, value):
        value = value.strip().upper()
        if value not in COUNTRY_CODES:
            raise ValueError('Choose a valid country.')
        return value

class Profile(BaseModel):
    display_name: str = Field(min_length=1,max_length=60)
    bio: str = Field(default='', max_length=280)
    country: str | None = None

    @field_validator('country')
    @classmethod
    def validate_country(cls, value):
        if value is None or not value.strip():
            return None
        value = value.strip().upper()
        if value not in COUNTRY_CODES:
            raise ValueError('Choose a valid country.')
        return value

class Movie(BaseModel):
    id: int = Field(gt=0)
    title: str = Field(min_length=1,max_length=300)
    poster_path: str | None = Field(default=None,max_length=200)
    release_date: str = Field(default='',max_length=20)
    overview: str = Field(default='',max_length=5000)
    vote_average: float = Field(default=0,ge=0,le=10)

class Entry(BaseModel):
    movie: Movie
    rating: float | None = Field(default=None, ge=0.5, le=5, multiple_of=0.5)
    review: str = Field(default='', max_length=5000)
    watched_on: date
    spoilers: bool = False
    is_public: bool = True
    remove_from_watchlist: bool = False

    @model_validator(mode='after')
    def validate_date(self):
        # A calendar day may already have begun in the user's time zone.
        from datetime import timedelta
        if self.watched_on > datetime.now(timezone(timedelta(hours=14))).date():
            raise ValueError('Watched date cannot be in the future.')
        self.review = self.review.strip()
        return self

class PasswordChange(BaseModel):
    current_password:str=Field(min_length=1,max_length=128)
    new_password:str=Field(min_length=8,max_length=128)

class RecoveryEmail(BaseModel):
    current_password:str=Field(min_length=1,max_length=128)
    email:str=Field(max_length=254)
    @field_validator('email')
    @classmethod
    def email_valid(cls,value):
        value=value.strip().lower()
        if not re.fullmatch(r'[^\s@<>\r\n]+@[^\s@<>\r\n]+\.[^\s@<>\r\n]+',value):
            raise ValueError('Enter a valid email address.')
        return value

class ResetRequest(BaseModel):
    email:str=Field(min_length=3,max_length=254)

class ResetPassword(BaseModel):
    token:str=Field(min_length=32,max_length=200)
    new_password:str=Field(min_length=8,max_length=128)

class DeleteAccount(BaseModel):
    current_password:str=Field(min_length=1,max_length=128)
    confirmation:str=Field(max_length=24)

class ListData(BaseModel):
    name:str=Field(min_length=1,max_length=100)
    description:str=Field(default='',max_length=1000)
    is_public:bool=False

class MoveMovie(BaseModel):
    direction:str=Field(pattern='^(up|down)$')

class CommentData(BaseModel):
    body:str=Field(min_length=1,max_length=2000)
    spoilers:bool=False

class Preferences(BaseModel):
    hide_spoilers:bool=True

class ProfileDetails(BaseModel):
    genres:str=Field(default='',max_length=200)
    show_favorites:bool=True
    show_stats:bool=False
    show_activity:bool=True
    pinned_review:int|None=Field(default=None,gt=0)
    pinned_list:int|None=Field(default=None,gt=0)

class Favorites(BaseModel):
    movies:list[Movie|None]=Field(max_length=5)

class ImageData(BaseModel):
    data:str=Field(max_length=2800000)

class Report(BaseModel):reason:str=Field(min_length=10,max_length=2000)

class Verify(BaseModel):token:str=Field(min_length=32,max_length=200)
