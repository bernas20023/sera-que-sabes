#! py -3.7
from kivy.config import Config

Config.set('graphics', 'width', '405')
Config.set('graphics', 'height', '720')
Config.set('graphics', 'resizable', True)

import json
import random as rd
import kvimports as kv


class Root(kv.Carousel):
	"""Kivy properties go here"""

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		""""""


class PlayerBox(kv.BoxLayout):
	player_name = kv.StringProperty()
	medals_layout = kv.ObjectProperty()

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		player_ti = PlayerTextInput()
		self.add_widget(player_ti)
		self.bind(player_name=player_ti.setter("text"))

		self.medals_layout = kv.BoxLayout(padding="10dp", spacing="10dp")
		self.add_widget(self.medals_layout)
		for category in app.questions.categories:
			medal = MedalCheckbox()
			medal.category = category
			app.reset_on_win.append(medal)
			self.medals_layout.add_widget(medal)

	def check_win(self):
		if all([medal.state == "down" for medal in self.medals_layout.children]):
			app.reset_game()
			sound = kv.SoundLoader().load("./Win/win_sound.mp3")
			sound.volume = 0.3
			sound.play()
			WinPopup(title=f"Parabéns {self.player_name}!").open()


class WinPopup(kv.Popup):
	pass


class PlayerTextInput(kv.TextInput):
	pass


class MedalCheckbox(kv.ToggleButtonBehavior, kv.Image):
	category = kv.StringProperty()

	def on_state(self, _, state):
		if state == "normal":
			self.source = "./medal_checkbox_normal.png"
		else:
			self.source = "./medal_checkbox_down.png"

		self.parent.parent.check_win()


class QuestionButton(kv.Button):
	category = kv.StringProperty()

	def __init__(self, category="", **kwargs):
		super().__init__(**kwargs)
		self.category = category
		app.bind(questions=lambda *_: setattr(self, "disabled", False))

	def on_release(self):
		if app.questions.questions_left(self.category) <= 1:
			self.disabled = True
		popup = kv.ModalView(size_hint=(7/8, 2/5))
		popup.background = ""
		popup.background_color = (0, 0, 0, 0)
		popup.add_widget(QuestionCard(self.category))
		popup.open()


class QuestionCard(kv.ButtonBehavior, kv.BoxLayout):
	category = kv.StringProperty()
	displaying_question = kv.BooleanProperty()
	question = kv.StringProperty()
	answer = kv.StringProperty()
	angle = kv.NumericProperty()
	qa_label = kv.ObjectProperty()
	text_label = kv.ObjectProperty()
	icon_image = kv.ObjectProperty()

	def __init__(self, category="", **kwargs):
		super().__init__(**kwargs)
		self.category = category
		self.icon_image.source = "Questions/Icons/" + self.category + ".png"
		self.question, self.answer = app.questions.pop_question(category)
		self.displaying_question = True
		self.flip_anim = kv.Animation(angle=180, duration=0.3)
		self.flip_anim.bind(on_complete=self.restitute_content)

	def flip_card(self):
		self.angle = 0
		self.flip_anim.start(self)
		self.icon_image.opacity = 0
		self.text_label.text = ""
		self.qa_label.text = ""
		self.displaying_question = not self.displaying_question

	def restitute_content(self, *args):
		self.icon_image.opacity = 1
		if self.displaying_question:
			self.text_label.text = self.question
			self.qa_label.text = "Pergunta"
		else:
			self.text_label.text = self.answer
			self.qa_label.text = "Resposta"


class DiceButton(kv.Button):
	angle = kv.NumericProperty()
	dice_image = kv.ObjectProperty()

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.replace_anim = None
		self.anim_duration = 1
		self.rot_anim = kv.Animation(angle=720, duration=self.anim_duration * 1.2)
		self.roll_sound = kv.SoundLoader.load("./Dice/sound.wav")

	def on_release(self):
		if self.replace_anim is not None:
			self.replace_anim.cancel()
		roll = rd.randrange(1, 7)
		self.replace_anim = kv.Clock.schedule_once(lambda _: setattr(
			self.dice_image,
			"source",
			f"./Dice/{roll}.png"), 1)
		self.dice_image.anim_delay = 0.15
		self.dice_image.source = "./Dice/animation.zip"
		self.angle = 0
		self.rot_anim.start(self)
		self.roll_sound.play()


class ResetButton(kv.Button):
	angle = kv.NumericProperty()
	anim = kv.ObjectProperty()

	def __init__(self, **kwargs):
		super(ResetButton, self).__init__(**kwargs)
		self.anim = kv.Animation(angle=-720, duration=1)
		self.anim.bind(on_complete=lambda *_: setattr(self, "angle", 0))

	def on_release(self):
		app.reset_game()
		self.anim.start(self)


class MainApp(kv.App):
	questions = kv.ObjectProperty()
	# TODO: change unique colors for each category
	category_colors = kv.DictProperty({
		"art": (0.698, 0.133, 0.133),
		"science": (0.18, 0.545, 0.341),
		"geography": (0.98, 0.502, 0.447),
		"history": (0.98, 0.878, 0.259),
		"math": (0.059, 0.298, 0.506),
		"informatic": (1.0, 0.6, 0.2),
	})
	reset_on_win = kv.ListProperty()

	def build(self):
		self.questions = QuestionDB()
		root = Root()
		return root

	def reset_game(self):
		for checkbox in self.reset_on_win:
			checkbox.state = "normal"
		self.questions = QuestionDB()


class QuestionDB(kv.EventDispatcher):
	questions_path = kv.StringProperty("./Questions")
	categories = kv.ListProperty(["art", "science", "geography", "history", "math", "informatic"])
	art = kv.DictProperty()
	geography = kv.DictProperty()
	history = kv.DictProperty()
	informatic = kv.DictProperty()
	math = kv.DictProperty()
	science = kv.DictProperty()

	def __init__(self):
		super().__init__()
		for category in self.categories:
			setattr(self, category, self.parse_questions(category))

	def parse_questions(self, category_name) -> dict:
		with open(f"{self.questions_path}/{category_name}.json", encoding="UTF-8") as f:
			return json.load(f)

	def pop_question(self, category=None) -> tuple:
		if category is None:
			category = rd.choice(self.categories)

		category_dict = getattr(self, category)
		question, answer = rd.choice(list(category_dict.items()))
		del category_dict[question]

		return question, answer

	def questions_left(self, category):
		return len(getattr(self, category))


if __name__ == '__main__':
	app = MainApp()
	app.run()
