from gpiozero import Button

# Liste os GPIOs que você quer verificar
gpio_pins = [4, 17, 18, 27, 22, 23, 24, 25, 16]  # Adicione os GPIOs que você quer monitorar

# Crie um dicionário para armazenar o estado de cada GPIO
gpio_states = {}

for pin in gpio_pins:
    try:
        button = Button(pin)
        if button.is_pressed:
            gpio_states[pin] = "LOW (sem corrente)"
        else:
            gpio_states[pin] = "HIGH (com corrente)"
    except:
        gpio_states[pin] = "Não foi possível acessar o GPIO (talvez não esteja configurado)."

# Exibe o estado de cada GPIO
for pin, state in gpio_states.items():
    print(f"GPIO {pin}: {state}")
