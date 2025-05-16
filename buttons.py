from gpiozero import Button
print("buttons running")
BUTTON_GPIO = {
	"UP": 5,
	"DOWN": 6,
	"LEFT": 13,
	"RIGHT": 19,
	"OK": 26,
	"BACK": 16
}

buttons = {name: Button(pin, pull_up=True) for name, pin in BUTTON_GPIO.items()}
