from functools import partial

from core.modifier import Modifier
from core.timeline import Listener, Timer
from conf import float_ceil, OPS, SELF
from core.log import log


class InactiveAbility(Exception):
    pass


### Conditions

CONDITIONS = {}


class Cond:
    def __init__(self, adv, data, *args) -> None:
        self._adv = adv
        self.event = None
        self.end_event = None
        self._extra_checks = []
        if cd := data.get("cd"):
            self._cooldown = Timer(timeout=cd - 0.0001)
            self._extra_checks.append(self.not_cooldown)
        if actcond := data.get("actcond"):
            self._actcond_id = actcond
            self._extra_checks.append(self.has_actcond)

    def not_cooldown(self):
        if not self._cooldown.online:
            self._cooldown.on()
            return True
        return False

    def has_actcond(self):
        return self._adv.active_actconds.stacks(self._actcond_id) > 0

    def extra_checks(self):
        return all((ec() for ec in self._extra_checks))

    def get(self):
        return 1

    def check(self, e):
        return True

    def end_check(self, e):
        return True

    def checked_get(self):
        return self.extra_checks() and self.get()

    def _checked_callback(self, callback, e):
        if self.extra_checks() and self.check(e):
            callback(e)

    def trigger(self, callback, order=1):
        if self.event is not None:
            return Listener(self.event, partial(self._checked_callback, callback), order=order)

    def _end_checked_callback(self, callback, e):
        if self.end_check(e):
            callback(e)

    def end_trigger(self, callback, order=1):
        if self.end_event is not None:
            return Listener(self.end_event, partial(self._end_checked_callback, callback), order=order)


class CondAlways(Cond):
    def __init__(self, adv, data, *args) -> None:
        super().__init__(adv, data, *args)
        self._extra_checks = []
        if cd := data.get("cd"):
            self._cooldown = Timer(timeout=cd - 0.0001, repeat=True)
        self._actcond_id = data.get("actcond")
        self._count = data.get("count", -1)
        self._can_trigger = bool(cd and (self._actcond_id or self._count))

    def _checked_callback(self, callback, e):
        if self._actcond_id is None or self.has_actcond() and self._count != 0:
            callback(e)
            if self._count > 0:
                self._count -= 1
        else:
            self._cooldown.off()

    def _activate(self, e):
        if e.actcond.id == self._actcond_id and SELF in e.actcond.generic_target:
            self._cooldown.on()
            self._cooldown.process(self._cooldown)

    def trigger(self, callback, order=1):
        if self._can_trigger:
            self._cooldown.process = partial(self._checked_callback, callback)
            if self._actcond_id is not None:
                self.l_actcond = Listener("actcond", self._activate, order=order)
            else:
                self._cooldown.name = "dauntless"
                self._cooldown.on()
            return None


CONDITIONS["always"] = CondAlways
CONDITIONS["dauntless"] = CondAlways


class CompareCond(Cond):
    def __init__(self, event, adv, data, *args) -> None:
        super().__init__(adv, data, *args)
        self._op = OPS[args[0]]
        self.value = args[1]
        self.event = event
        try:
            self.moment = bool(args[2])
        except IndexError:
            self.moment = False
        self.current_state = False

    def check(self, e):
        # check is true only when here is a change from current state
        new_state = self.get()
        result = self.current_state != new_state
        self.current_state = new_state
        return result


class CondHP(CompareCond):
    def __init__(self, adv, data, *args) -> None:
        super().__init__("hp", adv, data, *args)

    def get(self):
        return self._op(self._adv.hp, self.value)


CONDITIONS["hp"] = CondHP


class CondHits(CompareCond):
    def __init__(self, adv, data, *args) -> None:
        super().__init__("hits", adv, data, *args)

    def get(self):
        return self._op(self._adv.hits, self.value)


CONDITIONS["hits"] = CondHits


class CondActcond(CompareCond):
    def __init__(self, adv, data, *args) -> None:
        super().__init__("actcond", adv, data, *args[1:])
        self.actcond_id = args[0]

    def get(self):
        return self._op(self._adv.active_actconds.stacks(self.actcond_id), self.value)


CONDITIONS["actcond"] = CondActcond


class CondDragonShiftCount(CompareCond):
    def __init__(self, adv, data, *args) -> None:
        super().__init__("dragon", adv, data, *args)

    def get(self):
        return self._op((0 if self._adv.conf.c["utp"] else self._adv.dshift_count), self.value)


CONDITIONS["dshift_count"] = CondDragonShiftCount


class CondBuffedBy(Cond):
    def __init__(self, adv, data, *args) -> None:
        super().__init__(adv, data, *args)
        self.target = args[0]
        self.event = "s"

    def check(self, e):
        return e.base == self.target


CONDITIONS["buffed_by"] = CondBuffedBy


