#!/usr/bin/env python
# -*- coding: utf-8 -*-

#############################################################################
#  ______     ______     ______   ______     ______     ______     ______   #
# /\  ___\   /\  __ \   /\__  _\ /\  ___\   /\  == \   /\  __ \   /\__  _\  #
# \ \ \__ \  \ \  __ \  \/_/\ \/ \ \  __\   \ \  __<   \ \ \/\ \  \/_/\ \/  #
#  \ \_____\  \ \_\ \_\    \ \_\  \ \_____\  \ \_____\  \ \_____\    \ \_\  #
#   \/_____/   \/_/\/_/     \/_/   \/_____/   \/_____/   \/_____/     \/_/  #
#                                                                           #
#############################################################################


from telegram import InlineKeyboardButton, InlineKeyboardMarkup, error
from telegram.ext import CommandHandler, Updater
from telegram.ext import CallbackQueryHandler, MessageHandler, Filters
from telegram.bot import Bot
from telegram.update import Update
from configparser import ConfigParser, ExtendedInterpolation
import random
import re
import os
import logging
import time
import json
import feedparser
import redis
import sys


# the reason why this is done, is to allow you to run the script anywhere
# it's always a full path.
path = os.path.dirname(os.path.realpath(sys.argv[0]))

__author__ = "Mario"
__copyright__ = "Copyright 2019, Mario || @dizaztor"
__license__ = "MIT"
__maintainer__ = "@dizaztor"
__email__ = "mario@dizator.com"
__version__ = "v0.2.0"

config = ConfigParser(interpolation=ExtendedInterpolation())
config.read(f"{path}/data/config.ini")


if config.sections() is []:
    print("Are you sure the config file is there? \
            This is read as an empty file!")
    sys.exit(0)

rdb: redis.Redis = redis.Redis(
    host=config["REDIS"]["host"],
    port=int(config["REDIS"]["port"]),
    db=0)

with open(f"{path}/data/quizzes.json") as quizzes_json:
    quizzes = json.load(quizzes_json)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)

logger = logging.getLogger(__name__)


def is_admin(bot: Bot, update: Update, user_id: int) -> bool:
    """
    This function checks if the given user_id is an admin

    returns True or False.
    """
    admins: list = [admin.user.id for admin in
                    bot.get_chat_administrators(update.message.chat.id)]
    return user_id in admins


def is_digit(obj: object) -> bool:
    """
    This functions checks if the given object is a digit.

    returns: True or False
    """
    try:
        int(float(obj))
        return True
    except ValueError:
        return False


def parse_rss(string: str) -> dict:
    """
    This function parses the RSS syntax string into a Python dictionary.

    If `interval` is not provided, then it defaults to the [GENERAL] section.
    rss_interval, which has the default value of 1200.

    If `first` is not provided, then it defaults to the [GENERAL] section.
    rss_first, which has the default value of 5.

    returns: dict
    """
    parsed: dict = {}
    for kv in string.split(","):
        kv = kv.split("=")
        key: str = kv[0]
        value: str = kv[1]
        if key == "link" and "reddit" in value:
            value = f"https://www.reddit.com/r/{value.split(':')[1]}/.rss"
        elif key == "interval" or key == "first":
            value = int(value)
        parsed[key] = value
    if "interval" not in parsed:
        parsed["interval"] = int(config["GENERAL"]["rss_interval"])
    if "first" not in parsed:
        parsed["first"] = int(config["GENERAL"]["rss_first"])
    return parsed


def parse_list(string: str, splitter: str = ",") -> list:
    """
    This function will parse the given string into a list,
    separating values with a comma, however:

    You can change that if you want with the splitter parameter.

    it will use `is_digit()` to check if the current string is a digit,

    if it is, then it will add it as a digit. That's it.

    returns: list
    """
    return [int(i.strip()) if is_digit(i)
            else i.strip() for i in string.split(splitter)]


def parse_dict(section: str) -> dict:
    """
    This function simply returns a dictionary based off a section of choice.

    returns: dict
    """
    return {key: value for key, value in config[section].items()}


def decode_dict(obj: dict) -> dict:
    """
    This function simply parses a dict from the Redis database
    and decode every value.

    returns: dict
    """
    return {key.decode("utf-8"): val.decode("utf-8")
            for key, val in obj.items()}


