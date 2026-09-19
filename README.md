# AniManga Bot

A maubot plugin that allows you to search for anime and manga in AniList or MyAnimeList (via [Tenrai API](https://tenrai.org/)) database.

The plugin requires `pillow` Python package that is not a part of the default maubot installation. It can be installed the same way you [install maubot](https://docs.mau.fi/maubot/usage/setup/index.html#production-setup):

```
cd maubot
source ./bin/activate
pip install --upgrade pillow
```

## Screenshots
<img width="45%" height="45%" alt="animangabig" src="https://github.com/user-attachments/assets/3d1e915c-60bd-48ed-a3df-d0b9b85a6ce9" />
<img width="45%" height="45%" alt="animanga1" src="https://github.com/user-attachments/assets/5c2e911c-2bdc-45b1-b61f-7e554d1ab398" />


## Usage

Type the title of the anime or manga:
```
!anime <title>
!manga <title>
```

The bot allows for a one-time edit of the search result. You can replace the main result with an entry from the *Other results* list found in the *LINKS* section. To do this, react to the bot's message using the 1️⃣, 2️⃣, 3️⃣, etc., emojis, The number on the emoji corresponds to the number in the *Other results* list.
It is also possible to completely remove the bot's message by reacting to it with the 👎 emoji.
The bot will accept one of these commands only if it comes from the person who originally triggered the `!anime` or `!manga` command.

## Configuration

It's possible to change plugin's configuration in maubot's control panel. Available options:
* `max_relations` - controls how many related entries will be displayed (default: 3)
* `max_results` - controls how many results will be displayed (default: 4)
* `use_mal_api` - if `true` uses Tenrai API instead of AniList API (default: `false`)

## Disclaimer

This plugin is not affiliated with AniList, MyAnimeList, and Tenrai API. It is not intended for commercial use or any purpose that violates Terms of Service of mentioned services. By using this plugin, you acknowledge that you will not use it in a way that infringes on these service's terms.
