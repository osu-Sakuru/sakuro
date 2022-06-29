#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
import os

import discord

from objects.sakuro import Sakuro

__all__ = ()

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    intents.messages = True

    Sakuro(intents=intents).run()