def get_results(obj: dict) -> dict:
    """
    This function will give you the results from a dictionary.
    For an example {"unanswered": 9, "correct": 2, "wrong": 2}
    And it just does that, the button handler will do the rest.
    E.g. see if the "correct" value is the same or bigger than the
    one in the config file.

    returns: dict
    """
    parsed = {"u": 0, "c": 0, "w": 0}
    for value in obj.values():
        parsed[value] += 1
    return parsed


class GateHandlers(object):

    def new_status(self, bot: Bot, update: Update) -> None:
        """
        This function handles incoming users or users leaving.

        If the user is a new chat member, then it will restrict them and
        link them to the bot, sending a message saying so (configurable).

        If the user is a member leaving (e.g. getting banned by the bot), then:
        It will check and see if config.ini wants to delete the status message.
        If it does, then delete it, otherwise, do nothing.

        returns: None
        """
        main_chats = config["CHATS"]["main_chats"]
        if update.message.chat_id not in parse_list(main_chats):
            update.message.reply_text(
                config["STRINGS"]["unknown_group"],
                format(ID=update.message.chat.id))
        else:
            if update.message.new_chat_members:
                from_id = update.message.new_chat_members[0].id
                from_username = update.message.new_chat_members[0].username
                if from_id in parse_list(config["CHATS"]["main_chats"]):
                    update.message.reply_text(
                        config["STRINGS"]["new_member_bot"])
                elif is_admin(bot, update, from_id):
                    pass
                else:
                    if from_username is not None:
                        rdb.hset(f"user:{from_id}", "username", from_username)
                    rdb.hset("users:start", from_id, time.time())
                    bot.restrict_chat_member(
                        chat_id=update.message.chat.id,
                        user_id=from_id,
                        can_send_message=False,
                        can_send_media_messages=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False)
                    ans = int(config['GENERAL']['correct_answers'])
                    que = int(config['GENERAL']['questions_count'])
                    update.message.reply_text(
                        text=config["STRINGS"]["send_me_start"].format(
                            correct_answers=ans,
                            questions_count=que,
                            calc_percentage=f"{int((ans/que)*100)}"),
                        parse_mode="Markdown",
                        disable_web_page_preview=True)


