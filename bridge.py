import random

# VULNERABLE {"type":"tag","name":"Vulnerable","value":"None"}
# DEALER {"type":"tag","name":"Dealer","value":"N"}
# DEAL {"type":"tag","name":"Deal","value":"N:T983.743.A9.K964 Q752.AT82.QJT7.5 4.KQJ9.K8652.Q87 AKJ6.65.43.AJT32","cards":[{"seat":"N","suit":"S","rank":"T"},{"seat":"N","suit":"S","rank":"9"},{"seat":"N","suit":"S","rank":"8"},{"seat":"N","suit":"S","rank":"3"},{"seat":"N","suit":"H","rank":"7"},{"seat":"N","suit":"H","rank":"4"},{"seat":"N","suit":"H","rank":"3"},{"seat":"N","suit":"D","rank":"A"},{"seat":"N","suit":"D","rank":"9"},{"seat":"N","suit":"C","rank":"K"},{"seat":"N","suit":"C","rank":"9"},{"seat":"N","suit":"C","rank":"6"},{"seat":"N","suit":"C","rank":"4"},{"seat":"E","suit":"S","rank":"Q"},{"seat":"E","suit":"S","rank":"7"},{"seat":"E","suit":"S","rank":"5"},{"seat":"E","suit":"S","rank":"2"},{"seat":"E","suit":"H","rank":"A"},{"seat":"E","suit":"H","rank":"T"},{"seat":"E","suit":"H","rank":"8"},{"seat":"E","suit":"H","rank":"2"},{"seat":"E","suit":"D","rank":"Q"},{"seat":"E","suit":"D","rank":"J"},{"seat":"E","suit":"D","rank":"T"},{"seat":"E","suit":"D","rank":"7"},{"seat":"E","suit":"C","rank":"5"},{"seat":"S","suit":"S","rank":"4"},{"seat":"S","suit":"H","rank":"K"},{"seat":"S","suit":"H","rank":"Q"},{"seat":"S","suit":"H","rank":"J"},{"seat":"S","suit":"H","rank":"9"},{"seat":"S","suit":"D","rank":"K"},{"seat":"S","suit":"D","rank":"8"},{"seat":"S","suit":"D","rank":"6"},{"seat":"S","suit":"D","rank":"5"},{"seat":"S","suit":"D","rank":"2"},{"seat":"S","suit":"C","rank":"Q"},{"seat":"S","suit":"C","rank":"8"},{"seat":"S","suit":"C","rank":"7"},{"seat":"W","suit":"S","rank":"A"},{"seat":"W","suit":"S","rank":"K"},{"seat":"W","suit":"S","rank":"J"},{"seat":"W","suit":"S","rank":"6"},{"seat":"W","suit":"H","rank":"6"},{"seat":"W","suit":"H","rank":"5"},{"seat":"W","suit":"D","rank":"4"},{"seat":"W","suit":"D","rank":"3"},{"seat":"W","suit":"C","rank":"A"},{"seat":"W","suit":"C","rank":"J"},{"seat":"W","suit":"C","rank":"T"},{"seat":"W","suit":"C","rank":"3"},{"seat":"W","suit":"C","rank":"2"}]}
# AUCTION {"type":"tag","name":"Auction","value":"N","section":["Pass  Pass  1D    1S","Pass  2NT   Pass  3NT","Pass  4S    Pass  Pass","Pass"],"tokens":["Pass","Pass","1D","1S","Pass","2NT","Pass","3NT","Pass","4S","Pass","Pass","Pass"]}
# -> CONTRACT {"type":"tag","name":"Contract","value":"4S","level":4,"denomination":"S","risk":""}
# -> DECLARER {"type":"tag","name":"Declarer","value":"W"}
# PLAY {"type":"tag","name":"Play","value":"N","section":["H3 H2 H9 H6","H4 HA HQ H5","H7 H8 HJ S6","D9 DT DK D4","C4 HT HK SA","S3 S2 S4 SK","S8 S5 D5 SJ","DA D7 D6 D3","C6 C5 CQ CA","CK S7 C7 CJ","S9 SQ D2 C2","ST DQ D8 C3","C9 DJ C8 CT","*"],"tokens":["H3","H2","H9","H6","H4","HA","HQ","H5","H7","H8","HJ","S6","D9","DT","DK","D4","C4","HT","HK","SA","S3","S2","S4","SK","S8","S5","D5","SJ","DA","D7","D6","D3","C6","C5","CQ","CA","CK","S7","C7","CJ","S9","SQ","D2","C2","ST","DQ","D8","C3","C9","DJ","C8","CT","*"]}
# -> RESULT {"type":"tag","name":"Result","value":"9"}
# -> SCORE {"type":"tag","name":"Score","value":"NS 50"}

