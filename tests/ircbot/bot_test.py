import unittest

import botologist.irc as irc
import botologist.bot as bot


class CommandMessageTest(unittest.TestCase):
	def test_commands_and_args_are_parsed(self):
		msg = irc.Message('nick!ident@host.com', '#channel', '!foo bar baz')
		cmd = bot.CommandMessage(msg)
		self.assertEqual('!foo', cmd.command)
		self.assertEqual(['bar', 'baz'], cmd.args)