class GateButtons(object):
    def __init__(self):
        self.query = None

    """
    This method checks and sees what button handlers to call.
    It changes the direction of the call.

    returns: None
    """
    def diverter(self, bot: Bot, update: Update) -> None:
        self.query = update.callback_query
        print(self.query.data)
        if (self.query.data == "ready" or self.query.data[0] == "ready"):
            self.ready_handler(bot, update)
        elif "forward" in self.query.data or "back" in self.query.data:
            self.forward_or_back_handler(bot, update)
        elif "answer" in self.query.data:
            self.check_answer(bot, update)
        elif "ok_cool" in self.query.data:
            pass
        else:
            pass
        bot.answerCallbackQuery(
                callback_query_id=self.query.id)

    """
    When the user clicks on "Ready", this is the handler for that button.

    returns: None
    """
    def ready_handler(self, bot: Bot, update: Update) -> None:
        user_id: int = self.query.from_user.id
        name: str = f"user:questions:{user_id}"
        rdb.setnx(name,
                  json.dumps(random.sample(
                                quizzes["quizzes"],
                                int(config["GENERAL"]["questions_count"])),
                             sort_keys=True))
        rdb.hsetnx(f"user:{user_id}", "question", 0)
        # no need to do it with my old shitty way
        # i was just trying to make it work back then
        # so...
        # first question ;)
        self.make_keyboard(bot, update)

    """
    This method is responsible for making the keyboard layout.

    returns: None
    """
    def make_keyboard(self, bot: Bot, update: Update) -> None:
        user_id: int = self.query.from_user.id
        name: str = f"user:questions:{user_id}"
        name_results: str = f"user:results:{user_id}"
        user_questions = json.loads(rdb.get(name))
        question_number = int(rdb.hget(f"user:{user_id}", "question"))
        current_question = user_questions[question_number]
        question_id = quizzes["quizzes"].index(current_question)
        user_question_id = user_questions.index(current_question)
        keyboard = [[], []]
        rdb.hsetnx(
            name=name_results,
            key=user_question_id,
            value="u")
        chosen = rdb.hget(
            name=name_results,
            key=user_question_id).decode("utf-8")

        text = f"<code>(ID: {question_id})</code>\n" \
               f"{current_question['question']}\n"

        keyboard[1].append(InlineKeyboardButton(
            "<", callback_data=f"back"))
        keyboard[1].append(InlineKeyboardButton(
            f"{question_number + 1}/{config['GENERAL']['questions_count']}",
            callback_data=f"ok_cool"))
        keyboard[1].append(InlineKeyboardButton(
            ">", callback_data=f"forward"))

        # TODO: make this pretty.
        if chosen == "u":
            for option in current_question["options"]:
                option_index = current_question["options"].index(option)
                keyboard[0].append(InlineKeyboardButton(
                    str(option_index),
                    callback_data=f"answer:{user_question_id}:{option_index}",
                    parse_mode="HTML"))
                text += f"\n{option_index}) {option}"
        elif chosen == "c" or chosen == "w":
            for option in current_question["options"]:
                option_index = current_question["options"].index(option)
                text += f"\n{option_index}) {option}"
            choice = config["STRINGS"]["correct_choice"] if chosen == "c" \
                else config["STRINGS"]["wrong_choice"]
            text += f"\n\n<i>{choice}</i>"

        kwargs = {
            "chat_id": self.query.message.chat.id,
            "text": text,
            "reply_markup": InlineKeyboardMarkup(keyboard),
            "parse_mode": "HTML"}

        # had this as one line, but flake8... :(
        sendQuiz = bot.editMessageText
        kwargs["message_id"] = self.query.message.message_id
        sendQuiz(**kwargs)
        bot.answerCallbackQuery(
            callback_query_id=self.query.id)

    """
    This method is handles your > and < clicks (i.e. forward and back)
    However, the only thing it basically does it either increment your
    current question_number or decrement it.

    This means that:
    If you /start a quiz, and keep at, let's say, question number 4.
    Decide to /start another quiz for some reason, then it will start
    at the same question that you left unanswered, or just left it there.

    If, let's say, it didn't start at the same question, it will start at 0,
    and when you click > (forward), it will go to question number 5, since
    left at 4.

    Keep in mind that this method only handles what's said above,
    self.make_keyboard is still the one responsible for making the layout.
    This method just updates the Redis database, and calls self.make_keyboard.
    It will also either restrict members and put them in the wait database
    if they finished the questions and didn't score enough, or unrestrict
    them.

    returns: None
    """
    def forward_or_back_handler(self, bot: Bot, update: Update) -> None:
        # TODO: this is very unstable and buggy, fix.
        user_id: int = self.query.from_user.id
        name: str = f"user:{user_id}"
        question_number = int(rdb.hget(name, "question"))
        max_number = int(config["GENERAL"]["questions_count"]) - 1
        min_correct = int(config["GENERAL"]["correct_answers"])
        if "forward" in self.query.data:
            rdb.hincrby(name, "question", 1)
        elif "back" in self.query.data:
            rdb.hincrby(name, "question", -1)

        if question_number > max_number:
            rdb.hset(name, "question", -1)
        elif question_number == max_number:
            user_results = get_results(decode_dict(
                rdb.hgetall(f"user:results:{user_id}")))
            if user_results["u"] == 0:
                if user_results["c"] >= min_correct:
                    bot.answerCallbackQuery(
                        callback_query_id=self.query.id,
                        text=config["STRINGS"]["enough_correct"],
                        show_alert=True)
                    for chat_id in parse_list(config["CHATS"]["main_chats"]):
                            bot.restrictChatMember(
                                chat_id=chat_id,
                                user_id=user_id,
                                can_send_messages=True,
                                can_send_media_messages=True,
                                can_send_other_messages=True,
                                can_add_web_page_previews=True)
                else:
                    rdb.setnx(f"user:wait:{user_id}", time.time())
                    bot.answerCallbackQuery(
                        callback_query_id=self.query.id,
                        text=config["STRINGS"]["has_to_wait"],
                        show_alert=True)
            else:
                bot.answerCallbackQuery(
                        callback_query_id=self.query.id,
                        text=config["STRINGS"]["unanswered_questions"],
                        show_alert=True)
            return
        elif question_number < 0:
            rdb.hincrby(name, "question", 1)

        self.make_keyboard(bot, update)

    """
    This method simply checks if the chosen answer is correct or not.
    And then changes the database based on the results.

    It also calls self.make_keyboard() to set up the layout.

    returns: None
    """
    def check_answer(self, bot: Bot, update: Update) -> None:
        user_id: int = self.query.from_user.id
        name: str = f"user:questions:{user_id}"
        name_results: str = f"user:results:{user_id}"
        answer_data = parse_list(self.query.data, splitter=":")
        print(answer_data)
        chosen = rdb.hget(
            name=name_results,
            key=answer_data[1]).decode("utf-8")
        if chosen != "u":
            bot.answerCallbackQuery(
                callback_query_id=self.query.id,
                text=config["STRINGS"]["already_chosen"],
                show_alert=True)
            return
        else:
            user_questions = json.loads(rdb.get(name))
            current_question = user_questions[answer_data[1]]
            choice_string = "c" if int(current_question["answer"]) \
                == answer_data[2] else "w"
            print(choice_string)
            print(current_question)
            rdb.hset(
                name=name_results,
                key=answer_data[1],
                value=choice_string)
            self.make_keyboard(bot, update)


