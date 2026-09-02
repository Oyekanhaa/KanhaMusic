# -----------------------------------------------
# 🔸 VampireMusic Project
# 🔹 Developed & Maintained by: Vampire Bots (https://github.com/TEAM-VAMPIRE-OP)
# 📅 Copyright © 2025 – All Rights Reserved
#
# 📖 License:
# This source code is open for educational and non-commercial use ONLY.
# You are required to retain this credit in all copies or substantial portions of this file.
# Commercial use, redistribution, or removal of this notice is strictly prohibited
# without prior written permission from the author.
#
# ❤️ Made with dedication and love by TEAM-VAMPIRE-OP
# -----------------------------------------------


from typing import Union
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from VampireMusic import app


def help_pannel(_, START: Union[bool, int] = None):
    first = [InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data=f"close")]
    second = [
        InlineKeyboardButton(
            text=_["BACK_BUTTON"],
            callback_data=f"settingsback_helper",
        ),
    ]
    mark = second if START else first
    upl = InlineKeyboardMarkup(
        [
	    [
	        InlineKeyboardButton(
                    text=_["H_B_34"],
                    callback_data="help_callback hb10",
		)
	    ],    
            [
                InlineKeyboardButton(
                    text=_["H_B_25"],
                    callback_data="help_callback hb1",
                ),
                InlineKeyboardButton(
                    text=_["H_B_26"],
                    callback_data="help_callback hb2",
                ),
                InlineKeyboardButton(
                    text=_["H_B_28"],
                    callback_data="help_callback hb3",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_["H_B_27"],
                    callback_data="help_callback hb4",
                ),
                InlineKeyboardButton(
                    text=_["H_B_31"],
                    callback_data="help_callback hb5",
                ),
                InlineKeyboardButton(
                    text=_["H_B_29"],
                    callback_data="help_callback hb6",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_["H_B_33"],
                    callback_data="help_callback hb7",
                ),
                InlineKeyboardButton(
                    text=_["H_B_30"],
                    callback_data="help_callback hb8",
                ),
                InlineKeyboardButton(
                    text=_["H_B_32"],
                    callback_data="help_callback hb9",
                ),
            ],
            mark,
        ]
    )
    return upl

def help_back_markup(_):
	upl = InlineKeyboardMarkup([[InlineKeyboardButton(text=_["BACK_BUTTON"], callback_data=f"settings_back_helper")]])
	return upl

def private_help_panel(_):
	buttons = [[InlineKeyboardButton(text=_["S_B_4"], url=f"https://t.me/{app.username}?start=help")]]
	return buttons
