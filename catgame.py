import asyncio
import asyncssh
import random
import sys

# --- GAME ENGINE LOGIC ---
class Card:
    def __init__(self, name, energy_cost, stress_cost, delay_damage, description):
        self.name = name
        self.energy_cost = energy_cost
        self.stress_cost = stress_cost
        self.delay_damage = delay_damage
        self.description = description

class Obstacle:
    def __init__(self, name, delay, stress_damage):
        self.name = name
        self.delay = delay
        self.stress_damage = stress_damage

def get_fresh_deck():
    pool = [
        Card("Zoomies Sprint", 1, 0, 15, "Sprint forward. Deals 15 damage."),
        Card("Aggressive Meowing", 2, 0, 30, "Meow for a clear path. Deals 30 damage."),
        Card("Knock Over Coffee", 1, 20, 40, "Panicked move. Deals 40 damage, but adds 20 Stress!"),
        Card("Catnap", 0, -30, 0, "Take a quick breather. Lowers Stress by 30."),
        Card("Sidewalk Prowl", 2, -10, 20, "Weave through crowds. Deals 20 damage and lowers Stress by 10.")
    ]
    return pool + [Card(c.name, c.energy_cost, c.stress_cost, c.delay_damage, c.description) for c in pool]

# --- NETWORK HANDLER ---
async def handle_client(process):
    """
    This function manages a single player's session over the SSH network.
    It replaces standard print/input with network write/readline streams.
    """
    def s_print(text=""):
        process.stdout.write(text + "\r\n")

    async def s_input(prompt=""):
        process.stdout.write(prompt)
        try:
            line = await process.stdin.readline()
            return line.strip()
        except asyncio.IncompleteReadError:
            return ""

    s_print("=" * 50)
    s_print("\033[1;36m🐱 WELCOME TO LATE FOR WORK: CAT EDITION 🐱\033[0m")
    s_print("=" * 50)
    s_print("You overslept! You must clear the obstacle before your stress maxes out!\r\n")
    
    stress = 0
    max_stress = 100
    obstacle = Obstacle("The Chatty Neighbor", 100, 15)
    
    deck = get_fresh_deck()
    random.shuffle(deck)
    hand = []
    discard = []
    turn = 1

    while obstacle.delay > 0 and stress < max_stress:
        s_print(f"\n\033[1;36m=== TURN {turn} ===\033[0m")
        
        status_line = (
            f"Status: 🐱 Stress: \033[1;31m{stress}/{max_stress}\033[0m | "
            f"🛑 Obstacle: \033[1;36m{obstacle.name}\033[0m (\033[1;31m{obstacle.delay} Delay Left\033[0m)"
        )
        s_print(status_line)
        
        # --- Clean Card Drawing Loop ---
        energy = 3
        while len(hand) < 3:
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
                s_print("❌ Please enter a number!")
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
            stress += card.stress_cost
            obstacle.delay -= card.delay_damage
            stress = max(0, stress)
            
            s_print(f"\n✨ You played \033[1;32m{card.name}\033[0m!")
            if card.delay_damage > 0:
                s_print(f"💥 Reduced obstacle delay by \033[1;31m{card.delay_damage}\033[0m!")
            if card.stress_cost != 0:
                s_print(f"😰 Stress altered by \033[1;31m{card.stress_cost}\033[0m!")
                
            if obstacle.delay <= 0 or stress >= max_stress:
                break

        if obstacle.delay > 0 and stress < max_stress:
            s_print(f"\n⚠️ \033[1;31m{obstacle.name}\033[0m blocks your path! You suffer \033[1;31m{obstacle.stress_damage}\033[0m Stress.\n")
            stress += obstacle.stress_damage
            discard.extend(hand)
            hand.clear()
            turn += 1

    s_print("\n" + "=" * 50)
    if obstacle.delay <= 0:
        s_print("🎉 \033[1;32mSUCCESS! You sprinted past the obstacle and made it to work on time!\033[0m")
    else:
        s_print("🙀 \033[1;31mGAME OVER! Your stress hit 100% and you hid under a bush. You're fired!\033[0m")
    s_print("=" * 50)
    
    process.exit(0)


# --- START THE SERVER ---
class MySSHServer(asyncssh.SSHServer):
    def connection_made(self, conn):
        print(f"📥 New connection request received from {conn.get_extra_info('peername')[0]}")

    def auth_completed(self):
        print("✅ Authentication bypassed! Player is logging in...")

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
    # 🟢 This forces the server to accept absolutely ANY password or empty enter keys!
        return True

async def main():
    server_key = asyncssh.generate_private_key('ssh-rsa')
    
    # We pass our custom MySSHServer class to handle authentication overrides
    server = await asyncssh.create_server(
        MySSHServer, 
        host='', 
        port=8022,
        server_host_keys=[server_key],
        process_factory=handle_client
    )
    print("🚀 SSH Cat Battler server running on port 8022...")
    await server.wait_closed()

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down server.")
