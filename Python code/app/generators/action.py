from enum import Enum
from collections import defaultdict
import json

class TabletActions(str, Enum):

    def __new__(cls, value, is_background_action):
        member = str.__new__(cls, value)
        member._value_ = value
        member.is_background_action = is_background_action
        return member

    sleep_report_action_bad = "sleep-report-action-bad", True
    sleep_report_action_okay = "sleep-report-action-okay", True
    sleep_report_action_good = "sleep-report-action-good", True
    sleep_report_action_very_good = "sleep-report-action-very-good", True
    meal_report_action_yes = "meal-report-action-yes", True
    meal_report_action_no = "meal-report-action-no", True
    medication_report_action_yes = "medication-report-action-yes", True
    medication_report_action_no = "medication-report-action-no", True
    mood_report_action_bad = "mood-report-action-bad", True
    mood_report_action_okay = "mood-report-action-okay", True
    mood_report_action_good = "mood-report-action-good", True
    mood_report_action_very_good = "mood-report-action-very-good", True
    activity_report_action_yes = "activity-report-action-yes", True
    activity_report_action_no = "activity-report-action-no", True
    screen_action_show_breathing_exercise = "screen-action-show-breathing-exercise", False
    screen_action_show_dialogue_screen = "screen-action-show-dialogue-screen", False
    screen_action_show_home_screen = "screen-action-show-home-screen", False
    def __str__(self):
        return str(self.value).lower()


async def queue_tablet_actions(action_keys: dict, tablet_id: str, controller):
    for action, args in action_keys.items():
        if action == TabletActions.sleep_report_action_bad:
            controller._parent_app.add_background_task(controller.send_sleep_report, tablet_id=tablet_id,
                                                       response=json.dumps({"value": "1", "followUp": {"text": "Report", "value": args}}))  # you can add a follow up to this response
        elif action == TabletActions.sleep_report_action_okay:
            controller._parent_app.add_background_task(controller.send_sleep_report, tablet_id=tablet_id,
                                                       response=json.dumps({"value": "2", "followUp": {"text": "Report", "value": args}}))  # you can add a follow up to this response
        elif action == TabletActions.sleep_report_action_good:
            controller._parent_app.add_background_task(controller.send_sleep_report, tablet_id=tablet_id,
                                                       response=json.dumps({"value": "3", "followUp": {"text": "Report", "value": args}}))  # you can add a follow up to this response
        elif action == TabletActions.sleep_report_action_very_good:
            controller._parent_app.add_background_task(controller.send_sleep_report, tablet_id=tablet_id,
                                                       response=json.dumps({"value": "4", "followUp": {"text": "Report", "value": args}}))  # you can add a follow up to this response
        elif action == TabletActions.meal_report_action_yes:
            controller._parent_app.add_background_task(controller.send_meal_report, tablet_id=tablet_id,
                                                       response=json.dumps({"value": "1", "followUp": {"text": "Report", "value": args}}))  # you can add a follow up to this response
        elif action == TabletActions.meal_report_action_no:
            controller._parent_app.add_background_task(controller.send_meal_report, tablet_id=tablet_id,
                                                       response=json.dumps({"value": "0", "followUp": {"text": "Report", "value": args}}))  # you can add a follow up to this response
        elif action == TabletActions.medication_report_action_yes:
            controller._parent_app.add_background_task(controller.send_medication_report, tablet_id=tablet_id,
                                                       response=json.dumps({"value": "1", "followUp": {"text": "Report", "value": args}}))  # you can add a follow up to this response
        elif action == TabletActions.medication_report_action_no:
            controller._parent_app.add_background_task(controller.send_medication_report, tablet_id=tablet_id,
                                                       response=json.dumps({"value": "0", "followUp": {"text": "Report", "value": args}}))  # you can add a follow up to this response
        elif action == TabletActions.mood_report_action_bad:
            controller._parent_app.add_background_task(controller.send_mood_report, tablet_id=tablet_id,
                                                       response=json.dumps({"value": "1", "followUp": {"text": "Report", "value": args}}))  # you can add a follow up to this response
        elif action == TabletActions.mood_report_action_okay:
            controller._parent_app.add_background_task(controller.send_mood_report, tablet_id=tablet_id,
                                                       response=json.dumps({"value": "2", "followUp": {"text": "Report", "value": args}}))  # you can add a follow up to this response
        elif action == TabletActions.mood_report_action_good:
            controller._parent_app.add_background_task(controller.send_mood_report, tablet_id=tablet_id,
                                                       response=json.dumps({"value": "3", "followUp": {"text": "Report", "value": args}}))  # you can add a follow up to this response
        elif action == TabletActions.mood_report_action_very_good:
            controller._parent_app.add_background_task(controller.send_mood_report, tablet_id=tablet_id,
                                                       response=json.dumps({"value": "4", "followUp": {"text": "Report", "value": args}}))  # you can add a follow up to this response
        elif action == TabletActions.activity_report_action_yes:
            controller._parent_app.add_background_task(controller.send_activity_report, tablet_id=tablet_id,
                                                       response=json.dumps({"value": "1", "followUp": {"text": "Report", "value": args}}))  # you can add a follow up to this response
        elif action == TabletActions.activity_report_action_no:
            controller._parent_app.add_background_task(controller.send_activity_report, tablet_id=tablet_id,
                                                       response=json.dumps({"value": "0", "followUp": {"text": "Report", "value": args}}))  # you can add a follow up to this response

        elif action == TabletActions.screen_action_show_breathing_exercise:
            controller._parent_app.add_background_task(controller.show_video, tablet_id=tablet_id,
                                                       title='Breathing exercise',
                                                       url='https://player.vimeo.com/video/867906624')

        elif action == TabletActions.screen_action_show_dialogue_screen:
            controller._parent_app.add_background_task(controller.show_dialogue_screen, tablet_id=tablet_id)

        elif action == TabletActions.screen_action_show_home_screen:
            controller._parent_app.add_background_task(controller.show_home_screen, tablet_id=tablet_id)