from dataclasses import dataclass


@dataclass
class SearchResult:
    id: int = 0,
    id_mal: int = 0,
    title_en: str = "",
    title_ro: str = "",
    media_type: str = "",


@dataclass
class AniMangaData:
    id: int = 0,
    id_mal: int = 0,
    title_ro: str = "",
    title_en: str = "",
    title_ja: str = "",
    type: str = "",
    image: str = "",
    start_date: str = "",
    end_date: str = "",
    description: str = "",
    average_score: int = 0,
    mean_score: int = 0,
    votes: int = 0,
    favorites: int = 0,
    nsfw: bool = False,
    format: str = "",
    status: str = "",
    genres: list[str] = [],
    tags: list[str] = [],
    episodes: int = 0,
    season: str = "",
    season_year: int = 0,
    next_episode_num: int = 0,
    next_episode_date: str = "",
    duration: int = 0,
    relations: list[tuple[str, SearchResult]] = [],
    studios: set[tuple[str, int]] = {},
    studio_number: int = 0,
    links: list[tuple[str, str]] = [],
    volumes: int = 0,
    chapters: int = 0,
    trailer: tuple[str, str] = ()


media_formats = {
    "TV": "TV Show",
    "TV_SHORT": "TV Short",
    "MOVIE": "Movie",
    "SPECIAL": "Special",
    "OVA": "OVA",
    "ONA": "ONA",
    "MUSIC": "Music",
    "MANGA": "Manga",
    "NOVEL": "Novel",
    "ONE_SHOT": "One Shot"
}

statuses = {
    "FINISHED": "Finished",
    "RELEASING": "Releasing",
    "NOT_YET_RELEASED": "Not Yet Released",
    "CANCELLED": "Cancelled",
    "HIATUS": "Hiatus",
}

seasons = {
    "WINTER": "Winter",
    "SPRING": "Spring",
    "SUMMER": "Summer",
    "FALL": "Fall"
}

# Numbers are used for sorting the relations
relation_types = {
    "ADAPTATION": ("Adaptation", 0),
    "PREQUEL": ("Prequel", 1),
    "SEQUEL": ("Sequel", 2),
    "PARENT": ("Parent", 3),
    "SIDE_STORY": ("Side Story", 4),
    "SPIN_OFF": ("Spin Off", 5),
    "ALTERNATIVE": ("Alternative", 6),
    "SUMMARY": ("Summary", 7),
    "SOURCE": ("Source", 8),
    "COMPILATION": ("Compilation", 9),
    "OTHER": ("Other", 10),
    "CONTAINS": ("Contains", 11),
    "CHARACTER": ("Character", 12)
}

months = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec"
}
