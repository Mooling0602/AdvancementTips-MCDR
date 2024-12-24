import os
try:
    import json5, json # type: ignore
    json_module = lambda *args, **kwargs: (json5(*args, **kwargs))
except ModuleNotFoundError:
    import json
    json_module = lambda *args, **kwargs: (json(*args, **kwargs))

from mcdreforged.api.all import *

psi = ServerInterface.psi()


MCDRConfig = psi.get_mcdr_config()
plgSelf = psi.get_self_metadata()
serverDir = MCDRConfig["working_directory"]

geyser_config = {
    "tr_lang": f"{serverDir}/plugins/Geyser-Spigot/locales/zh_cn.json",
    "use_json5": False
}

default_config = {
    "tr_lang": "zh_cn.json",
    "use_json5": False
}

def tr(tr_key):
    raw = psi.rtr(f"{plgSelf.id}.{tr_key}")
    return str(raw)

def send(text: str):
    try:
        from matrix_sync.commands import matrix_reporter
        matrix_reporter(text)
        psi.logger.info("Found MSync, sending message to Matrix...")
    except ModuleNotFoundError:
        psi.logger.info(text)


def on_load(server: PluginServerInterface, prev_module):
    global tr_lang, tr_langRegion
    if os.path.exists(geyser_config["tr_lang"]):
        config = server.load_config_simple('config.json', geyser_config)
    else:
        config = server.load_config_simple('config.json', default_config)
    tr_lang_path = config["tr_lang"]
    if os.path.exists(tr_lang_path):
        try:
            with open(f'{tr_lang_path}', 'r', encoding='utf-8') as f:
                if config["use_json5"]:
                    tr_lang = json_module.load(f)
                else:
                    tr_lang = json.load(f)
        except UnicodeDecodeError:
            with open(f'{tr_lang_path}', 'r', encoding='gbk') as f:
                if config["use_json5"]:
                    tr_lang = json_module.load(f)
                else:
                    tr_lang = json.load(f)
        tr_langRegion = os.path.splitext(os.path.basename(tr_lang_path))[0]
        server.register_event_listener("PlayerAdvancementEvent", on_player_advancement)
    else:
        server.logger.error("No lang file in given path, please reload plugin after configured correctly!")
        server.unload_plugin(plgSelf.id)

def on_player_advancement(server, player, event, content):
    from mg_events.config import lang # type: ignore
    if tr_langRegion != content.lang:
        psi.logger.info("detected advancement message.")
        raw = tr_lang.get(event, None)
        replacements = [player, content.advancement]
        tip = raw
        for replacement in replacements:
            tip = tip.replace('%s', str(replacement), 1)
        if lang is not None:
            for key, value in lang.items():
                if value == content.advancement.replace('[', '').replace(']', ''):
                    content_key = key
        else:
            server.logger.info("Loaded lang from upstream seems error!")
        try:
            advancement = tr_lang.get(content_key, None)
        except UnboundLocalError:
            advancement = None
        if advancement is not None:
            tip = tip.replace(content.advancement, f"[{advancement}]")
        send(tip)