# Setting up the development environment 


## Dev tools

Links to downloads you may want/need

- https://discord.com/developers/applications
- https://git-scm.com/downloads
- https://cli.github.com/
- https://www.python.org/downloads/
- https://sqlite.org/download.html
- https://code.visualstudio.com/download

Note you may need to complete an MFA step in the browser before you can generate a bot token. 

## Setup

You may want to fork it first

`git clone https://github.com/danielzting/clearurls-discord-bot.git`

or 

`gh repo clone danielzting/clearurls-discord-bot`

Having installed `python`, create a virtual environment to manage dependencies 

`python -m venv .`

Activate the environment with `scripts\activate` (Windows) or `bin\activate` (Linux).

Then install dependencies with `pip install -r requirements.txt`

## Project structure 

The [unalix](https://github.com/AmanoTeam/Unalix/tree/master/unalix) library is archived. Its source is included in this project in the `unalix` folder.

The bot itself is in `main.py`.