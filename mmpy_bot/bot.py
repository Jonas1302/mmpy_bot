# -*- coding: utf-8 -*-

from __future__ import absolute_import

import imp
import importlib
import logging
import os
import re
import time
from glob import glob

from six.moves import _thread

from mmpy_bot.settings import default_settings
from mmpy_bot.dispatcher import MessageDispatcher
from mmpy_bot.mattermost import MattermostClient
from mmpy_bot.scheduler import schedule

logger = logging.getLogger(__name__)


class Bot(object):
    def __init__(self, settings=None):
        self._settings = default_settings
        if settings:
            self._settings.update(settings)
        
        if settings["MATTERMOST_API_VERSION"] < 4:
            raise ValueError('mmpy-bot only supports API Version 4+')
        self._client = MattermostClient(
            self._settings["BOT_URL"], self._settings["BOT_TEAM"],
            self._settings["BOT_LOGIN"], self._settings["BOT_PASSWORD"],
            self._settings["SSL_VERIFY"], self._settings["BOT_TOKEN"],
            self._settings["WS_ORIGIN"])
        logger.info('connected to mattermost')
        self._plugins = PluginsManager()
        self._dispatcher = MessageDispatcher(self._client, self._plugins, self._settings)

    def run(self):
        self._plugins.init_plugins()
        self._plugins.trigger_at_start(self._client)
        self._dispatcher.start()
        _thread.start_new_thread(self._keep_active, tuple())
        _thread.start_new_thread(self._run_jobs, tuple())
        self._dispatcher.loop()

    def _keep_active(self):
        logger.info('keep active thread started')
        while True:
            time.sleep(60)
            self._client.ping()

    def _run_jobs(self):
        logger.info('job running thread started')
        while True:
            time.sleep(self._settings["JOB_TRIGGER_PERIOD"])
            schedule.run_pending()


class PluginsManager(object):
    commands = {
        'respond_to': {},
        'listen_to': {},
        'post_edited': {},
        'post_deleted': {},
        'reaction_added': {},
        'reaction_removed': {},
    }
    _at_start = []

    def __init__(self, plugins=None):
        self.plugins = plugins or []

    def init_plugins(self):
        if self.plugins == []:
            if 'PLUGINS' in self._settings:
                self.plugins = self._settings["PLUGINS"]
            if self.plugins == []:
                self.plugins.append('mmpy_bot.plugins')

        for plugin in self.plugins:
            self._load_plugins(plugin)

    @staticmethod
    def _load_plugins(plugin):
        logger.info('loading plugin "%s"', plugin)
        path_name = None
        # try to load root package as module first
        PluginsManager._load_module(plugin)
        # load modules in this plugin package
        for mod in plugin.split('.'):
            if path_name is not None:
                path_name = [path_name]
            _, path_name, _ = imp.find_module(mod, path_name)
        for py_file in glob('{}/[!_]*.py'.format(path_name)):
            module = '.'.join((plugin, os.path.split(py_file)[-1][:-3]))
            PluginsManager._load_module(module)

    @staticmethod
    def _load_module(module):
        try:
            _module = importlib.import_module(module)
            if hasattr(_module, 'on_init'):
                _module.on_init()
        except Exception as err:
            logger.exception(err)

    def get_plugins(self, category, text):
        has_matching_plugin = False
        for matcher in self.commands[category]:
            m = matcher.regex.search(text)
            if m:
                has_matching_plugin = True
                yield self.commands[category][matcher], m.groups()

        if not has_matching_plugin:
            yield None, None

    def trigger_at_start(self, client):
        for func in self._at_start:
            try:
                func(client)
            except Exception as err:
                logger.exception(err)


class Matcher(object):
    """This allows us to map the same regex to multiple handlers."""
    def __init__(self, regex):
        self.regex = regex


def get_wrapper(wrapper_type, regexp, flags=0):
    def wrapper(func):
        m = Matcher(re.compile(regexp, flags))
        PluginsManager.commands[wrapper_type][m] = func
        logger.info(
            'registered %s plugin "%s" to "%s"',
            wrapper_type, func.__name__, regexp)
        return func

    return wrapper


def respond_to(regexp, flags=0):
    return get_wrapper('respond_to', regexp, flags)


def listen_to(regexp, flags=0):
    return get_wrapper('listen_to', regexp, flags)


def post_edited(regexp, flags=0):
    return get_wrapper('post_edited', regexp, flags)


def post_deleted(regexp, flags=0):
    return get_wrapper('post_deleted', regexp, flags)


def reaction_added(regexp, flags=0):
    return get_wrapper('reaction_added', regexp, flags)


def reaction_removed(regexp, flags=0):
    return get_wrapper('reaction_removed', regexp, flags)

def at_start():
    def wrapper(func):
        PluginsManager._at_start.append(func)
        logger.info(
            'registered %s plugin "%s"',
            "at_start", func.__name__)
        return func

    return wrapper