class CondInShift(Cond):
    def __init__(self, adv, data, *args) -> None:
        super().__init__(adv, data, *args)
        if args[0] == "dform":
            self.form_check = self._adv.dragonform.in_dform
            self.event = "dragon"
            self.end_event = "dragon_end"
        elif args[0] == "ddrive":
            self.form_check = self._adv.dragonform.in_ddrive
            self.event = "dragondrive"
            self.end_event = "dragondrive_end"
        self.count = args[1]

    def get(self):
        return self.form_check() and self._adv.dshift_count >= self.count


CONDITIONS["in_shift"] = CondInShift


class CondEvent(Cond):
    def __init__(self, adv, data, *args) -> None:
        super().__init__(adv, data, *args)
        self.event = args[0]


CONDITIONS["event"] = CondEvent


class CondPersistentCount(Cond):
    def __init__(self, event, adv, data, *args) -> None:
        super().__init__(adv, data, *args)
        self.event = event
        self.threshold = args[0]
        self.count = 0
        self.target = None
        if len(args) > 1:
            self.target = args[1]

    def check(self, e):
        if self.target is not None and not e.name.startswith(self.target):
            return False
        self.count += e.count
        if self.count < self.threshold:
            return False
        else:
            self.count -= self.threshold
            return True


class CondHitsEvent(CondPersistentCount):
    def __init__(self, adv, data, *args) -> None:
        super().__init__("hits", adv, data, *args)


CONDITIONS["hitcount"] = CondHitsEvent


class CondSlayer(CondPersistentCount):
    def __init__(self, adv, data, *args) -> None:
        super().__init__("slayer", adv, data, *args)


CONDITIONS["slayer"] = CondSlayer


class CondAffProc(Cond):
    def __init__(self, adv, data, *args) -> None:
        super().__init__(adv, data, *args)
        self.event = "aff"
        self.aff = args[0]

    def check(self, e):
        return e.atype == self.aff


CONDITIONS["aff"] = CondAffProc


class CondSelfAff(CondAffProc):
    def __init__(self, adv, data, *args) -> None:
        super().__init__(adv, data, *args)
        self.event = "selfaff"


CONDITIONS["selfaff"] = CondSelfAff


