# helpful link to view pbn: https://www.philallen.co.uk/PBNViewerVersion1_1c.html
import os
# from bridge import Bridge
from bridgeClean import Bridge
import json

seats = ['N','E','S','W']

games = []

TARGET = {'Vulnerable', 'Dealer', 'Deal', 'Declarer', 'Contract', 'Result', 'Score', 'Auction', 'Play'}

# all denominations in order
DENOMS = ['C', 'D', 'H', 'S', 'NT']

# generate 1C–7NT
BIDS = [f"{level}{denom}" for level in range(1, 8) for denom in DENOMS]

VALID_AUCTION_ACTIONS = set(
    ['Pass', 'X', 'XX']  # pass, double, redouble
    + BIDS               # all valid level+denom bids
)

# Load in games from parsed pbn file
input_dir = 'parsed-games'

for filename in os.listdir(input_dir):
    # if filename != 'parsed-Esoito01.jsonl':
    #     continue

    if not filename.endswith('.jsonl'):
        continue

    filepath = os.path.join(input_dir, filename)
    file_games = []
    with open(filepath, 'r') as file:
        current_game = None

        for line in file:
            line = line.strip()
            if not line:
                continue

            obj = json.loads(line)

            if obj.get('type') == 'game':
                if current_game:
                    file_games.append(current_game)
                current_game = {}

            elif obj.get('type') == 'tag' and current_game is not None:
                name = obj.get('name')
                if name in TARGET:
                    current_game[name] = obj

        if current_game:
            file_games.append(current_game)
    games.append((filename, file_games))

print(f"total files loaded: {len(games)}")

declarers = []
actual_declarers = []
contracts = []
actual_contracts = []
results = []
actual_results = []
scores = []
actual_scores = []
for file_name, file_games in games:
    print('filename: ', file_name)
    for gameIndex, game in enumerate(file_games):
        # {"name":"Auction", "player":"N", value:"1D"}
        # {"name":"Play", "player":"W", value"H3"}
        print('game', gameIndex)
        if 'Auction' not in game:
            continue
        auctionActions = []
        auctionTokens = game['Auction']['tokens']
        seatIndex = seats.index(game['Auction']['value'])
        for token in auctionTokens:
            if token not in VALID_AUCTION_ACTIONS:
                continue
            auctionActions.append({'name': 'Auction', 'player': seats[seatIndex], 'value': token})
            seatIndex = (seatIndex + 1) % len(seats)
        
        actions = [game['Vulnerable'], game['Dealer'], game['Deal']] + auctionActions
        b = Bridge(actions)

        playActions = []
        if 'Play' not in game:
            continue
        playTokens = game['Play']['tokens']
        seatIndex = seats.index(game['Play']['value'])
        plays = []
        tricks = 0
        for token in playTokens:
            playAction = {'name': 'Play', 'player': seats[seatIndex], 'value': token}
            plays.append(playAction)
            seatIndex = (seatIndex + 1) % len(seats)
            if len(plays) == 4:
                count = 4
                while count:
                    i = 0
                    for index, item in enumerate(plays):
                        if item.get("player") == b.tricks[-1].next_player():
                            i = index
                    b.simulate(plays[i])
                    count -= 1
                tricks += 1
                plays = []
        if tricks == 13:
            results.append(b.results[0])
            actual_results.append(int(game['Result']['value']))
            scores.append(b.scores[0])
            actual_scores.append(game['Score']['value'])
            if b.scores[0] != game['Score']['value']:
                print(f'mismatch in score for file {file_name} at game {gameIndex}', b.scores[0], game['Score']['value'])
            if b.results[0] != int(game['Result']['value']):
                print(f'mismatch in result for file {file_name} at game {gameIndex}', b.results[0], int(game['Result']['value']))

        if b.declarers[0] != game['Declarer']['value']:
            print('declarers mismatch at game {gameIndex} in file {file_name}')
        declarers.append(b.declarers[0])
        actual_declarers.append(game['Declarer']['value'])
        contract = str(b.contracts[0]['level']) + str(b.contracts[0]['denomination']) + str(b.contracts[0]['risk'])
        contracts.append(contract)
        actual_contracts.append(game['Contract']['value'])
        if contract != game['Contract']['value']:
            print('contract mismatch at game {gameIndex} in file {file_name}')

for i in range(len(declarers)):
    if declarers[i] != actual_declarers[i]:
        print('declarers mismatch at ', i)

for i in range(len(contracts)):
    if contracts[i] != actual_contracts[i]:
        print('contracts mismatch at ', i)

for i in range(len(results)):
    if results[i] != actual_results[i]:
        print('results mismatch at ', i)

for i in range(len(scores)):
    if scores[i] != actual_scores[i]:
        print('scores mismatch at ', i)

print(len(scores))
print(len(results))
print(len(declarers))
print(len(contracts))
