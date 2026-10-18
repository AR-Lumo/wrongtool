import asyncio
import random
import asyncssh

class Card:
     def  __init__(self, name, energy_cost, stress_cost, delay_damage, description):
          self.name = name
          self.energy_cost = energy_cost
          self.stress_cost = stress_cost
          self.delay_damage = delay_damage
          self.description = description

class Obstacle:
     def __init__(self, name, delay, stress_damage, intro_text, is_boss=False):
          self.name = name
          self.delay = delay
          self.stress_damage = stress_damage
          self.intro_text = intro_text
          self.is_boss = is_boss

def get_fresh_deck():
     pool = [
          Card("Zoomies Sprint", 1, 0, 15, "Sprint forward. Deals 15 damage."),
          Card("Agressive Meowing", 2, 0, 30, "Meow for a path. Deals 30 damage."),
          Card("Knock Over Coffee", 1, 20, 40, "Panicked move. Deals 40 damage, +20 stress."),
          Card("Catnap", 0, -30, 0, "Take a quick breather. lowers  stress by 30."),
          Card("Sidewalk Prowl", 2, -10, 20, "Weave through the Crowd. Deals 20 damage, -10 stress.")
     ]
     return pool + [Card(c.name, c.energy_cost, c.stress_cost, c.delay_damage, c.description) for c in pool]

OBSTACLE_POOL = [
     Obstacle("The Chatty Neighbor", 80, 12, "Oh no! Mrs. Higgins is watering her plants and spotted you!"),
     Obstacle("The Slow-Moving Bus", 90, 15, "The bus is crawling through traffic! You need to force your way off."),
     Obstacle("Sudden Downpour", 75, 18, "It's raining hard. Your fur is getting soaked!")
]

async def handle_client(process):
     def s_print(text=""):
          process.stdout.write(text + "\r\n")

     async def s_input(prompt=""):
          process.stdout.write(prompt)
          try:
               line = await process.stdin.readline()
               return line.strip()
          except asyncio.IncompleteReadError:
               return ""

     s_print("\033[H\033[J")
     s_print("=" * 60)
     s_print("\033[1;36m🐱 LATE FOR WORK: EXTENDED BOSS EDITION v3.0 🐱\033[0m")
     s_print("=" * 60)
     s_print(" [1] Start Campaign")
     s_print(" [2] How to Play")

     menu_choice = await s_input("\nSelect an option: ")
     if menu_choice == '2':
          s_print("\n\033[1;33m--- INSTRUCTIONS ---\033[0m")
          s_print("- Fight through one street obstacle, then defeat the Boss at the elevator.")
          s_print("- Keep Stress below 100 or you run away and lose!")
          await s_input("\nPress [Enter] to start your day...")

     s_print("\033[H\033[J")
     stress = 0
     max_stress = 100

     s_print("\033[1;36m🎒 CHOOSE YOUR CAT GEAR:\033[0m")
     s_print(" [1] Premium Catnip (Draw 4 cards per turn instead of 3)")
     s_print(" [2] Cardboard Box (Increases Max Stress Limit to 120)")
     item_choice = await s_input("\nPick an item: ")

     hand_size = 3
     if item_choice == '1':
          hand_size = 4
          s_print("\n\033[1;32m✨ Equipped Premium Catnip! (+1 Draw Size)\033[0m\n")
     elif item_choice == '2':
          max_stress = 120
          s_print("\n\033[1;32m✨ Equipped Cardboard Box! (+20 Max Stress)\033[0m\n")
     else:
          s_print("\nGoing running bare claws! Bold.\n")
     
     await s_input("Press [Enter] to hit the streets...")

     stages = [
          random.choice(OBSTACLE_POOL),
          Obstacle("The Disctracted Boss", 150, 25, "STAGE 2: You made it to the office lobby, but the Boss is blocking the elevator!", is_boss=True)
     ]

     for current_obstacle in stages:
          if stress >= max_stress:
               break

          s_print("\033[H\033[J")
          s_print(f"\033[1;31m🚨 {current_obstacle.intro_text}\033[0m\n")

          deck = get_fresh_deck()
          random.shuffle(deck)
          hand = []
          discard = []
          turn = 1

          while current_obstacle.delay > 0 and stress < max_stress:
               s_print(f"\n\033[1;36m=== TURN {turn} ===\033[0m")
               status_line = (
                    f"Status: 🐱 Stress: \033[1;31m{stress}/{max_stress}\033[0m | "
                    f"🛑 Enemy: \033[1;36m{current_obstacle.name}\033[0m (\033[1;31m{current_obstacle.delay} Delay Left\033[0m)"
               )
               s_print(status_line)

               energy = 3
               while len(hand) < hand_size:
                    if not deck:
                         deck = list(discard)
                         random.shuffle(deck)
                         discard.clear()
                    if not deck:
                         break
                    hand.append(deck.pop(0))
               while energy > 0 and hand:
                    s_print(f"\nAvailable Energy: \033[1;33m{'⚡ ' * energy}({energy})\033[0m")
                    s_print("Your Hand:")   
                    for i, card in enumerate(hand):
                         s_print(f" [\033[1;36m{i + 1}\033[0m] \033[1;32m{card.name}\033[0m (Cost: \033[1;33m{card.energy_cost}⚡\033[0m) -> {card.description}")
                    s_print(" [\033[1;31m0\033[0m] End Turn")

                    choice = await s_input("\nChoose a card to play: ")
                    if choice == '0' or not choice:
                         break

                    if not choice.isdigit():
                         s_print("❌ Enter a number!")
                         continue

                    idx = int(choice) - 1
                    if idx < 0 or idx >= len(hand):
                         s_print("❌ Invalid card number!")
                         continue

                    card = hand[idx]
                    if card.energy_cost > energy:
                         s_print("❌ Not enough energy!")
                         continue

                    hand.pop(idx)
                    discard.append(card)
                    energy -= card.energy_cost
                    stress +=card.stress_cost
                    current_obstacle.delay -= card.delay_damage
                    stress = max(0, stress)

                    s_print(f"\n✨ You played \033[1;32m{card.name}\033[0m!")
                    if current_obstacle.delay <= 0 or stress >= max_stress:
                         break

               if current_obstacle.delay > 0 and stress < max_stress:
                    s_print(f"\n⚠️ \033[1;31m{current_obstacle.name}\033[0m counters! You suffer \033[1;31m{current_obstacle.stress_damage}\033[0m Stress.\n")
                    stress += current_obstacle.stress_damage
                    discard.extend(hand)
                    hand.clear()
                    turn += 1
          if current_obstacle.delay <= 0 and not current_obstacle.is_boss:
               s_print("\n\033[1;32m🎉 Street cleared! Entering the office building...\033[0m")
               await s_input("Press [Enter] to face the final boss...")
     
     s_print ("\n" + "=" * 60)
     if stress < max_stress:
        s_print("🎉 \033[1;32mCAMPAIGN VICTORY! You slipped into the elevator unnoticed and made it to your desk!\033[0m")
     else:
        s_print("🙀 \033[1;31mGAME OVER! You broke down out of stress and hid in a supply closet!\033[0m")
     s_print("=" * 60)
    
     process.exit(0)
     
                    
class MySSHServer(asyncssh.SSHServer):
     def password_auth_supported(self): return True
     def validate_password(self, username, password): return True

async def main():
    server_key = asyncssh.generate_private_key('ssh-rsa')
    server = await asyncssh.create_server(MySSHServer, host='', port=8022, server_host_keys=[server_key], process_factory=handle_client)
    print("🚀 SSH Cat Battler v3.0 server active on port 8022...")
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shutdown.")