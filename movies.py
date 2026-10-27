import os,re,time
from collections import OrderedDict
from datetime import datetime,timezone
from urllib.parse import urlparse
import httpx
from django.http import HttpResponse
from rest_framework.response import Response
from .common import endpoint,required,page,Problem
cache=OrderedDict()
client=httpx.Client(timeout=httpx.Timeout(6,connect=3))

def tmdb(path,**params):
    key=(path,tuple(sorted(params.items())));old=cache.get(key)
    if old and time.monotonic()-old[0]<300:return dict(old[1])
    token=os.getenv('TMDB_READ_ACCESS_TOKEN','').strip();api_key=os.getenv('TMDB_API_KEY','').strip()
    if not token and not api_key:raise Problem(503,{'code':'TMDB_NOT_CONFIGURED','message':'Movie service is not configured. Add a TMDB credential on the backend.'})
    headers={'Authorization':f'Bearer {token}'} if token else {};query={'language':'en-US',**params}
    if not token:query['api_key']=api_key
    try:
        for attempt in range(3):
            try:
                result=client.get('https://api.themoviedb.org/3'+path,params=query,headers=headers)
                if result.status_code==404:raise Problem(404,'Movie not found.')
                if result.status_code==429:raise Problem(429,'Movie service is busy. Please try again shortly.')
                if result.status_code>=500 and attempt<2:time.sleep(.2*(attempt+1));continue
                result.raise_for_status();data=result.json();break
            except (httpx.NetworkError,httpx.TimeoutException):
                if attempt==2:raise Problem(502,'Movie service connection timed out. Please try again.')
                time.sleep(.2*(attempt+1))
        cache[key]=(time.monotonic(),data);cache.move_to_end(key)
        while len(cache)>128:cache.popitem(last=False)
        return dict(data)
    except (httpx.HTTPError,ValueError,Problem) as error:
        if old and time.monotonic()-old[0]<1800 and getattr(error,'status_code',502) in (429,502,503):return {**old[1],'_stale':True}
        if isinstance(error,Problem):raise
        raise Problem(502,'Movie service is temporarily unavailable.')

@endpoint('GET')
def health(request):return Response({'status':'ok','backend':'django','tmdb_configured':bool(os.getenv('TMDB_API_KEY') or os.getenv('TMDB_READ_ACCESS_TOKEN'))})

@endpoint('GET')
def collection(request,kind):
    number=page(request,500)
    if kind=='country':
        user=required(request)
        if not user.country:raise Problem(409,'Choose a country in your profile first.')
        data=tmdb('/discover/movie',with_origin_country=user.country,sort_by='popularity.desc',include_adult='false',include_video='false',page=number,**{'primary_release_date.lte':datetime.now(timezone.utc).date().isoformat()})
        return Response({**data,'country':user.country,'ranking_basis':'TMDB global popularity among films originating in the selected country','cached':bool(data.get('_stale')),'stale':bool(data.get('_stale'))})
    paths={'trending':'/trending/movie/week','popular':'/movie/popular','top-rated':'/movie/top_rated'}
    return Response(tmdb(paths[kind],page=number))

@endpoint('GET')
def search(request):
    p=request.query_params;query=p.get('query','');params={'page':page(request,500),'include_adult':'false'}
    if len(query)>200 or query and not query.strip():raise Problem(422,'Enter a valid movie title.')
    def integer(name,minimum,maximum):
        if not p.get(name):return None
        try:value=int(p[name])
        except ValueError:raise Problem(422,f'Invalid {name}.')
        if not minimum<=value<=maximum:raise Problem(422,f'Invalid {name}.')
        return value
    year=integer('year',1888,2100);genre=integer('genre',1,999999);language=p.get('language')
    if language and not re.fullmatch('[a-z]{2}',language):raise Problem(422,'Invalid language.')
    if year:params['primary_release_year']=year
    if query.strip():
        data=tmdb('/search/movie',query=query.strip(),**params)
        if genre or language:data={**data,'results':[m for m in data.get('results',[]) if (not genre or genre in m.get('genre_ids',[])) and (not language or language==m.get('original_language'))]}
        return Response({**data,'filtered':bool(genre or language)})
    if genre:params['with_genres']=genre
    if language:params['with_original_language']=language
    return Response(tmdb('/discover/movie',sort_by='popularity.desc',**params))

@endpoint('GET')
def detail(request,movie_id):
    if movie_id<1:raise Problem(422,'Invalid movie ID.')
    return Response(tmdb(f'/movie/{movie_id}',append_to_response='credits,videos,recommendations'))

@endpoint('GET')
def providers(request,movie_id):
    if movie_id<1:raise Problem(422,'Invalid movie ID.')
    user=required(request)
    if not user.country:raise Problem(422,'Choose your country in your profile first.')
    data=tmdb(f'/movie/{movie_id}/watch/providers');region=data.get('results',{}).get(user.country,{})
    link=region.get('link','');parsed=urlparse(link)
    return Response({'country':user.country,**{key:region.get(key,[]) for key in ('flatrate','free','ads','rent','buy')},'link':link if parsed.scheme=='https' and parsed.hostname in ('themoviedb.org','www.themoviedb.org') else None,'_stale':bool(data.get('_stale'))})

@endpoint('GET')
def artwork(request,size,filename):
    if size not in ('w300','w500','w1280') or not re.fullmatch(r'[a-zA-Z0-9_-]+\.(jpg|png|webp)',filename):raise Problem(404,'Image not found.')
    try:
        response=client.get(os.getenv('TMDB_IMAGE_BASE_URL','https://image.tmdb.org/t/p').rstrip('/')+'/'+size+'/'+filename,timeout=8);response.raise_for_status()
        if not response.headers.get('content-type','').startswith('image/') or len(response.content)>5_000_000:raise Problem(502,'Poster unavailable.')
        return HttpResponse(response.content,content_type=response.headers['content-type'],headers={'Cache-Control':'public, max-age=86400'})
    except httpx.HTTPError:raise Problem(502,'TMDB poster unavailable. Please try again later.')