class GateJobs(object):
    """Main class for PythonTalkTalk's jobs, this contains \
    only the jobs for the bot. I.e. doing $X every $Y"""

    """
    This method handles parsing the RSS feeds and doing stuff with them.
    It can handle as many RSS feeds as you want, and it will save the data
    for each different RSS in a special folder `rss` in src/data/rss

    This is done simply to know new entries. I can avoid doing this, but then
    I'd have to store them in memory, which I might do later on, since I'm
    using Redis anyways. This is just the rewritten version of the old source
    code.

    returns: None
    """
    def rss_reader(self, bot, job) -> None:
        args = job.context
        feed = feedparser.parse(args["link"])
        file_name = f"data/rss/{args['name']}_rss.txt"
        try:
            with open(file_name, "r+") as rss_file:
                pass
        except FileNotFoundError:
            with open(file_name, "w") as rss_file:
                pass
        with open(file_name, "r+") as rss_file:
            data = [line.rstrip("\n") for line in rss_file]
            entries = [entry["title"] for entry in feed["entries"]]
            new_entries = [entry for entry in entries
                           if entry not in set(data)]
            if len(new_entries) != 0:
                final_message = f"RSS (registered name):" \
                    f" <code>{args['name']}</code>" \
                    f" [<code>ID {args['ID']}</code>]\n\n"
                for entry in feed["entries"]:
                    if entry["title"] in new_entries:
                        final_message += (f"→ <a href=\"{entry['link']}\">"
                                          f"{entry['title']}</a>\n")
                    else:
                        continue
                for chat in parse_list(config["CHATS"]["main_chats"]):
                    bot.sendMessage(
                        chat_id=chat,
                        text=final_message,
                        parse_mode="HTML",
                        disable_web_page_preview=True)
            rss_file.seek(0)
            rss_file.truncate()
            rss_file.write("\n".join(entries))

    """
    This method will check if there are any users who haven't sent `/start`
    to the bot in 10 minutes (can change that in `config.ini`)

    You can also configure how long it takes for the this job to run again.

    returns: None
    """
    def has_sent_start(self, bot, job) -> None:
        current_time = time.time()
        for from_id, start_time in rdb.hgetall("users:start").items():
            if not is_digit(from_id) and not is_digit(start_time):
                continue
            from_id = int(from_id)
            start_time = int(float(start_time))
            if current_time - start_time < \
                    int(config["USER"]["check_sent_start"]):
                continue
            for custom_chat in parse_list(config["CHATS"]["main_chats"]):
                custom_chat = int(custom_chat)
                bot.kickChatMember(
                    chat_id=custom_chat,
                    user_id=from_id)
                bot.unbanChatMember(
                    chat_id=custom_chat,
                    user_id=from_id)
                rdb.hdel("users:start", from_id)
                if config["GENERAL"]["log_kick_no_start_user"] == "true":
                    from_username = rdb.hget(
                        f"user:{from_id}",
                        "username").decode("utf-8")
                    log_message = config["STRINGS"]["no_start"].format(
                        username=from_username)
                    bot.sendMessage(
                        chat_id=custom_chat,
                        text=log_message,
                        parse_mode="Markdown")


