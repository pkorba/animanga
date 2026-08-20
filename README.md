# AniManga Bot

A maubot plugin that allows you to search for anime and manga in AniList database.

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

## Configuration

It's possible to change plugin's configuration in maubot's control panel. Available options:
* `max_relations` - controls how many related entries will be displayed (defaults to 3)
* `max_results` - controls how many results will be displayed (defaults to 4)

## Disclaimer

This plugin is not affiliated with AniList. It is not intended for commercial use or any purpose that violates AniList's Terms of Service. By using this plugin, you acknowledge that you will not use it in a way that infringes on AniList's terms. The official AniList website can be found at https://anilist.co.
