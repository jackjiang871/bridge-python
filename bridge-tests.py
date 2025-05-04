from bridge import Bridge
import json

seats = ['N','E','S','W']

games = []

TARGET = {'Vulnerable', 'Dealer', 'Deal', 'Declarer', 'Contract', 'Result', 'Score', 'Auction', 'Play'}

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
for game in games:
    # {"name":"Auction", "player":"N", value:"1D"}
    # {"name":"Play", "player":"W", value"H3"}
    auctionActions = []
    auctionTokens = game['Auction']['tokens']
    seatIndex = seats.index(game['Auction']['value'])
    for token in auctionTokens:
        auctionActions.append({'name': 'Auction', 'player': seats[seatIndex], 'value': token})
        seatIndex = (seatIndex + 1) % len(seats)

    playActions = []
    playTokens = game['Play']['tokens']
    seatIndex = seats.index(game['Play']['value'])
    for token in playTokens:
        auctionActions.append({'name': 'Play', 'player': seats[seatIndex], 'value': token})
        seatIndex = (seatIndex + 1) % len(seats)

    actions = [game['Vulnerable'], game['Dealer'], game['Deal']] + auctionActions + playActions
    b = Bridge(actions)
    declarers.append(b.declarers[0])
    actual_declarers.append(game['Declarer']['value'])
print(declarers)
print(actual_declarers)