from fastapi import FastAPI,HTTPException, Query, Path, Body, Depends
from sqlmodel import Field, Session, SQLModel, create_engine, select, and_
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from transformers import AutoTokenizer, BertForSequenceClassification
import torch

from typing import Annotated, Optional, Dict, List
import json
from sqlalchemy import Column, Text

import logging
logging.basicConfig(level=logging.INFO)

model_is_ready = False
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# Model load
try:
    tokenizer = AutoTokenizer.from_pretrained('monologg/kobert', trust_remote_code=True)
    model = BertForSequenceClassification.from_pretrained('jeonghyeon97/koBERT-Senti5').to(device)
    model_is_ready = True
except Exception as e:
    logging.error(f"Model loading failed: {e}")

#SQLite Dataset load
sqlite_file_name = 'movies.db'
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=False, connect_args=connect_args,)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Dependancy setting
def get_session():
    with Session(engine) as session:
        yield session

# DI
SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("SERVICE UP!")
    create_db_and_tables()
    yield
    logging.info("SERVICE DOWN!")

app = FastAPI(lifespan=lifespan)

# DB Table Declaration
class MoviesTable(SQLModel, table=True):
    '''Default Table Declaration'''
    __tablename__ = "movie_info"
    id: Optional[int] = Field(description='Unique ID Number', default=None, primary_key=True)
    title: str = Field(description='Title of Movie')
    director: str = Field(description='Name of Director')
    category: str = Field(description='Genre of movie')
    rating: Optional[float] = Field(default=None)
    image_url: Optional[str] = Field(default=None)
    review: Optional[str] = Field(default=None)

    sentiment_raw: Optional[str] = Field(default=None, sa_column=Column("sentiment", Text))

    @property
    def sentiment(self) -> Optional[Dict[str, float]]:
        if self.sentiment_raw:
            try:
                return json.loads(self.sentiment_raw)
            except json.JSONDecodeError:
                return None
        return None

    @sentiment.setter
    def sentiment(self, value: Optional[Dict[str, float]]):
        self.sentiment_raw = json.dumps(value) if value else None

