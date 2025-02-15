# awap-engine-2025

Welcome to AWAP 2025!

## Installation

We use python version >= 3.9
<br>
<br>

This installs pygame for visualization purposes:

`pip install -r requirements.txt`

## Quick Start

#### Try our tutorial bots!

#### Run this for a sample bot vs bot game:

`python3 run_game.py -c config.json`
<br>
<br>


#### Run this for a pygame-based vizualization:

`python3 run_game.py -b bots/attack_bot_v1.py -r bots/builder_bot.py -m maps/simple_map.awap25m --render`

Equivalently, running the above command without the render flag does not render the pygame.
<br>
<br>


#### Run this for an ascii-based vizualization in the terminal after running a previous command:

`python3 replay_game_cli.py replays/game_replay.awap25r`
<br>
<br>


To create a bot, add a new file to `/bots`.