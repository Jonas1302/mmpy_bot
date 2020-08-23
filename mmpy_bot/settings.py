default_settings = {
	"DEBUG": False,
	"PLUGINS": [
		'mmpy_bot.plugins',
	],
	"PLUGINS_ONLY_DOC_STRING": False,

	"MATTERMOST_API_VERSION": 4,
	"BOT_URL": 'http://mm.example.com/api/v4',
	"BOT_LOGIN": 'bot@example.com',
	"BOT_PASSWORD": None,
	"BOT_TOKEN": None,
	"BOT_TEAM": 'devops',
	"SSL_VERIFY": True,
	"WS_ORIGIN": None,
	"WEBHOOK_ID": None,  # if not specified mmpy_bot will attempt to create one
	
	"IGNORE_NOTIFIES": ['@here', '@channel', '@all'],
	"IGNORE_USERS": [],
	"WORKERS_NUM": 10,
	
	"DEFAULT_REPLY_MODULE": None,
	"DEFAULT_REPLY": None,

	"""
	If you use Mattermost Web API to send messages (with send_webapi()
	or reply_webapi()), you can customize the bot logo by providing Icon or Emoji.
	If you use Mattermost API to send messages (with send() or reply()),
	the used icon comes from bot settings and Icon or Emoji has no effect.
	"""
	# BOT_ICON = 'http://lorempixel.com/64/64/abstract/7/'
	# BOT_EMOJI = ':godmode:'
	
	"""
	Period to trigger jobs in sechduler. Measures in seconds.
	If JOB_TRIGGER_PERIOD is not set, mmpy_bot will set default priod 5 seconds.
	"""
	"JOB_TRIGGER_PERIOD": 5
}
