general = """
query ($page: Int = 1, $perPage: Int, $search: String, $type: MediaType) {
    Page(page: $page, perPage: $perPage) {
        media(search: $search, type: $type) {
            id
            idMal
            title {
                romaji
                english
            }
        }
    }
}
"""

anime = """
query ($id: Int) {
    Media (id: $id) {
        id
        idMal
        title {
            romaji
            english
            native
        }
        type
        coverImage {
            large
        }
        trailer {
            site
            id
        }
        startDate {
            day
            month
            year
        }
        endDate {
            day
            month
            year
        }
        description
        averageScore
        meanScore
        stats {
            scoreDistribution {
                amount
            }
        }
        favourites
        isAdult
        format
        status
        genres
        tags {
            name
            isMediaSpoiler
        }
        episodes
        season
        seasonYear
        nextAiringEpisode {
            airingAt
            episode
        }
        duration
        relations {
            edges {
                relationType
                node {
                    id
                    idMal
                    title {
                        romaji
                        english
                    }
                    type
                }
            }
        }
        studios {
            nodes {
                id
                name
                isAnimationStudio
            }
            edges {
                isMain
                node {
                    id
                    name
                }
            }
        }
        externalLinks {
            url
            site
        }
    }
}
"""

manga = """
query ($id: Int) {
    Media (id: $id) {
        id
        idMal
        title {
            romaji
            english
            native
        }
        type
        coverImage {
            large
        }
        startDate {
            day
            month
            year
        }
        endDate {
            day
            month
            year
        }
        description
        averageScore
        meanScore
        stats {
            scoreDistribution {
                amount
            }
        }
        volumes
        chapters
        favourites
        isAdult
        format
        status
        genres
        tags {
            id
            name
            isMediaSpoiler
        }
        relations {
            edges {
                relationType
                node {
                    id
                    idMal
                    title {
                        romaji
                        english
                    }
                    type
                }
            }
        }
        externalLinks {
            url
            site
        }
    }
}
"""
