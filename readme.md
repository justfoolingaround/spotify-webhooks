### For what is the point of development, if you can't flex.

# `spotify-webhooks`

The one way connection between your Spotify client and your Discord.

This project uses [`spotivents`](https://github.com/justfoolingaround/spotivents) with some tweaking. Due to this library, this code with minimal API calls while maintaining near-live updates.

> **Note**:
> The player progress is not dynamic. It updates only if the event updates it.

## So, what's the point?

- **It is a flex.**
- It is the demonstration of what [`spotivents`](https://github.com/justfoolingaround/spotivents) is capable of.
- It may serve as a private Spotify presence for your friends and *only* your friends (if you have any that is).
- It exposes private session and the current volume of your active device (because why not?)
- It is clean, unless you try and re-run it a million times.

## Usage

-
    ```console
    $ py webhooks.py
    ```

For debug mode (the mode that shows websocket latency, last received event, Spotivents device and if Spotivents is invisible.),

-
    ```console
    $ py webhooks.py -d
    ```

For invisible mode (the mode where Spotivents does not bother with showing its presence (for stalking your crush ik ik.).),

- 
    ```console
    $ py webhooks.py -i
    ```

## Screenshots

<p align="center">
<img src="https://media.discordapp.net/attachments/848266763824922644/1067475698165497856/Screenshot_20230124-215208.jpg">
</p>

> **Note**:
> If you don't use `-d`, the bottom embed will not appear.