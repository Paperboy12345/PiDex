import time
from PIL import ImageFont
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas

serial = i2c(port=1, address=0x3C)
device = sh1106(serial)

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)

layouts = [
	[list("qwertyuiop"), list("asdfghjkl"), list("zxcvbnm"), ["SPACE", "BACK", "→"]],
	[list("QWERTYUIOP"), list("ASDFGHJKL"), list("ZXCVBNM"), ["SPACE", "BACK", "←", "→"]],
	[list("1234567890"), list("!@#$%^&*()"), list("-_=+[]{}.'"), ["SPACE", "BACK", "←"]]
]

def get_text_input(buttons):
	cursor_row = 0
	cursor_col = 0
	text_buffer = ""
	layout_index = 0
	keyboard_visible = True
	last_states = {k: False for k in buttons}
	last_action_time = 0
	debounce_time = 0.15

	def current_layout():
		return layouts[layout_index]

	def draw_keyboard():
		device.clear()
		with canvas(device) as draw:
			draw.text((0, 0), text_buffer[-21:], font=font, fill=1)
			layout = current_layout()
			for row in range(len(layout)):
				for col in range(len(layout[row])):
					char = layout[row][col]
					x = col * 12
					y = row * 12 + 16
					if row == cursor_row and col == cursor_col:
						draw.rectangle((x, y, x + 11, y + 11), outline=1, fill=1)
						draw.text((x + 1, y + 1), char[:1], font=font, fill=0)
					else:
						draw.text((x + 1, y + 1), char[:1], font=font, fill=1)

	draw_keyboard()

	while keyboard_visible:
		now = time.time()
		for name, btn in buttons.items():
			if btn.is_pressed and not last_states[name]:
				if now - last_action_time > debounce_time:
					layout = current_layout()
					if name == "UP":
						cursor_row = (cursor_row - 1) % len(layout)
						cursor_col = min(cursor_col, len(layout[cursor_row]) - 1)
					elif name == "DOWN":
						cursor_row = (cursor_row + 1) % len(layout)
						cursor_col = min(cursor_col, len(layout[cursor_row]) - 1)
					elif name == "LEFT":
						cursor_col = (cursor_col - 1) % len(layout[cursor_row])
					elif name == "RIGHT":
						cursor_col = (cursor_col + 1) % len(layout[cursor_row])
					elif name == "OK":
						char = layout[cursor_row][cursor_col]
						if char == "SPACE":
							text_buffer += " "
						elif char == "BACK":
							text_buffer = text_buffer[:-1]
						elif char == "→":
							layout_index = (layout_index + 1) % len(layouts)
							cursor_row = 0
							cursor_col = 0
						elif char == "←":
							layout_index = (layout_index - 1) % len(layouts)
							cursor_row = 0
							cursor_col = 0
						else:
							text_buffer += char
					elif name == "BACK":
						keyboard_visible = False
					last_action_time = now
					draw_keyboard()
			last_states[name] = btn.is_pressed
		time.sleep(0.05)

	device.clear()
	return text_buffer