# PLAY and AUCTION need to have completed format and non completed format to support live games

# bridge class that should work well with parsed pbn format
# actions are mostly in the format of parsed pbn format, but one caveat is
# auction and play input formats are different.
# You need to first convert the parsed pbn format's auction and play params into 'live' auction and play
# because this class will parse each action one by one and determine if its legal or not
class bridge():
    # spades, hearts, diamonds, clubs
    suits = ['C','D','H','S']
    ranks = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']
    players = ['N','E','S','W']

    # Pass in actions to simulate each action for the match
    def __init__(self, actions=None):
        # setup cards, ordered by suit + rank
        self.cards = [s + r for s in self.suits for r in self.ranks]

        # game state
        self.actions = actions
        self.hands = {'N': [], 'S': [], 'E': [], 'W': []}
        self.gameIndex = 0
        self.currentPhase = None
        self.vulnerable = None

        # info required for pbn format
        self.dealers = []
        self.vulnerables = []
        self.deals = []
        self.auctions = []
        self.contracts = []
        self.declarers = []
        self.results = []
        self.scores = []

        if self.actions == None:
            # initialize a fresh match
            self.actions = []
            self.actions.append({ 'name': 'Vulnerable', 'value': 'None' })
            self.actions.append({ 'name': 'Dealer', "value": random.choice([self.players]) })
            self.actions.append(self.generateDeal())
        for action in actions:
            self.simulate(action)

    def generateDeal(self):
        shuffledCards = random.sample(self.cards, k=len(self.cards))
        dealtCards = []
        for card in shuffledCards[ 0:13]:
            dealtCards.append({'seat': 'N', 'suit': card[0], 'rank': card[1]})
        for card in shuffledCards[13:26]:
            dealtCards.append({'seat': 'W', 'suit': card[0], 'rank': card[1]})
        for card in shuffledCards[26:39]:
            dealtCards.append({'seat': 'S', 'suit': card[0], 'rank': card[1]})
        for card in shuffledCards[39:52]:
            dealtCards.append({'seat': 'E', 'suit': card[0], 'rank': card[1]})
        deal = {'name':'Deal' , 'cards': dealtCards}
        return deal

    # updates states based on each action
    # NOTE: actions for auction/play are in non parsed pbn format:
    # {"name":"Auction", "player":"N", value:"1D"}
    # {"name":"Play", "player":"W", value"H3"}
    def simulate(self, action):
        if action['name'] == 'Auction':
            self.handleAuctionAction(action)
        elif action['name'] == 'Deal':
            self.handleDealAction(action)
        elif action['name'] == 'Dealer':
            self.handleDealerAction(action)
        elif action['name'] == 'Play':
            self.handlePlayAction(action)
        elif action['name'] == 'Vulnerable':
            self.handleVulnerableAction(action)
    
    def handleAuctionAction(self, action):
        pass

    def handleDealAction(self, action):
        pass
    
    def handleDealerAction(self, action):
        self.dealers.append(action['value'])

    def handlePlayAction(self, action):
        pass

    def handleVulnerableAction(self, action):
        self.vulnerable.append(action['value'])

    def simulateGame(self, actions):
        for action in actions:
            # Auction phase
            # each bid must be higher than the last
            # auction end when 3 passes in a row
            # player can double or re - double

            # Play phase
            # Once contract is determined, play starts
            # The player to the left of the declarer makes the first lead.
            # Players take turns playing a card to each "trick" in clockwise order.
            # Declarer plays both their own hand and the dummy's hand
            # First to bid the winning contract is the declarer, other is dummy
            # First trick is led by declarer, and each subsequent tricks are led by winner of previous trick.

            # Scoring phase
            # seems complicated but can figure out after we finish making auction and play phase
            pass

b = bridge()
print(b.deal)
print(b.hands)