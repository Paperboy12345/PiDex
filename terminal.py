import subprocess
import time
from PIL import ImageFont
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas
from keyboard import get_text_input

serial = i2c(port=1, address=0x3C)
device = sh1106(serial)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)

def run_command(cmd):
	try:
		result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=10)
		return result.decode().strip().splitlines()
	except subprocess.CalledProcessError as e:
		return [f"Error: {e.output.decode().strip()}"]
	except Exception as e:
		return [f"Exception: {str(e)}"]

def launch_terminal(buttons):
	while True:
		device.clear()
		with canvas(device) as draw:
			draw.text((0, 0), "OK = type", font=font, fill=1)
			draw.text((0, 12), "BACK = exit", font=font, fill=1)
		time.sleep(0.1)

		if buttons["OK"].is_pressed:
			cmd = get_text_input(buttons)
			output = run_command(cmd)
			device.clear()
			with canvas(device) as draw:
				draw.text((0, 0), f"$ {cmd}", font=font, fill=1)
				for i, line in enumerate(output[-4:]):
					draw.text((0, 12 + i * 10), line[:21], font=font, fill=1)
			time.sleep(2)

		if buttons["BACK"].is_pressed:
			device.clear()
			break
