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

class bridge():
    # spades, hearts, diamonds, clubs
    suits = ['C','D','H','S']
    ranks = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']

    def __init__(self):
        self.cards = [s + r for s in self.suits for r in self.ranks]
        self.hands = {'N': [], 'S': [], 'E': [], 'W': []}
        self.dealer = self.getRandomDealer()
        self.deal = []
        self.vulnerable = None
        self.phase = 'AUCTION'
        self.generateDeal()

    def getRandomDealer(self):
        return random.choice(['N','S','E','W'])

    def generateDeal(self):
        shuffledCards = random.sample(self.cards, k=len(self.cards))
        self.deal = shuffledCards

        self.hands['N'] = self.deal[ 0:13]
        self.hands['E'] = self.deal[13:26]
        self.hands['S'] = self.deal[26:39]
        self.hands['W'] = self.deal[39:52]

    def play(self, actions):
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