import time
from datetime import datetime
from PIL import ImageFont
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas
from buttons import buttons
from terminal import launch_terminal

serial = i2c(port=1, address=0x3C)
device = sh1106(serial)

title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
version_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
menu_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)

menus = {
	"main": ["Start", "Terminal", "Settings"],
	"Start": ["Wi-Fi", "Bluetooth", "RF", "NFC", "RFID", "IR", "BACK"],
	"Wi-Fi": ["Connect to Wi-Fi", "Wi-Fi Scanner", "Handshakes", "Twin Attk", "Deauth", "PMKID", "Sniffer", "Beacon", "Access Point", "Jammer", "MITM", "DNS Spoof", "BACK"],
	"Bluetooth": ["Scanner", "Signal Log", "Tracker", "Deauth", "AD Flood", "L2CAP Flood", "Null Flood", "Beacon Flood", "Pairing Flood", "DoS", "ID Faker", "Serial Control", "BACK"],
	"RF": ["Sniffer", "Signal Log", "IDr", "Recorder", "Broadcast", "Jammer", "Beacon", "Decoder", "Blind Jam", "BACK"],
	"NFC": ["Reader", "Broadcaster", "Cloner", "Emulator", "NDEF Payload", "URL Writer", "Wiper", "Garbage", "Key Crack", "BACK"],
	"RFID": ["Scanner", "Broadcaster", "Cloner", "Overwriter", "Formatter", "Injector", "BACK"],
	"IR": ["Sniffer", "Analyzer", "IDr", "Broadcaster", "UEB", "Spammer", "Jammer", "BACK"]
}

menu_stack = ["main"]
selected = 0
scroll_offset = 0
VISIBLE_ITEMS = 5
last_states = {k: False for k in buttons}
last_action_time = 0
debounce_time = 0.15

def current_menu_name():
	return menu_stack[-1]

def current_menu_items():
	return menus[current_menu_name()]

def draw_menu():
	device.clear()
	with canvas(device) as draw:
		now = datetime.now().strftime("%H:%M")
		draw.text((100, 0), now, font=version_font, fill=1)

		if current_menu_name() == "main":
			pidex_width = title_font.getbbox("PiDex")[2]
			draw.text((5, 0), "PiDex", font=title_font, fill=1)
			draw.text((5 + pidex_width + 5, 5), "v1.0", font=version_font, fill=1)

		start_y = 16 if current_menu_name() == "main" else 8
		items = current_menu_items()
		view_items = items[scroll_offset:scroll_offset + VISIBLE_ITEMS]

		for i, label in enumerate(view_items):
			x = 10
			y = start_y + i * 12
			w = 108
			h = 11
			item_index = scroll_offset + i
			if item_index == selected:
				draw.rectangle((x, y, x + w, y + h), outline=1, fill=1)
				draw.text((x + 5, y), label, font=menu_font, fill=0)
			else:
				draw.rectangle((x, y, x + w, y + h), outline=1, fill=0)
				draw.text((x + 5, y), label, font=menu_font, fill=1)

def update_scroll():
	global scroll_offset
	items = current_menu_items()
	if selected < scroll_offset:
		scroll_offset = selected
	elif selected >= scroll_offset + VISIBLE_ITEMS:
		scroll_offset = selected - VISIBLE_ITEMS + 1

def handle_button(name):
	global selected, scroll_offset

	items = current_menu_items()
	label = items[selected]

	if name == "UP":
		selected = (selected - 1) % len(items)
	elif name == "DOWN":
		selected = (selected + 1) % len(items)
	elif name == "OK":
		if label == "BACK":
			if len(menu_stack) > 1:
				menu_stack.pop()
				selected = 0
				scroll_offset = 0
		elif label == "Terminal":
			launch_terminal(buttons)
		elif label in menus:
			menu_stack.append(label)
			selected = 0
			scroll_offset = 0
		else:
			device.clear()
			print("Selected:", label)
			time.sleep(1)
	elif name == "BACK" and current_menu_name() != "main":
		menu_stack.pop()
		selected = 0
		scroll_offset = 0

	update_scroll()
	draw_menu()

def run_menu():
	global last_action_time
	draw_menu()
	while True:
		now = time.time()
		for name, btn in buttons.items():
			if btn.is_pressed and not last_states[name]:
				if now - last_action_time > debounce_time:
					handle_button(name)
					last_action_time = now
			last_states[name] = btn.is_pressed
		time.sleep(0.05)

if __name__ == "__main__":
	run_menu()
