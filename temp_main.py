
player_score = 0

def update_score(amount):
    global player_score
    player_score += amount
    print(f'Score changed: {player_score}')

def main():
    update_score(5)
//블록
