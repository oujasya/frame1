// A fixed sample selection, never represented as current TMDB charts.
export const demoMovies = [
[693134,'Dune: Part Two','2024','1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg','Paul Atreides follows a dangerous path across Arrakis.'],
[569094,'Spider-Man: Across the Spider-Verse','2023','8Vt6mWEReuy4Of61Lnj5Xj704m8.jpg','Miles Morales discovers a world beyond his own.'],
[872585,'Oppenheimer','2023','ptpr0kGAckfQkJeJIt8st5dglvd.jpg','A physicist confronts the consequences of his work.'],
[545611,'Everything Everywhere All at Once','2022','w3LxiVYdWWRvEVdn5RYq6jIqkb1.jpg','An ordinary life opens onto extraordinary possibilities.'],
[157336,'Interstellar','2014','gEU2QniE6E77NI6lCU6MxlNBvIx2.jpg','A journey beyond Earth in search of a future.'],
[329865,'Arrival','2016','x2FJsf1ElAgr63Y3PNPtJrcmpoe.jpg','A linguist searches for understanding after an unexpected arrival.'],
[129,'Spirited Away','2001','39wmItIWsg5sZMyRUHLkWBcuVCM.jpg','A young girl finds courage in an unfamiliar world.'],
[496243,'Parasite','2019','7IiTTgloJzvGI1TAYymCfbfl3vT.jpg','Two families become entangled across a widening social divide.']
].map(([id,title,release_date,poster,overview])=>({id,title,release_date,poster_path:`/${poster}`,overview,vote_average:0}));
export const demoBackdrop='/xOMo8BRK7PfcJvHmz2j7s5GnZV1.jpg';
