from pedal.cait.cait_api import *
from pedal.report.imperative import *


def filter_group():
    missing_if_in_for()
    append_not_in_if()


def missing_if_in_for():
    """
    Name: missing_if_in_for
    Pattern:
    missing
    for <item> in ___ :
        if ...<item> ... :

    Feedback: The arrangement of decision and iteration is not correct for the filter pattern.

    :return:
    """
    matches = find_matches("for _item_ in ___:\n"
                           "    if __expr__:\n"
                           "        pass")
    if matches:
        for match in matches:
            _item_ = match.symbol_table.get("_item_")[0].astNode
            __expr__ = match.exp_table.get("__expr__")
            if __expr__.has(_item_):
                return False
    explain("The arrangement of decision and iteration is not correct for the filter pattern.<br><br><i>"
            "(missing_if_in_for)<i></br>")
    return True


def append_not_in_if():
    """
    Name: append_not_in_if
    Pattern:
    missing
    if ... :
       ___.append(___)

    Feedback: Only items satisfying some condition should be appended to the list.

    :return:
    """
    match = find_match("if ___:\n"
                       "    ___.append(___)")
    if not match:
        explain(
            "Only items satisfying some condition should be appended to the list.<br><br><i>(app_not_in_if)<i></br>")
        return True
    return False
