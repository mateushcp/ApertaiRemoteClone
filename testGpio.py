from gpiozero import Button
import time

# GPIOs que você quer monitorar
gpio_pins = [17, 16, 24]  # Monitorar GPIO 17, 18 e 24

# Crie os botões para os GPIOs especificados
buttons = {pin: Button(pin) for pin in gpio_pins}

print("Monitorando os estados dos GPIOs 17, 18 e 24 em tempo real...")

try:
    while True:
        for pin, button in buttons.items():
            if not button.is_pressed:
                print(f"GPIO {pin}: Botão PRESSIONADO NA QUADRA pressionado, CORRENTE CORTADA (corrente presente - HIGH)")
            if button.is_pressed:
                print(f"GPIO {pin}: CORRENTE FECHADA SEM PRESSIONAR O BOTAO (corrente ausente - LOW)")
        
        time.sleep(1)  # Aguarda 1 segundo antes de checar novamente
        print("---")
        
except KeyboardInterrupt:
    print("Encerrando monitoramento...")
