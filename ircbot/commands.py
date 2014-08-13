from ircbot.streams import get_online_streams, add_stream, sub_stream, list_user_subs, \
                           StreamNotFoundException, AlreadySubscribedException
from ircbot.web import get_google_result


def streams(bot, args, user):
	streams = get_online_streams(bot)

	if streams is None:
		return None
	elif streams:
		return 'Online streams: ' + ' -- '.join([stream.url for stream in streams])
	else:
		return 'No streams online!'


def addstream(bot, args, user):
	if len(args) < 1:
		return

	if add_stream(args[0], bot):
		return 'Stream added!'
	else:
		return 'Stream could not be added.'


def sub(bot, args, user):
	if len(args) > 0:
		try:
			sub_stream(bot, user, args[0])
			return 'You ('+user+') are now subscribed!'
		except StreamNotFoundException:
			return 'That stream has not been added.'
		except AlreadySubscribedException:
			return 'Already subscribed to ' + args[0]
	else:
		streams = list_user_subs(bot, user)
		if streams:
			return 'You ('+user+') are subscribed to: ' + ', '.join(streams)
		else:
			return 'You ('+user+') are not subscribed to any streams.'

def g(bot, args, user):
	result = get_google_result(args)

	if result:
		return result
