import re
import random
import itertools
import math
from collections import defaultdict, deque

from src.utilities import *
from src import channels, users, debuglog, errlog, plog
from src.functions import get_players, get_all_players, get_main_role, get_reveal_role
from src.decorators import command, event_listener
from src.containers import UserList, UserSet, UserDict, DefaultUserDict
from src.messages import messages
from src.status import try_misdirection, try_exchange, try_protection, add_dying

def _get_targets(var, pl, user):
    """Gets the mad scientist's targets.

    var - settings module
    pl - list of alive players
    nick - nick of the mad scientist

    """
    for index, player in enumerate(var.ALL_PLAYERS):
        if player is user:
            break

    num_players = len(var.ALL_PLAYERS)
    target1 = var.ALL_PLAYERS[index - 1]
    target2 = var.ALL_PLAYERS[(index + 1) % num_players]
    if num_players >= var.MAD_SCIENTIST_SKIPS_DEAD_PLAYERS:
        # determine left player
        i = index
        while True:
            i = (i - 1) % num_players
            if var.ALL_PLAYERS[i] in pl or var.ALL_PLAYERS[i] is user:
                target1 = var.ALL_PLAYERS[i]
                break
        # determine right player
        i = index
        while True:
            i = (i + 1) % num_players
            if var.ALL_PLAYERS[i] in pl or var.ALL_PLAYERS[i] is user:
                target2 = var.ALL_PLAYERS[i]
                break

    return (target1, target2)

@event_listener("del_player")
def on_del_player(evt, var, player, all_roles, death_triggers):
    if not death_triggers or "mad scientist" not in all_roles:
        return

    target1, target2 = _get_targets(var, get_players(), player)

    prots1 = try_protection(var, target1, player, "mad scientist", "mad_scientist_fail")
    prots2 = try_protection(var, target2, player, "mad scientist", "mad_scientist_fail")
    if prots1:
        channels.Main.send(*prots1)
    if prots2:
        channels.Main.send(*prots2)

    kill1 = prots1 is None and add_dying(var, target1, killer_role="mad scientist", reason="mad_scientist")
    kill2 = prots2 is None and target1 is not target2 and add_dying(var, target2, killer_role="mad scientist", reason="mad_scientist")

    if kill1:
        if kill2:
            if var.ROLE_REVEAL in ("on", "team"):
                r1 = get_reveal_role(target1)
                an1 = "n" if r1.startswith(("a", "e", "i", "o", "u")) else ""
                r2 = get_reveal_role(target2)
                an2 = "n" if r2.startswith(("a", "e", "i", "o", "u")) else ""
                tmsg = messages["mad_scientist_kill"].format(player, target1, an1, r1, target2, an2, r2)
            else:
                tmsg = messages["mad_scientist_kill_no_reveal"].format(player, target1, target2)
            channels.Main.send(tmsg)
            debuglog(player.nick, "(mad scientist) KILL: {0} ({1}) - {2} ({3})".format(target1, get_main_role(target1), target2, get_main_role(target2)))
        else:
            if var.ROLE_REVEAL in ("on", "team"):
                r1 = get_reveal_role(target1)
                an1 = "n" if r1.startswith(("a", "e", "i", "o", "u")) else ""
                tmsg = messages["mad_scientist_kill_single"].format(player, target1, an1, r1)
            else:
                tmsg = messages["mad_scientist_kill_single_no_reveal"].format(player, target1)
            channels.Main.send(tmsg)
            debuglog(player.nick, "(mad scientist) KILL: {0} ({1})".format(target1, get_main_role(target1)))
    else:
        if kill2:
            if var.ROLE_REVEAL in ("on", "team"):
                r2 = get_reveal_role(target2)
                an2 = "n" if r2.startswith(("a", "e", "i", "o", "u")) else ""
                tmsg = messages["mad_scientist_kill_single"].format(player, target2, an2, r2)
            else:
                tmsg = messages["mad_scientist_kill_single_no_reveal"].format(player, target2)
            channels.Main.send(tmsg)
            debuglog(player.nick, "(mad scientist) KILL: {0} ({1})".format(target2, get_main_role(target2)))
        else:
            tmsg = messages["mad_scientist_fail"].format(player)
            channels.Main.send(tmsg)
            debuglog(player.nick, "(mad scientist) KILL FAIL")

@event_listener("transition_night_end", priority=2)
def on_transition_night_end(evt, var):
    for ms in get_all_players(("mad scientist",)):
        pl = get_players()
        target1, target2 = _get_targets(var, pl, ms)

        to_send = "mad_scientist_notify"
        if ms.prefers_simple():
            to_send = "mad_scientist_simple"
        ms.send(messages[to_send].format(target1, target2))

@event_listener("myrole")
def on_myrole(evt, var, user):
    if user in var.ROLES["mad scientist"]:
        pl = get_players()
        target1, target2 = _get_targets(var, pl, user)
        evt.data["messages"].append(messages["mad_scientist_myrole_targets"].format(target1, target2))

@event_listener("revealroles_role")
def on_revealroles(evt, var,  user, role):
    if role == "mad scientist":
        pl = get_players()
        target1, target2 = _get_targets(var, pl, user)
        evt.data["special_case"].append(messages["mad_scientist_revealroles_targets"].format(target1, target2))

@event_listener("get_role_metadata")
def on_get_role_metadata(evt, var, kind):
    if kind == "role_categories":
        evt.data["mad scientist"] = {"Village", "Cursed"}

# vim: set sw=4 expandtab:
