import json
import os
import glob

from core import Conf
import functools

ELEMENTS = ("flame", "water", "wind", "light", "shadow")
WEAPON_TYPES = (
    "sword",
    "blade",
    "dagger",
    "axe",
    "lance",
    "bow",
    "wand",
    "staff",
    "gun",
)
TRIBE_TYPES = (
    "thaumian",
    "physian",
    "demihuman",
    "therion",
    "undead",
    "demon",
    "human",
    "dragon",
)
DURATIONS = (180,)
ELE_AFFLICT = {
    "flame": ("burn", "scorchrend"),
    "water": ("frostbite",),  # sadness
    "wind": ("poison", "stormlash"),
    "light": ("paralysis", "flashburn"),
    "shadow": ("poison", "shadowblight"),
}
SKIP_VARIANT = ("RNG", "mass")
DRG = "drg"
DEFAULT = "default"
DDRIVE = "ddrive"

ROOT_DIR = os.getenv("ROOT_DIR", os.path.realpath(os.path.join(__file__, "../..")))


def get_conf_json_path(fn):
    froot = os.path.join(ROOT_DIR, "conf")
    return os.path.join(froot, fn)


def save_json(fn, data, indent=None):
    fpath = get_conf_json_path(fn)
    with open(fpath, "w", encoding="utf8") as f:
        return json.dump(data, f, ensure_ascii=False, default=str, indent=indent)


def load_json(fn, fuzzy=False):
    fpath = get_conf_json_path(fn)
    if fuzzy:
        fpath = glob.glob(fpath)[0]
    with open(fpath, "r", encoding="utf8") as f:
        return json.load(f, parse_float=float, parse_int=int)


wyrmprints = load_json("wyrmprints.json")
# weapons = load_json('weapons.json')

baseconfs = {}
weapons = {}
for wep in WEAPON_TYPES:
    baseconfs[wep] = load_json(f"base/{wep}.json")
    weapons[wep] = load_json(f"wep/{wep}.json")


@functools.cache
def load_adv_json(adv):
    return load_json(f"adv/*/{adv}.json", fuzzy=True)


@functools.cache
def load_drg_json(drg):
    return load_json(f"drg/*/{drg}.json", fuzzy=True)


def load_drg_by_element(ele):
    for fn in sorted(os.listdir(os.path.join(ROOT_DIR, "conf", "drg"))):
        fn, ext = os.path.splitext(fn)
        if ext != ".json":
            continue
        conf = load_drg_json(fn)
        if conf["d"]["ele"] == ele:
            yield fn, conf


def get_icon(adv):
    try:
        return load_adv_json(adv)["c"]["icon"]
    except (FileNotFoundError, KeyError):
        return ""


def get_fullname(adv):
    try:
        return load_adv_json(adv)["c"]["name"]
    except (FileNotFoundError, KeyError):
        return adv


def get_adv(name):
    conf = Conf(load_adv_json(name))

    wt = conf.c.wt
    base = baseconfs[wt]
    baseconf = Conf(base)

    if bool(conf.c.spiral):
        baseconf.update(baseconf.lv2)
    del baseconf["lv2"]

    if wt == "gun" and len(conf.c.gun) == 1:
        # move gun[n] to base combo
        target = conf.c.gun[0]
        for xn, xconf in list(baseconf.find(r"^(x\d|fsf?)_gun\d$")):
            if int(xn[-1]) == target:
                baseconf[xn.split("_")[0]] = xconf
            del baseconf[xn]
        # ban fsf on gun2
        if conf.c.gun[0] == 2:
            baseconf.cannot_fsf = True

    conf.update(baseconf, rebase=True)

    return conf


def all_subclasses(cl):
    return set(cl.__subclasses__()).union([s for c in cl.__subclasses__() for s in all_subclasses(c)])


def subclass_dict(cl):
    return {sub_class.__name__: sub_class for sub_class in all_subclasses(cl)}


def list_advs():
    for fn in sorted(os.listdir(os.path.join(ROOT_DIR, "conf", "adv"))):
        fn, ext = os.path.splitext(fn)
        if ext != ".json":
            continue
        yield fn
