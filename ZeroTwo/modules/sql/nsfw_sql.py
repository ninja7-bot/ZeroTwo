import threading

from sqlalchemy import Column, String, UnicodeText, Integer

from ZeroTwo.modules.sql import SESSION, BASE

class NSFWSettings(BASE):
    __tablename__ = "nsfw_settings"
    chat_id = Column(String(14), primary_key=True)
    nsfw_type = Column(Integer, default=1)
    value = Column(UnicodeText, default="0")

    def __init__(self, chat_id, nsfw_type=1, value="0"):
        self.chat_id = str(chat_id)
        self.nsfw_type = nsfw_type
        self.value = value

    def __repr__(self):
        return "<{} will execute {} for any NSFW media.>".format(
            self.chat_id,
            self.nsfw_type,
        )


NSFWSettings.__table__.create(checkfirst=True)
NSFW_SETTINGS_INSERTION_LOCK = threading.RLock()
CHAT_SETTINGS_NSFW = {}

def set_nsfw_strength(chat_id, nsfw_type, value):
    # for nsfw_type
    # 0 = nothing
    # 1 = ban
    # 2 = warn
    # 3 = mute
    # 4 = kick
    # 5 = tban
    # 6 = tmute
    with NSFW_SETTINGS_INSERTION_LOCK:
        global CHAT_SETTINGS_NSFW
        curr_setting = SESSION.query(NSFWSettings).get(str(chat_id))
        if not curr_setting:
            curr_setting = NSFWSettings(
                chat_id,
                nsfw_type=int(nsfw_type),
                value=value,
            )

        curr_setting.nsfw_type = int(nsfw_type)
        curr_setting.value = str(value)
        CHAT_SETTINGS_NSFW[str(chat_id)] = {
            "nsfw_type": int(nsfw_type),
            "value": value,
        }

        SESSION.add(curr_setting)
        SESSION.commit()


def get_nsfw_setting(chat_id):
    try:
        setting = CHAT_SETTINGS_NSFW.get(str(chat_id))
        if setting:
            return setting["nsfw_type"], setting["value"]
        return 1, "0"

    finally:
        SESSION.close()
