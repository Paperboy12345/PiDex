import time
from PIL import Image, ImageDraw, ImageFont
from luma.core.render import canvas
from luma.oled.device import sh1106
from luma.core.interface.serial import i2c
from gpiozero import Button

serial = i2c(port=1, address=0x3C)
device = sh1106(serial)

BUTTON_GPIO = {
	"UP": 5,
	"DOWN": 6,
	"LEFT": 13,
	"RIGHT": 19,
	"OK": 26,
	"BACK": 16
}

buttons = {name: Button(pin, pull_up=True) for name, pin in BUTTON_GPIO.items()}

KEYBOARD = [
	list("QWERTYUIOP"),
	list("ASDFGHJKL"),
	list("ZXCVBNM"),
	[" ", ".", "_", "<", "O", "K", ">", ""]
]

ROWS = len(KEYBOARD)
COLS = max(len(row) for row in KEYBOARD)

cursor_row = 0
cursor_col = 0
text_buffer = ""
keyboard_visible = True

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)

last_states = {name: False for name in buttons}
last_action_time = 0
debounce_time = 0.15

def draw_keyboard():
	device.clear()
	with canvas(device) as draw:
		draw.text((0, 0), text_buffer[-16:], font=font, fill=1)
		for row in range(ROWS):
			for col in range(len(KEYBOARD[row])):
				char = KEYBOARD[row][col]
				x = col * 12
				y = row * 12 + 16
				if row == cursor_row and col == cursor_col:
					draw.rectangle((x, y, x + 11, y + 11), outline=1, fill=1)
					draw.text((x + 2, y + 1), char, font=font, fill=0)
				else:
					draw.text((x + 2, y + 1), char, font=font, fill=1)

def handle_button(button):
	global cursor_row, cursor_col, text_buffer, keyboard_visible
	if not keyboard_visible and button == "BACK":
		keyboard_visible = True
		draw_keyboard()
		return
	if not keyboard_visible:
		return
	if button == "UP":
		cursor_row = (cursor_row - 1) % ROWS
		cursor_col = min(cursor_col, len(KEYBOARD[cursor_row]) - 1)
	elif button == "DOWN":
		cursor_row = (cursor_row + 1) % ROWS
		cursor_col = min(cursor_col, len(KEYBOARD[cursor_row]) - 1)
	elif button == "LEFT":
		cursor_col = (cursor_col - 1) % len(KEYBOARD[cursor_row])
	elif button == "RIGHT":
		cursor_col = (cursor_col + 1) % len(KEYBOARD[cursor_row])
	elif button == "OK":
		char = KEYBOARD[cursor_row][cursor_col]
		if char == "<":
			text_buffer = text_buffer[:-1]
		elif char == ">":
			pass
		elif char == " ":
			text_buffer += " "
		elif char == "O" or char == "K":
			pass
		else:
			text_buffer += char
	elif button == "BACK":
		keyboard_visible = False
		device.clear()
		return
	if keyboard_visible:
		draw_keyboard()

def run_keyboard_loop():
	global last_action_time
	draw_keyboard()
	while True:
		now = time.time()
		for name, btn in buttons.items():
			pressed = btn.is_pressed
			if pressed and not last_states[name]:
				if now - last_action_time > debounce_time:
					handle_button(name)
					last_action_time = now
			last_states[name] = pressed
		time.sleep(0.05)

if __name__ == "__main__":
	run_keyboard_loop()
