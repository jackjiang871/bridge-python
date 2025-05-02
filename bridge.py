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

class Auction:
    """
    Encapsulates a contract bridge auction sequence:
      - Records calls (Pass, X, XX, or bids like '1C','2NT', etc.)
      - Validates each call for basic legality
      - Detects end-of-auction conditions (pass out or 3 passes after last bid)
      - Computes final contract and declarer
    """

    # allowed denominations (in increasing order) and levels
    DENOMINATIONS = ['C', 'D', 'H', 'S', 'NT']
    LEVELS = list(range(1, 8))  # 1 through 7

    def __init__(self):
        self.calls = []             # list of {'player': 'N', 'call': '1H' | 'Pass' | ...}
        self.last_bid_idx = None    # index into calls where last real bid occurred

    @classmethod
    def _bid_value(cls, bid_str: str) -> int:
        """Convert a bid like '3NT' into an integer for ordering"""
        level = int(bid_str[0])
        denom = bid_str[1:]
        denom_index = cls.DENOMINATIONS.index(denom)
        # spread out by levels so all 1x < all 2x < ...
        return (level - 1) * len(cls.DENOMINATIONS) + denom_index

    def is_valid_call(self, player: str, call: str) -> bool:
        """Basic legality checks for a new call"""
        # Pass always legal
        if call == 'Pass':
            return True

        # Double: only immediately after an opponent's bid
        if call == 'X':
            if not self.calls or self.calls[-1]['call'] in ('Pass', 'X', 'XX'):
                return False
            return self.calls[-1]['player'] != player

        # Redouble: only immediately after opponent's Double
        if call == 'XX':
            if not self.calls or self.calls[-1]['call'] != 'X':
                return False
            return self.calls[-1]['player'] != player

        # Otherwise must be a level+denomination bid
        if len(call) < 2 or not call[0].isdigit():
            return False
        level = int(call[0])
        denom = call[1:]
        if level not in self.LEVELS or denom not in self.DENOMINATIONS:
            return False
        # must exceed any previous bid
        if self.last_bid_idx is not None:
            last = self.calls[self.last_bid_idx]['call']
            if self._bid_value(call) <= self._bid_value(last):
                return False
        return True

    def add_call(self, player: str, call: str) -> bool:
        """
        Record a new call. Raises ValueError if invalid.
        Returns True if auction is now finished, False otherwise.
        """
        if not self.is_valid_call(player, call):
            raise ValueError(f"Illegal call {call!r} by {player}")

        self.calls.append({'player': player, 'call': call})
        idx = len(self.calls) - 1
        # track last real bid
        if call not in ('Pass', 'X', 'XX'):
            self.last_bid_idx = idx

        return self.is_finished()

    def is_finished(self) -> bool:
        """True if auction has ended: pass-out or three passes after last bid"""
        # Pass-out: first four calls are Pass
        if self.last_bid_idx is None and len(self.calls) >= 4:
            if all(c['call'] == 'Pass' for c in self.calls[:4]):
                return True

        # Normal: at least three calls after the last bid
        if self.last_bid_idx is not None:
            if len(self.calls) - self.last_bid_idx >= 4:
                return True

        return False

    def contract(self) -> dict:
        """
        Returns final contract as:
          {'level': int, 'denomination': str or None, 'risk': ''|'X'|'XX'}
        """
        if not self.is_finished():
            raise RuntimeError("Auction not finished yet")

        # pass-out
        if self.last_bid_idx is None:
            return {'level': 0, 'denomination': None, 'risk': ''}

        last_bid = self.calls[self.last_bid_idx]
        level = int(last_bid['call'][0])
        denom = last_bid['call'][1:]
        tail = [c['call'] for c in self.calls[self.last_bid_idx+1:]]
        if 'XX' in tail:
            risk = 'XX'
        elif 'X' in tail:
            risk = 'X'
        else:
            risk = ''

        return {'level': level, 'denomination': denom, 'risk': risk}

    def declarer(self) -> str:
        """
        Returns the seat ('N','E','S','W') of the player who first bid the final contract.
        """
        ctr = self.contract()
        if ctr['level'] == 0:
            return None
        bid_str = f"{ctr['level']}{ctr['denomination']}"
        for c in self.calls:
            if c['call'] == bid_str:
                return c['player']
        return None

    def reset(self):
        """Clear the auction state to start anew."""
        self.calls.clear()
        self.last_bid_idx = None


# bridge class that should work well with parsed pbn format
# actions are mostly in the format of parsed pbn format, but one caveat is
# auction and play input formats are different.
# You need to first convert the parsed pbn format's auction and play params into 'live' auction and play
# because this class will parse each action one by one and determine if its legal or not
class bridge():
    # spades, hearts, diamonds, clubs
    suits = ['C','D','H','S']
    ranks = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']
    seats = ['N','E','S','W']

    # Pass in actions to simulate each action for the match
    def __init__(self, actions=None):
        # setup cards, ordered by suit + rank
        self.cards = [s + r for s in self.suits for r in self.ranks]

        # game state
        self.actions = actions or []
        self.hands = {'N': [], 'E': [], 'S': [], 'W': []}
        self.dealer = None
        self.gameIndex = 0
        self.currentPhase = None
        self.vulnerable = None

        # auction state
        self.auction = None

        # info required for pbn format
        self.dealers = []
        self.vulnerables = []
        self.deals = []
        self.auctions = []
        self.contracts = []
        self.declarers = []
        self.results = []
        self.scores = []

        if not self.actions:
            # initialize a fresh match
            self.actions = [
                {'name':'Vulnerable','value':'None'},
                {'name':'Dealer','value':random.choice(self.seats)},
                self.generateDeal()
            ]
        for action in self.actions:
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
        try:
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
        except Exception as e:
            print('error during simulation', e)

    # {"name":"Auction", "player":"N", value:"1D"}
    def handleAuctionAction(self, action):
        # start phase if first call
        if self.currentPhase != 'Auction':
            self.currentPhase = 'Auction'
            # ensure fresh auction
            self.auction = Auction()
        finished = self.auction.add_call(action['player'], action['value'])
        # record every call to raw auction tokens
        # we'll snapshot full sequence at end
        if finished:
            # store completed auction
            self.auctions.append([c['call'] for c in self.auction.calls])
            # record contract & declarer
            ctr = self.auction.contract()
            self.contracts.append(ctr)
            self.declarers.append(self.auction.declarer())
            # clear phase
            self.currentPhase = None
        return

    def handleDealAction(self, action):
        for card in action['cards']:
            self.hands[card['seat']].append(card['suit'] + card['rank'])
        self.deals.append(action['cards'])
    
    def handleDealerAction(self, action):
        self.dealer = action['value']
        self.dealers.append(action['value'])

    def handlePlayAction(self, action):
        pass

    def handleVulnerableAction(self, action):
        self.vulnerable = action['value']
        self.vulnerables.append(action['value'])

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