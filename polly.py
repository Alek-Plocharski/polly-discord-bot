import discord

from discord.ext import commands
from discord.ext.commands import DefaultHelpCommand

from string import digits, ascii_lowercase
from random import choice
from collections import OrderedDict


bot_command_prefix = '!'
bot_token = '<YOUR_BOT_TOKEN_HERE>'


class PollyHelpCommand(DefaultHelpCommand):
    def __init__(self):
        super().__init__()
        self.no_category = f'Command prefix: \'{bot_command_prefix}\'\n\nCommands'
        self.indent = 0
        self.command_attrs['hidden'] = True
        self.command_attrs['help'] = 'Shows information about available commands. ' \
                                     'Can be invoked without any arguments to show available commands ' \
                                     'or with a command name to show its description.\n\n' \
                                     f'Examples:\n{bot_command_prefix}help\n{bot_command_prefix}help poll'

    def get_ending_note(self):
        command_name = self.invoked_with
        return f'Type {self.clean_prefix}{command_name} <command_name> for more information on a command.\n'


class Poll:
    def __init__(self, question, answers):
        self.question = question
        self.answers = answers
        self.poll_id = generate_poll_id()
        self.message = None


bot = commands.Bot(command_prefix=bot_command_prefix,
                   help_command=PollyHelpCommand(),
                   activity=discord.Activity(name=f'DM {bot_command_prefix}help for info',
                                             type=discord.ActivityType.playing))

create_poll_command_name = 'poll'
add_to_poll_command_name = 'poll_add'

poll_id_symbols = digits + ascii_lowercase
poll_id_length = 6
example_poll_id = '64ye5q'

polls_dict = OrderedDict()
max_number_of_polls_tracked = 20

emojis = ['🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯', '🇰', '🇱', '🇲',
          '🇳', '🇴', '🇵', '🇶', '🇷', '🇸', '🇹', '🇺', '🇼', '🇽', '🇾', '🇿']


def get_emoji_for_index(index):
    return emojis[index]


def generate_poll_id():
    return str.join('', [choice(poll_id_symbols) for _ in range(poll_id_length)])


def construct_question_string(question):
    return f'**{question}**\n'


def construct_answer_string(index, answer):
    return f'\n{get_emoji_for_index(index)} {answer}\n'


def construct_message_string(poll):
    message_string = ''
    message_string += construct_question_string(poll.question)
    for i, answer in enumerate(poll.answers):
        message_string += construct_answer_string(i, answer)
    message_string += f'\nPoll ID: {poll.poll_id}\n'
    return message_string


async def add_answer_reactions_in_range(message, start_index, end_index):
    for i in range(start_index, end_index + 1):
        await message.add_reaction(get_emoji_for_index(i))


async def add_answer_reactions(message, number_of_answers):
    await add_answer_reactions_in_range(message, 0, number_of_answers - 1)


def add_poll_to_dict(poll):
    while len(polls_dict) > max_number_of_polls_tracked:
        polls_dict.popitem()
    polls_dict[poll.poll_id] = poll


async def send_poll(ctx, poll):
    message_string = construct_message_string(poll)
    poll_message = await ctx.send(message_string)
    await add_answer_reactions(poll_message, len(poll.answers))
    poll.message = poll_message
    add_poll_to_dict(poll)


async def update_poll(ctx, poll, new_answers):
    poll.answers += new_answers
    message_string = construct_message_string(poll)
    await poll.message.edit(content=message_string)
    await add_answer_reactions_in_range(poll.message, len(new_answers), len(poll.answers) - 1)


@bot.command(name=create_poll_command_name,
             brief='Create a poll',
             help=f'Creates a poll with a given question and answers '
                  f'(max number of answers for a poll is {len(emojis)}). '
                  f'Each poll is assigned an ID allowing to reference it in other commands.\n\n'
                  f'Example:\n{bot_command_prefix}{create_poll_command_name} "Am I a useful bot?" '
                  f'Yes Definitely Absolutely!!!\n\n'
                  f'Note: Phrases containing spaces have to be put in double quotes.')
async def create_a_poll(ctx, question, *answers):
    if len(answers) == 0:
        await ctx.send(f'No answers provided')
    elif len(answers) > len(emojis):
        await ctx.send(f'Too many answers (got:{len(answers)}, max number: {len(emojis)})')
    else:
        await send_poll(ctx, Poll(question, answers))


@bot.command(name=add_to_poll_command_name,
             brief='Add answers to an existing poll',
             help=f'Adds answers to an existing poll with given ID '
                  f'(max number of answers for a poll is {len(emojis)}). '
                  f'Only recent polls can have answers added to them.\n\n'
                  f'Example:\n{bot_command_prefix}{add_to_poll_command_name} {example_poll_id} new_answer '
                  f'"brand new answer with spaces"\n\n'
                  f'Note: Phrases containing spaces have to be put in double quotes.')
async def add_new_answers_to_poll(ctx, poll_id, *answers):
    if poll_id not in polls_dict:
        await ctx.send(f'Couldn\'t find a poll with such ID - {poll_id} (note: only recent polls are tracked)')
    else:
        poll = polls_dict[poll_id]
        if len(answers) == 0:
            await ctx.send(f'No answers provided')
        elif len(answers) + len(poll.answers) > len(emojis):
            await ctx.send(f'Too many answers after adding to poll'f'(got:{len(answers) + len(poll.answers)}, max number: {len(emojis)})')
        else:
            await update_poll(ctx, poll, answers)


bot.run(bot_token)
