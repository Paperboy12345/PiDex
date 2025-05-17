import time
import pexpect
import re
from PIL import ImageFont
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas
from keyboard import get_text_input

serial = i2c(port=1, address=0x3C)
device = sh1106(serial)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)

VISIBLE_LINES = 5
SCROLL_STEP = 18

ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
def clean_ansi(text):
	return ansi_escape.sub('', text)

def launch_terminal(buttons):
	shell = pexpect.spawn('/bin/bash', encoding='utf-8', echo=False)
	shell.setecho(False)
	shell.sendline('export PS1="$ "')
	shell.expect(r'\$')

	output_lines = []
	scroll_y = 0
	scroll_x = 0

	def draw_terminal():
		device.clear()
		with canvas(device) as draw:
			start = max(0, len(output_lines) - VISIBLE_LINES - scroll_y)
			end = start + VISIBLE_LINES
			view = output_lines[start:end]
			y = 0
			for line in view:
				line_clean = clean_ansi(line.strip())
				draw.text((-scroll_x, y), line_clean, font=font, fill=1)
				y += 10
			draw.text((0, 56), "$", font=font, fill=1)

	draw_terminal()

	while True:
		if buttons["OK"].is_pressed:
			while buttons["OK"].is_pressed:
				time.sleep(0.05)
			cmd = get_text_input(buttons)
			if not cmd.strip():
				continue
			shell.sendline(cmd)

			lines = [f"$ {cmd}"]
			buffer = ""
			timeout = time.time() + 10

			try:
				while time.time() < timeout:
					try:
						chunk = shell.read_nonblocking(size=128, timeout=0.5)
						buffer += chunk
						timeout = time.time() + 1  # reset timer if data flows

						parts = re.split(r'[\r\n]+', buffer)
						buffer = parts.pop()  # save incomplete part

						for part in parts:
							part = clean_ansi(part.strip())
							if part:
								lines.append(part)

						if buffer.strip():
							lines.append(clean_ansi(buffer.strip()))
						output_lines.extend(lines)
						draw_terminal()
						if buffer.strip():
							output_lines.pop()
						lines = []

					except pexpect.exceptions.TIMEOUT:
						if buffer.strip():
							lines.append(clean_ansi(buffer.strip()))
							output_lines.extend(lines)
							draw_terminal()
							output_lines.pop()
							lines = []
						continue
			except Exception as e:
				lines.append(f"[Error] {e}")
				output_lines.extend(lines)
				draw_terminal()

		elif buttons["UP"].is_pressed:
			while buttons["UP"].is_pressed:
				time.sleep(0.05)
			if scroll_y + VISIBLE_LINES < len(output_lines):
				scroll_y += 1
			draw_terminal()

		elif buttons["DOWN"].is_pressed:
			while buttons["DOWN"].is_pressed:
				time.sleep(0.05)
			if scroll_y > 0:
				scroll_y -= 1
			draw_terminal()

		elif buttons["LEFT"].is_pressed:
			while buttons["LEFT"].is_pressed:
				time.sleep(0.05)
			scroll_x = max(0, scroll_x - SCROLL_STEP)
			draw_terminal()

		elif buttons["RIGHT"].is_pressed:
			while buttons["RIGHT"].is_pressed:
				time.sleep(0.05)
			scroll_x += SCROLL_STEP
			draw_terminal()

		elif buttons["BACK"].is_pressed:
			while buttons["BACK"].is_pressed:
				time.sleep(0.05)
			shell.sendline('exit')
			shell.close()
			device.clear()
			break

		time.sleep(0.05)