class GateCommands(object):
    """Main class for GateBot, this contains only \
    the main non-modular commands. Sorted alphabetically."""

    def config(self, bot: Bot, update: Update) -> None:
        pass

    def edit(self, bot: Bot, update: Update) -> None:
        user_id: int = update.message.from_user.id
        if is_admin(bot, update, user_id):
            pass
        else:
            pass

    """
    This method handles extra commands, which are commands that you use to
    return the saved value, that you first used to create the extra command.

    Um, for an example, sending `/extra #hello [no hello]`, will register the
    command `#hello` to `no hello`.

    You do not need to escape anything, regex will simply get anything
    between the first [, and the last occurance of ].

    returns: None
    """
    def extra(self, bot: Bot, update: Update) -> None:
        user_id: int = update.message.from_user.id
        if is_admin(bot, update, user_id):
            text: str = update.message.text
            value_pattern = re.compile("\\[\\s*.*\\s*\\]")
            key_pattern = re.compile("#[_A-z0-9]*")
            value_match = re.findall(value_pattern, text)
            key_match = re.findall(key_pattern, text)
            value = value_match[0] if len(value_match) >= 1 else None
            key = key_match[0] if len(key_match) >= 1 else None
            if key and value:
                # TODO: add functionality
                pass
            else:
                update.message.reply_text(
                    text=config["STRINGS"]["failed_match"],
                    parse_mode="Markdown")
        else:
            if config["GENERAL"]["delete_commands"] == "true":
                bot.delete_message(chat_id=update.message.chat.id,
                                   message_id=update.message.message_id)

    def help(self, bot: Bot, update: Update) -> None:
        pass

    """
    This method handles banning multiple users only in the chat that the
    command was used from. This will not ban other users if they were in
    the [CHATS] section, "main_chats".

    If used as a reply to a message, it will only ban the user that sent
    the original message.

    If used as a normal command, then it will ban every single user used in
    the command, user with usernames have to be in the database, obviously.
    This isn't really a good idea since people can change usernames, but
    if you wanna do it, then I guess you can also do it this way.

    It will build up a nice log message telling you whether banning a
    specific user was successful or not.

    returns: None
    """
    def lban(self, bot: Bot, update: Update) -> None:
        from_id: int = update.message.from_user.id
        message: str = update.message.text
        if is_admin(bot, update, from_id) and len(message.split()) >= 2:
            ids_to_ban: dict = {}
            final_message = "<b>Banning log:</b>\n"
            if update.message.reply_to_message:
                reply_id = update.message.reply_to_message.from_user.id
                ids_to_ban[reply_id] = update.message.reply_to_message.\
                    from_user.username
            else:
                entities = update.message.parse_entities()
                for entity in entities:
                    mention = message[entity.offset:
                                      entity.offset + entity.length]
                    if entity.type == "mention":
                        user_id = rdb.get(f"username:{mention[1:]}")
                        if user_id != 0:
                            ids_to_ban[user_id] = mention
                    elif entity.type == "phone_number":
                        try:
                            from_user_id = bot.getChatMember(
                                chat_id=update.message.chat.id,
                                user_id=mention)
                            ids_to_ban[from_user_id.user.id] = \
                                from_user_id.user.first_name
                        except error.BadRequest:
                            continue
                    elif entity.type == "text_mention":
                        ids_to_ban[entity.user.id] = entity.user.first_name
            for usr in ids_to_ban:
                status: str = ""
                log_msg = f"<code>{ids_to_ban[usr]} {'.'*5} {status}</code>\n"
                try:
                    bot.kickChatMember(
                        chat_id=update.message.chat_id,
                        user_id=usr)
                    final_message += log_msg.format(status="OK")
                except error.BadRequest:
                    final_message += log_msg.format(status="FAIL")
            bot.sendMessage(
                chat_id=update.message.chat.id,
                text=final_message,
                parse_mode="HTML")
        else:
            if config["GENERAL"]["delete_commands"] == "true":
                bot.delete_message(chat_id=update.message.chat.id,
                                   message_id=update.message.message_id)

    def remove(self, bot: Bot, update: Update) -> None:
        if is_admin(bot, update, update.message.from_user.id):
            pass
        else:
            if config["GENERAL"]["delete_commands"] == "true":
                bot.delete_message(chat_id=update.message.chat.id,
                                   message_id=update.message.message_id)

    def start(self, bot: Bot, update: Update) -> None:
        if update.message.chat_id not in parse_list(
                config["CHATS"]["main_chats"]):
            from_id = update.message.from_user.id
            from_username = update.message.from_user.username
            name = f"user:{from_id}"
            if from_username is not None:
                rdb.hsetnx(name, "username", from_username)
            if rdb.hget(name, "allowed") == "true":
                update.message.reply_text(config["STRINGS"]["user_took_quiz"])
            else:
                keyboard = [[InlineKeyboardButton(
                        config["STRINGS"]["ready"],
                        callback_data="ready")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.message.reply_text(
                    config["STRINGS"]["start_message"].format(
                        username=from_username,
                        start=config["COMMANDS"]["start"],
                        correct_answers=config["GENERAL"]["correct_answers"],
                        questions_count=config["GENERAL"]["questions_count"]),
                    parse_mode="Markdown",
                    reply_markup=reply_markup)
        else:
            if config["GENERAL"]["send_start_no"] == "true":
                update.message.reply_text(config["STRINGS"]["no"])
            if config["GENERAL"]["delete_commands"] == "true":
                bot.delete_message(chat_id=update.message.chat.id,
                                   message_id=update.message.message_id)

    def test(self, bot: Bot, update: Update) -> None:
        if is_admin(bot, update, update.message.from_user.id):
            command = update.message.text.split()
            start_index: int = 0
            end_index: int = -1
            syntax = command[1].split("-") if len(command) == 2 else None
            if is_digit(syntax[0]) and is_digit(syntax[1]):
                start_index = int(syntax[0])
                end_index = int(syntax[1])
            for question in quizzes["quizzes"][start_index:end_index]:
                text = f'<code>(ID: {quizzes["quizzes"].index(question)})' \
                    f'</code>\n{question["question"]}\n'
                text += "\n".join(question["options"])
                text += "\nAnswer: " + str(question["answer"])
                update.message.reply_text(text, parse_mode="HTML")
                time.sleep(int(config["GENERAL"]["test_delay"]))
        else:
            if config["GENERAL"]["delete_commands"] == "true":
                bot.delete_message(chat_id=update.message.chat.id,
                                   message_id=update.message.message_id)

    def version(self, bot: Bot, update: Update) -> None:
        update.message.reply_text(__version__)


def main():
    updater: Updater = Updater(config["BOT"]["bot_token"],
                               request_kwargs={"read_timeout": 6,
                                               "connect_timeout": 7})
    gate_buttons: GateButtons = GateButtons()
    gate_commands: GateCommands = GateCommands()
    gate_jobs: GateJobs = GateJobs()
    gate_handlers: GateHandlers = GateHandlers()

    dispatcher = updater.dispatcher
    # TODO: fix this, not okay.
    dispatcher.add_handler(CommandHandler(
              config["COMMANDS"]["config"],
              gate_commands.config))
    dispatcher.add_handler(CommandHandler(
              config["COMMANDS"]["edit"],
              gate_commands.edit))
    dispatcher.add_handler(CommandHandler(
              config["COMMANDS"]["extra"],
              gate_commands.extra))
    dispatcher.add_handler(CommandHandler(
              config["COMMANDS"]["help"],
              gate_commands.help))
    dispatcher.add_handler(CommandHandler(
              config["COMMANDS"]["lban"],
              gate_commands.lban))
    dispatcher.add_handler(CommandHandler(
              config["COMMANDS"]["remove"],
              gate_commands.remove))
    dispatcher.add_handler(CommandHandler(
              config["COMMANDS"]["start"],
              gate_commands.start))
    dispatcher.add_handler(CommandHandler(
              config["COMMANDS"]["test"],
              gate_commands.test))
    dispatcher.add_handler(CommandHandler(
              config["COMMANDS"]["version"],
              gate_commands.version))
    dispatcher.add_handler(CallbackQueryHandler(gate_buttons.diverter))
    dispatcher.add_handler(MessageHandler(
        Filters.status_update,
        gate_handlers.new_status))

    jobs = dispatcher.job_queue
    counter_ID: int = 0

    if config["GENERAL"]["check_if_user_start"] != "true":
        pass
    else:
        jobs.run_repeating(
            gate_jobs.has_sent_start,
            interval=int(config["USER"]["check_sent_start_interval"]),
            first=int(config["USER"]["check_sent_start_first"]))

    if config["GENERAL"]["allow_rss"] != "true":
        pass
    else:
        rss_jobs = [config["RSS"][rss_job] for rss_job in config["RSS"]
                    if config["RSS"] != [] and rss_job != ""]
        for rss_job in rss_jobs:
            parsed = parse_rss(rss_job)
            jobs.run_repeating(
                gate_jobs.rss_reader,
                interval=parsed["interval"],
                first=parsed["first"],
                context={"link": parsed["link"],
                         "name": rss_job,
                         "ID": counter_ID})
            counter_ID += 1

    if config["GENERAL"]["enable_webhook"] == "true":
        updater.start_webhook(**parse_dict(config["WEBHOOK"]))
    else:
        updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