class CondMult(Cond):
    def __init__(self, adv, data, *args) -> None:
        super().__init__(adv, data, *args)
        self.value = args[0]
        self.threshold = args[1]
        self.max_count = args[2]

    def get(self):
        return min(self.max_count, getattr(self._adv, self.value, 0) // self.threshold)


CONDITIONS["mult"] = CondMult


class CondGetDP(Cond):
    def __init__(self, adv, data, *args) -> None:
        super().__init__(adv, data, *args)
        self.event = "dp"
        self.threshold = args[0]
        self.cache = 0

    def check(self, e):
        self.cache += e.value
        if self.cache > self.threshold:
            self.cache = self.cache % self.threshold
            return True
        return False


CONDITIONS["get_dp"] = CondGetDP


class CondDoublebuff(Cond):
    def __init__(self, adv, data, *args) -> None:
        super().__init__(adv, data, *args)
        self.event = "actcond"

    def check(self, e):
        if e.actcond.is_doublebuff:
            log("doublebuff", e.source[0])
        return e.actcond.is_doublebuff


CONDITIONS["doublebuff"] = CondDoublebuff


class CondFSHold(Cond):
    def __init__(self, adv, data, *args) -> None:
        self.required_time = args[0]
        if self.required_time == "cd":
            self.required_time = data["cd"]
            del data["cd"]
        super().__init__(adv, data, *args)
        self.event = args[1]

    def trigger(self, callback, order=1):

        fs_charging_timer = Timer(partial(self._checked_callback, callback), self.required_time - 0.00001, True)
        fs_charging_timer.name = "fs"
        Listener("fs_start", lambda _: fs_charging_timer.on())
        Listener(self.event, lambda _: fs_charging_timer.off())


CONDITIONS["fs_hold"] = CondFSHold


### Sub Abilities
SUB_ABILITIES = {}


class Ab:
    def __init__(self, adv, ability, *args) -> None:
        self._adv = adv
        self._ability = ability
        self._cond = ability.cond


class AbModifier(Ab):
    def __init__(self, adv, ability, value, mtype, morder) -> None:
        super().__init__(adv, ability)
        self.modifier = Modifier(mtype, morder, value, None if self._cond is None else self._cond.checked_get)


class AbMod(AbModifier):
    def __init__(self, adv, ability, *args) -> None:
        if len(args) == 3:
            super().__init__(adv, ability, args[0], args[1], args[2].replace("-t:", ""))
        else:
            super().__init__(adv, ability, args[0], args[1], "passive")


SUB_ABILITIES["mod"] = AbMod


class AbActdmg(AbModifier):
    def __init__(self, adv, ability, *args) -> None:
        self.target = args[1].replace("-t:", "")
        if len(args) == 3:
            super().__init__(adv, ability, args[0], self.target, args[2])
        else:
            super().__init__(adv, ability, args[0], self.target, "passive")


SUB_ABILITIES["actdmg"] = AbActdmg


class AbCtime(AbModifier):
    def __init__(self, adv, ability, *args) -> None:
        super().__init__(adv, ability, args[0], "ctime", "passive")


SUB_ABILITIES["ctime"] = AbCtime


class AbActcond(Ab):
    def __init__(self, adv, ability, *args) -> None:
        super().__init__(adv, ability)
        self.target = args[0]
        self.actcond_list = args[1:4]
        self.max_count = ability.data.get("count")
        self.count = 0
        self.idx = 0
        self.l_cond = None
        if self._cond is not None:
            self.l_cond = self._cond.trigger(self._actcond_on)
            self.l_end_cond = self._cond.end_trigger(self._actcond_off)
        self.actcond = None

    def _actcond_on(self, e):
        if e.name == "actcond":
            source = (e.source[0], None) or ("ability", None)
            dtype = e.dtype or "#"
        else:
            source = ("ability", None)
            dtype = "#"
        self.actcond = self._adv.actcond_make(self.actcond_list[self.idx], self.target, source, dtype=dtype, ev=getattr(e, "ev", 1))
        self.idx = (self.idx + 1) % len(self.actcond_list)
        if self.max_count is not None:
            self.count += 1
            if self.count >= self.max_count and self.l_cond is not None:
                self.l_cond.off()

    def _actcond_off(self, e):
        self.actcond.off()


SUB_ABILITIES["actcond"] = AbActcond


class AbHitattr(Ab):
    def __init__(self, adv, ability, *args) -> None:
        super().__init__(adv, ability)
        self.hitattrs = args
        self.max_count = ability.data.get("count")
        self.count = 0
        self.l_cond = None
        if self._cond is not None:
            self.l_cond = self._cond.trigger(self._actcond_on)

    def _actcond_on(self, e):
        for aseq, hitattr in enumerate(self.hitattrs):
            self._adv.hitattr_make("ab", "ab", "default", aseq, hitattr, ev=getattr(e, "ev", 1))
        if self.max_count is not None:
            self.count += 1
            if self.count >= self.max_count:
                self.l_cond.off()


SUB_ABILITIES["hitattr"] = AbHitattr


class AbDragonPrep(Ab):
    def __init__(self, adv, ability, *args) -> None:
        super().__init__(adv, ability, *args)
        self.value = args[0]
        if self._cond is not None:
            self.l_cond = self._cond.trigger(self._dprep)

    def _dprep(self, e):
        self._adv.dragonform.charge_dprep(self.value)


SUB_ABILITIES["dprep"] = AbDragonPrep


class AbDragonPrepCap(Ab):
    def __init__(self, adv, ability, *args) -> None:
        super().__init__(adv, ability, *args)
        self.value = args[0]
        if self._cond is not None:
            self.l_cond = self._cond.trigger(self._dprep_max, order=2)

    def _dprep_max(self, e):
        self._adv.dragonform.dragon_gauge = min(float_ceil(self._adv.dragonform.max_dragon_gauge, self.value), self._adv.dragonform.dragon_gauge)


SUB_ABILITIES["dprep_cap"] = AbDragonPrepCap


class AbHitattrShift(Ab):
    def __init__(self, adv, ability, *args) -> None:
        super().__init__(adv, ability, *args)
        if self._cond is not None:
            self.l_cond = self._cond.trigger(self._set_has, order=2)

    def _set_has(self, e):
        self._adv.hitattr_shift = 1
        if self._cond is not None:
            self.l_cond.off()


SUB_ABILITIES["hitattr_shift"] = AbHitattrShift


class AbActGrant(Ab):
    def __init__(self, adv, ability, *args) -> None:
        super().__init__(adv, ability, *args)
        self.actcond_id = args[0]
        self.action = args[1].replace("-t:", "")
        self.l_act = Listener(self.action, self._grant_actcond, order=2)
        self.actcond = None

    def _grant_actcond(self, e=None):
        if not self._cond or self._cond.checked_get():
            self.actcond = self._adv.actcond_make(self.actcond_id, "HOSTILE", ("actgrant", None), dtype=self.action)


SUB_ABILITIES["actgrant"] = AbActGrant

### Ability
class Ability:
    def __init__(self, adv, data, use_limit=False):
        self._adv = adv
        self.cond = None
        self.data = data
        if cond := data.get("cond"):
            try:
                self.cond = CONDITIONS[cond[0]](adv, data, *cond[1:])
            except KeyError:
                print(cond)
                self.cond = None
        self.abs = []
        if ab_lst := data.get("ab"):
            for ab in ab_lst:
                try:
                    sub_ab = SUB_ABILITIES[ab[0]](adv, self, *ab[1:])
                except KeyError:
                    continue
                if use_limit and isinstance(sub_ab, AbModifier):
                    sub_ab.modifier.limit_group = data.get("lg")
                self.abs.append(sub_ab)


def make_ability(adv, data, use_limit=False):
    if not data.get("ele", adv.slots.c.ele) == adv.slots.c.ele or not data.get("wt", adv.slots.c.wt) == adv.slots.c.wt:
        return None
    return Ability(adv, data, use_limit=use_limit)