# Response Body Declaration
class MovieResponse(BaseModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    director: str
    category: str
    rating: Optional[float] = None
    image_url: Optional[str] = None
    review: Optional[str] = None
    predicted_sentiment: Optional[Dict[str, float]] = None
    
    model_config = {
        'json_schema_extra': {
            'example': {
                'title': 'movie_title',
                'director': 'movie_director',
                'category': 'movie_genre',
                'rating': 4.5,
                'image_url': 'https://image.com/poster.jpg',
                'review': 'Great acting and story!',
                'predicted_sentiment': {'positive': 0.95, 'negative': 0.05}
            }
        }
    }

# Create movie class
class MovieCreate(BaseModel):
    title: str
    director: str
    category: str

# helper function
def check_duplicate(session: Session, title: str, director: str, exclude_id: Optional[int] = None):
    '''
    check if there are any matching movies in DB correspond to title and director of user input
    '''
    statement = select(MoviesTable).where(
        and_(
            MoviesTable.title == title,
            MoviesTable.director == director
        )
    )
    if exclude_id:
        statement = statement.where(MoviesTable.id != exclude_id)
    return session.exec(statement).first()

def reshaping_movie(movie: MoviesTable) -> MovieResponse:
    '''
    Response class expects to return predicted sentiment in one dictionary
    '''
    sentiment_dict = None
    if movie.sentiment:
        try:
            sentiment_dict = json.loads(movie.sentiment)
        except:
            sentiment_dict = None

    return MovieResponse(
        id=movie.id,
        title=movie.title,
        director=movie.director,
        category=movie.category,
        rating=movie.rating,
        image_url=movie.image_url,
        review=movie.review,
        predicted_sentiment=sentiment_dict
    )
# health check
@app.get("/health", tags=["Health"])
def health_check(session: SessionDep):
    '''
    Check all of the components for the backend has been loaded
    '''
    try:
        # DB 접근 테스트
        session.exec(select(MoviesTable).limit(1)).all()

        if model_is_ready:
            return {"status": "ok", "model": "ready", "db": "connected"}
        else:
            return JSONResponse(status_code=503, content={"status": "error", "model": "not ready", "db": "connected"})

    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return JSONResponse(status_code=503, content={"status": "error", "model": "unknown", "db": "disconnected"})

# Backend entry point
@app.get('/', description='Hello!', response_description='Welcome!')
async def root():
    '''
    Root endpoint of the Movie API.
    '''
    return {"messages": "HI! This website is for Movie search and estimate movie rates by reviews"}

# Get all the movie data from DB
@app.get('/movies', response_model=List[MovieResponse], description='List of Movies', response_description='All items in DB')
async def get_all_movies(session: SessionDep):
    '''
    Get a list of all movies in the DB.
    Args:
        session (SessionDep): SQLModel session dependency.
    Returns:
        List[MovieResponse]: List of all movies (if available).
    '''
    movies = session.exec(select(MoviesTable)).all()

    if not movies:
        raise HTTPException(status_code=404, detail='No movies found')

    return [reshaping_movie(movie) for movie in movies]

# Search from DB
@app.get('/movies/title/{movie_title}', response_model=MovieResponse, response_model_exclude=['id'])
async def get_title(session: SessionDep, movie_title: Annotated[str, Path(description="Input the movie title that you looking for!")]):
    '''
    take `movie_tile` as a input variable and return the correspond infos form DB
    Args:
        session (SessionDep): SQLModel session dependency.
        movie_title: user input, this variable will appended to the backend path.
    Returns:
        MovieResponse: movie which correspond to the user input (if available).
    '''
    if movie_title:
        statement = select(MoviesTable).where(MoviesTable.title == movie_title)
        movie = session.exec(statement).first()

        if not movie:
            raise HTTPException(status_code=404, detail='No movies found')
        
        return reshaping_movie(movie)

    raise HTTPException(status_code=404, detail=f"NO MATCHING MOVIE FOUND!: {movie_title}")
    

@app.get('/movies/director/{movie_director}', response_model=List[MovieResponse], response_model_exclude=['id'])
async def get_director(session: SessionDep, movie_director: Annotated[str, Path(description='Search Query')]):
    '''
    take `direcor` as a input variable and return the correspond infos form DB.
    Args:
        session (SessionDep): SQLModel session dependency.
        movie_director: user input, this variable will appended to the backend path.
    Returns:
        List[MovieResponse]: List of all movies (if available).
    '''
    if movie_director:
        statement = select(MoviesTable).where(MoviesTable.director == movie_director)
        movies = session.exec(statement).all()

        if not movies:
            raise HTTPException(status_code=404, detail='No movies found')
        
        return [reshaping_movie(movie) for movie in movies]
    
    raise HTTPException(status_code=404, detail=f'NO MATCHING DIRECTOR FOUND!: {movie_director}')

@app.get('/movies/search', response_model=List[MovieResponse], response_model_exclude=['id'])
async def get_mult_query(session: SessionDep,
                        title: Annotated[str, Query(description='title')],
                        director: Annotated[str, Query(description='title')],
                        category: Annotated[str, Query(description='title')]
                        ):
    '''
    Perform multi-conditional search on movie data. It searches exact match of user inputs
    Args:
        session (SessionDep): SQLModel session dependency.
        title, director, category: user inputs, these variables will formed into the backend query.
    Returns:
        List[MovieResponse]: List of all movies correspond to the user inputs (if available).
    '''
    conditions = []

    if title:
        conditions.append(MoviesTable.title == title)
    if director:
        conditions.append(MoviesTable.director == director)
    if category:
        conditions.append(MoviesTable.category == category)

    if not conditions:
        raise HTTPException(status_code=400, detail='At least one query parameter must be provided')

    
    statement = select(MoviesTable).where(and_(*conditions))

    movies = session.exec(statement).all()

    if not movies:
        raise HTTPException(status_code=404, detail='No matching movies found')

    return [reshaping_movie(movie) for movie in movies]

# Add new movie data to DB
@app.post('/movies', response_model=MovieResponse, status_code=201)
async def create_movie(session: SessionDep, new_movie: MovieCreate = Body(description='Movie information')):
    '''
    Add new movie info to DB
    Args:
        new_movie[MovieCreate]: initialize new movie
    Returns:
        wrap and parse the data with MovieResponse and return.
    '''
    if not new_movie.title or not new_movie.director or not new_movie.category:
        raise HTTPException(status_code=400, detail='Title, Director, and Category are required fields')
    
    # Check for duplicate title and director
    if check_duplicate(session, new_movie.title, new_movie.director):
        raise HTTPException(status_code=409, detail='Movie with the same title and director already exists')
    
    db_movie = MoviesTable(**new_movie.model_dump())
    session.add(db_movie)
    session.commit()
    session.refresh(db_movie)

    return MovieResponse(**db_movie.dict(), predicted_sentiment=None)

@app.put('/movies/{movie_id}', response_model=MovieResponse)
async def update_movie_by_id(session: SessionDep,
                       movie_id: Annotated[int, Path(description='ID of the movie to update')],
                       updated_movie: MovieResponse = Body(description='Updated movie information')
                       ):
    '''
    Update existing movie info in DB
    Args:
        movie_id: search keyword, the backend will search the movie by this variable
        updated_movie: user input, the informations that user wants to update for the movie corresponds to the ID
    Returns:
        MovieResponse: movies correspond to the user inputs (if available).
    '''
    movie = session.get(MoviesTable, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail=f'Movie with ID {movie_id} not found')

    # Check for duplicate title and director excluding current movie
    existing_movie = check_duplicate(session, updated_movie.title, updated_movie.director, exclude_id=movie_id)

    if existing_movie:
        raise HTTPException(status_code=409, detail='Another movie with the same title and director already exists')

    update_data = updated_movie.model_dump(exclude_unset=True)
    update_data.pop("predicted_sentiment", None)

    for key, value in update_data.items():
        setattr(movie, key, value)

    session.add(movie)
    session.commit()
    session.refresh(movie)

    return reshaping_movie(movie)

@app.delete('/movies/{movie_id}', status_code=204)
async def delete_movie_by_id(session: SessionDep, movie_id: Annotated[int, Path(description='ID of the movie to delete')]):
    '''
    Delete movie info from DB
    Args:
        movie_id: user input, search the ID that user wants, and delete
    '''
    movie = session.get(MoviesTable, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail=f'Movie with ID {movie_id} not found')

    session.delete(movie)
    session.commit()

    return {"messages": f"Movie with ID {movie_id} has been deleted"}

@app.post('/movies/{movie_id}/review', response_model=MovieResponse)
async def add_review(session: SessionDep, 
                     movie_id: Annotated[int, Path(description='ID of the movie to update')],
                     review_string: Annotated[str, Body(description='Movie review text for sentiment analysis')]
                     ):
    '''
    Add or update a review for a specific movie.

    Performs DB update only; sentiment analysis must be triggered separately.
    '''
    if not review_string:
        raise HTTPException(status_code=400, detail='Review text is required')
    
    # add review to DB
    movie = session.get(MoviesTable, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail=f'Movie with ID {movie_id} not found')
    movie.review = review_string

    session.add(movie)
    session.commit()
    session.refresh(movie)
    return reshaping_movie(movie)

@app.post('/movies/review_analyze', response_model=List[MovieResponse])
async def analyze_review(session: SessionDep):
    '''
    Analyze the sentiment of all movies with reviews.

    This endpoint uses KoBERT to compute sentiment scores and updates
    the sentiment field in the database.

    Returns:
        List[MovieResponse]: List of analyzed movies with predicted sentiment.
    '''
    movies = session.exec(select(MoviesTable).where(MoviesTable.review != None)).all()
    if not movies:
        raise HTTPException(status_code=404, detail='No reviews found for analysis')

    analyzed_movies = []
    for movie in movies:
        inputs = tokenizer(movie.review, return_tensors='pt', truncation=True, padding=True, max_length=512).to(device)
        outputs = model(**inputs)
        probs = outputs.logits.softmax(dim=1).detach().cpu().numpy()[0]

        sentiment_dict = {'positive': float(probs[1]), 'negative': float(probs[0])}
        movie.sentiment = json.dumps(sentiment_dict)
        session.add(movie)
        analyzed_movies.append(
            MovieResponse(
                id=movie.id,
                title=movie.title,
                director=movie.director,
                category=movie.category,
                rating=movie.rating,
                image_url=movie.image_url,
                review=movie.review,
                predicted_sentiment=sentiment_dict
            )
        )

    session.commit()
    return analyzed_movies