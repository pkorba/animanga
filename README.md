# AniManga Bot

A maubot plugin that allows you to search for anime and manga in AniList or MyAnimeList (via [Tenrai API](https://tenrai.org/)) database.

The plugin requires `pillow` Python package that is not a part of the default maubot installation. It can be installed the same way you [install maubot](https://docs.mau.fi/maubot/usage/setup/index.html#production-setup):

```
cd maubot
source ./bin/activate
pip install --upgrade pillow
```

## Screenshots
### Compact view (default)
<img width="565" height="326" alt="animanga" src="https://github.com/user-attachments/assets/6df380b3-6ffb-4734-8a2e-72dac8360384" />

### Expanded view
<img width="30%" height="30%" alt="animanga_big" src="https://github.com/user-attachments/assets/2f4da2fb-85b2-4444-9c20-891c54a8d5fd" />

## Usage

Type the title of the anime or manga:
```
!anime <title>
!manga <title>
```

The bot allows for a one-time edit of the search result. You can replace the main result with an entry from the *Other results* list found in the *LINKS* section. To do this, react to the bot's message using the 1️⃣, 2️⃣, 3️⃣, etc., emojis, The number on the emoji corresponds to the number in the *Other results* list.
It is also possible to completely remove the bot's message by reacting to it with the 👎 emoji.
The bot will accept one of these commands only if it comes from the person who originally triggered the `!anime` or `!manga` command.

https://github.com/user-attachments/assets/9bf591c8-c0da-41e9-b713-3ca07bb1e528

## Configuration

It's possible to change plugin's configuration in maubot's control panel. Available options:
* `max_relations` - controls how many related entries will be displayed (default: 3)
* `max_results` - controls how many results will be displayed (default: 4)
* `use_mal_api` - if `true` uses Tenrai API instead of AniList API (default: `false`)

## Disclaimer

This plugin is not affiliated with AniList, MyAnimeList, and Tenrai API. It is not intended for commercial use or any purpose that violates Terms of Service of mentioned services. By using this plugin, you acknowledge that you will not use it in a way that infringes on these service's terms.
