# GateBot

```txt
 ______     ______     ______   ______     ______     ______     ______  
/\  ___\   /\  __ \   /\__  _\ /\  ___\   /\  == \   /\  __ \   /\__  _\
\ \ \__ \  \ \  __ \  \/_/\ \/ \ \  __\   \ \  __<   \ \ \/\ \  \/_/\ \/
 \ \_____\  \ \_\ \_\    \ \_\  \ \_____\  \ \_____\  \ \_____\    \ \_\
  \/_____/   \/_/\/_/     \/_/   \/_____/   \/_____/   \/_____/     \/_/
```

`v0.2.1`

A Telegram bot.

This is a gate bot that you can use to protect your group from a specific kind of users by letting them go through a bunch of question first, and answer them correctly in order to join the group, you can choose the questions yourself using `JSON`.

In short, the main feature requires you to complete a bunch of tests in order to join the group.

Or you can just disable that feature, and have it run as a bot that will do quizzes for people. For an example, to learn English maybe?

There are 4 main classes, `GateCommands()`, `GateJobs()`, `GateButtons()` and `GateHandlers()`. Continue reading to see how to extend this bot's functionality.

**Note**: the way this bot stores questions for every user is as a string `JSON`, I wanted to change it to only store the indexes of the questions, but this is less efficient when it comes to removing questions from the database, and I do want to make admins be able to remove questions, so I'm currently not very sure about this. However I don't worry about this since I use Redis.

---------------------------------------------------------------------------

## Demo

Here is a demo of it doing its thing, the questions are Python-related questions. Basically me trying to get things wrong/correct/unanswered.

