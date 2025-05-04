# helpful link to view pbn: https://www.philallen.co.uk/PBNViewerVersion1_1c.html

from bridge import Bridge
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
with open('parsed-41284.jsonl', 'r') as file:
    current_game = None
    for line in file:
        line = line.strip()
        if not line:
            continue

        obj = json.loads(line)

        # start a new game
        if obj.get('type') == 'game':
            if current_game:
                games.append(current_game)
            current_game = {}

        # collect only the tags we care about
        elif obj.get('type') == 'tag' and current_game is not None:
            name = obj.get('name')
            if name in TARGET:
                current_game[name] = obj

    # don't forget to append the last game
    if current_game:
        games.append(current_game)

declarers = []
actual_declarers = []
contracts = []
actual_contracts = []
plays_tricks_count = []
results = []
actual_results = []
for gameIndex, game in enumerate(games):
    print('game', gameIndex + 1)
    # {"name":"Auction", "player":"N", value:"1D"}
    # {"name":"Play", "player":"W", value"H3"}
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
        print('complete tricks', gameIndex + 1)
        results.append(b.results[0])
        actual_results.append(game['Result']['value'])

    declarers.append(b.declarers[0])
    actual_declarers.append(game['Declarer']['value'])
    contract = str(b.contracts[0]['level']) + str(b.contracts[0]['denomination']) + str(b.contracts[0]['risk'])
    contracts.append(contract)
    actual_contracts.append(game['Contract']['value'])
    if (b.declarers[0] != game['Declarer']['value']) or (contract != game['Contract']['value']):
        print('actions: ', auctionActions)
print(declarers)
print(actual_declarers)
print(contracts)
print(actual_contracts)
print(results)
print(actual_results)