![Imgur](https://i.imgur.com/QiqNp6o.gif)

---------------------------------------------------------------------------

## Configuration

The bot is configurable. And here are the documentations for the current config variables. To config the bot, have a look at `data/config.ini`.

### General

This section is for settings that shouldn't necessarily be categorized, or used in the same section as their original settings. `allow_rss` is an example, which allows you to disable the RSS without having to remove your RSS settings. This means that `[GENERAL]` is more of a "disable `$x`" and "enable `$y`". This README section covers all of the stuff in the `[GENERAL]` section.

Please keep in mind that some integers might be treated as `int(float()`. For an example, it would not make any sense if you used `20.6` in `["GENERAL"]["questions_count"]`. This will result in an error, simply because `int("20.6")`:

```text
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ValueError: invalid literal for int() with base 10: '20.6'
```

However, `int(float("20.6"))` will work fine, but I do not do that for most of the variables.

* `allow_rss`

    **default**: `false`

    _Enable or disable the RSS reader._

* `rss_interval`

    **default**: `1200`

    _If the RSS reader is allowed, and this is allowed, then this will be the default interval for RSS feeds with no settings (i.e. only a link provided)_

    _What an interval is:_ \
    _This is basically the update interval in **seconds**. For an example, an interval of `60` means: "run this RSS feed parser job every `60` **seconds**"._

* `rss_first`

    **default**: `5`

    _If the RSS reader is allowed, and this is allowed, then this will be the default first for RSS feeds with no settings (i.e. only a link provided)_

    _What a first is:_ \
    _This means "when the RSS feed parser job starts, how many **seconds** should it wait _before_ starting?_

* `send_start_no`

    **default**: `true`

    _This sends `[STRINGS]["no"]` when a user tries to send `/start` (or whatever your start command is named) to one of the main groups._

* `delete_commands`

    **default**: `false`

    _This will delete commands in a situation where:_
  * _an admin sends a commnad that results in an error._
  * _a user tries to send an admin/mod-only command._

* `questions_count`

    **default**: `20`

    _How many questions should the bot get for you from `quizzes.json` per user? The default is `20`, feel free to change it._

* `correct_answers`

    **default**: `11`

    _How many answers does the user need to get right in order to join the group? Must be **<= questions_count**._

* `test_delay`

    **default**: `1`

    _This config variable is for the `/test` command (or whatever it is for you), when you send `/test`, it will test all of the questions. This delay will determine how many seconds the bot should wait per question-testing, until it goes to the next one._

* `check_if_user_start`

    **default**: `false`

    _This will check if the user has started the test or not, every `[USER][check_sent_start_interval]`, if not, then kick them out. Otherwise do nothing._

* `log_kick_no_start_user`

    **default**: `false`

    _This will log the kick message from `[GENERAL][check_if_user_start]`, which you can also configure!_

* `enable_webhook`

    **default**: `false`

    _If you wanna enable the `[WEBHOOK]` section, change this to `true`. default is polling._

---------------------------------------------------------------------------

### Bot

* `bot_token`

---------------------------------------------------------------------------

### Redis

This is the database this bot uses. default settings are the Redis settings. That is, the port is `6379` and the server is `localhost` (`127.0.0.1`)

* `host`

    **default**: `localhost`

* `port`

    **default**: `6379`

---------------------------------------------------------------------------

### Webhooks

This bot provides an option to enable webhooks if you wanna treat your server with care, since the default option is polling, which is the equivalent of saying "hey server, did anything new happen?" over and over. Webhooks are different, they will get triggered once you do something, e.g. send a command to the bot. But you need to enable this in the `[GENERAL]` section. Change `webhooks` to `true`, and then change the settings in `[WEBHOOK]` to fit your needs.

Read this: [python-telegram-bot/wiki/Webhooks](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks)

If you wanna disable something, just comment it out.

* `listen`

    **default**: `0.0.0.0`

* `port`

    **default**: `8443`

* `url_path`

    **default**: `${BOT:bot_token}`

* `key`

    **default**: `private.key`

* `cert`

    **default**: `cert.pem`

* `webhook_url`

    **default**: `https://example.com:${port}/${url_path}`

---------------------------------------------------------------------------

### Chats

* `main_chats`

    **default**: `null`

    _If you wanna store multiple chats, then you have to seperate them with a comma. For an example: `-12345678,-12345679`_

---------------------------------------------------------------------------

### Administration

* `mods`

    **default**: `null`.

    _Add mods to your group, who will get treated as admins, even if they aren't one._

---------------------------------------------------------------------------

### User

* `failed_user_wait`

    **default**: `259200`

    _This is for when a user fails a test, how many seconds does he need to wait in order to do it again?_

* `check_sent_start`

    **default**: `600`

    _If the user hasn't sent `/start` to the bot in `600` seconds, it will kick them out. Optional._

* `check_sent_start_interval`

    **default**: `300`

    _Interval for the job method that checks whether the user has sent `/start` or not. Basically, run every `300` seconds._

    _This is recommended to be the half of `check_sent_start`'s value._

* `check_sent_start_start`

    **default**: `5`

    _First for the job method that checks whether the user has sent `/start` or not. Basically, (first) run after waiting `5` seconds._

---------------------------------------------------------------------------

### Commands

This is what you use to run your commands. However, this cannot be reconfigured again using the bot (`/config`), without having to restart the bot. I mean, yes, it can, but you have to restart the bot. And this is how I want it to be.

This is useful when you're using this bot with another bot, that has the same commands names, or just want to translate the commands to other langauge, or whatever.

* `config`

    **default**: `config`

* `edit`

    **default**: `edit`

* `extra`

    **default**: `extra`

* `help`

    **default**: `help`

* `lban`

    **default**: `lban`

* `remove`

    **default**: `remove`

* `start`

    **default**: `start`

* `test`

    **default**: `test`

* `version`

    default: `version`

---------------------------------------------------------------------------

### Strings

This section is for translating your bot, or just using different strings if you want to. Keep in mind that `{}` in the string, will be replaced by something, it's a placeholder for something. For an example, the string `user_took_quiz` in this section, has a `{username}`. This will be the placeholder for the username.

---------------------------------------------------------------------------

## Built-in commands

* `/lban`

    This command is used to ban multiple users at once. However, if this bot is used to reply to a text message, it will only ban the user that sent that message. It will send the same log message (i.e. banned `$x ..... OK`) but just for one user. If you wanna use it to ban multiple users at once, you can do something like this: \
    `/lban @username 1234567 UserNoUsername`, where:
  * `@username`: username of the user, will ban only if it exists in the database.
  * `1234567`: ID of a user, will do `getChatMember()`, if failed, skips.
  * `@UserNoUsername`: a user that doesn't have any username.

* `/config` (**TODO**)

    This command is used to change `config.ini` with a command, from your Telegram client.

* `/edit` (**TODO**)

    This command is used to edit or add new questions with a command, from your Telegram client.

* `/extra` (**TODO** I just need to add the data to the DB)

    This command is used to add `/extra` commands, which are commands that are stored in the Redis database that return strings. \
    Use the commands created with `!`, or change that in the settings.

* `/help` (**TODO**)

    This will return your help message, that's stored in `config.ini`, in the `[STRINGS]` section.

* `/remove` (**TODO**)

    Remove questions with a command, from your Telegram client.

* `/start`

    Nothing to say here, other than that this command's message can be configured. You have to, however, use the placehoders somewhere (temp! they will be optional soon).

* `/test`

    This command will go through all of the questions and test them, it will stop as soon as there's an exception. Maybe wrong JSON syntax, or whatever.

* `/version`

    Returns the bot's current version. This is usually useful for me.


## Questions

In `data/quizzes.json`, there should be something like this: (example of `quizzes.json` with 3 questions)

```json
{"quizzes": [
    {
        "answer": 1,
        "options": [
            "<code>__iter__()</code>",
            "<code>__iter__()</code> and <code>__next__()</code>",
            "<code>__iter__()</code> and <code>__super__()</code>",
            "<code>__iter__()</code>, <code>__super__()</code> and <code>__next__()</code>"
        ],
        "question": "What are the method(s) that iterator object must implement?"
    },
    {
        "answer": 1,
        "options": [
            "It's an argument to the function",
            "It's a hint for the type of <code>i</code>",
            "It's an assertion of the type of <code>i</code>",
            "It's a syntax error"
        ],
        "question": "What does <code>int</code> mean in this line: <code>def func(i: int):</code>"
    },
    {
        "answer": 0,
        "options": [
            "You add it to the super classes of a class",
            "You write it above the function or the class @likethis",
            "You implement the special <code>__mixin__</code> method",
            "You import it from <code>mixin</code> module"
        ],
        "question": "How do you use a <code>mixin</code>?"
    }
]}
```

So, basically, what you need is this:

```json
{
    "answer": 0,
    "options": [
        "You add it to the super classes of a class",
        "You write it above the function or the class @likethis",
        "You implement the special <code>__mixin__</code> method",
        "You import it from <code>mixin</code> module"
    ],
    "question": "How do you use a <code>mixin</code>?"
}
```

As you can tell, it uses `HTML` to format stuff. If you use correct `JSON` syntax, you should have something similar to this, for an example:

![example-question](https://i.imgur.com/dqef4a8.png)

The same-looking UI will be used.


## Dependencies

Install Redis → [redis.io/download](https://redis.io/download)

Run → `python3 setup install --user`, this will:

* Install `redis` → `pip3 install --user redis`
* Install `feedparser` → `pip3 install --user feedparser`
* Install `python-telegram-bot` → `pip3 install --user python-telegram-bot`


## TODO

* [ ] Maybe allow users to extend the bot's functionality by allowing indirect editing (not within the main source code). This is one of the reasons why I added classes for different things, maybe users can just inherit from the class and do stuff.
* [ ] Sort out the config stuff, some of them don't make any sense and would better fit in their own section.
* [ ] Do the TODOs from the commands header.


## Contribution

Yeah, sure, if there's a bug you found and you'd like to fix it, go ahead. Make sure that you follow `pep8` (not too much is OK), and if `flake8` gives you 0 warnings and 0 errors, like this:

![flake8](https://i.imgur.com/t0lIAre.png)

Then you'd be good to go, thanks!