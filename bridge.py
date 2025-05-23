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

# all denominations in order
DENOMS = ['C', 'D', 'H', 'S', 'NT']

# generate 1C–7NT
BIDS = [f"{level}{denom}" for level in range(1, 8) for denom in DENOMS]

VALID_AUCTION_ACTIONS = set(
    ['Pass', 'X', 'XX']  # pass, double, redouble
    + BIDS               # all valid level+denom bids
)

class ScoreCalculator:
    """
    Duplicate‐style scoring for one deal.
    Inputs:
      contract: dict with keys {'level':int, 'denomination':str or None, 'risk': ''|'X'|'XX'}
      declarer: str in 'N','E','S','W'
      made: int = number of tricks actually taken by declarer (0–13)
      vulnerable: 'None','NS','EW','All'
    Returns:
      (side:str, score:int)
    """
    # per‐trick values
    TRICK_SCORE = {
        'C': 20, 'D': 20,
        'H': 30, 'S': 30,
        'NT': None  # special: first trick=40, rest=30
    }

    def __init__(self, contract, declarer, made, vulnerable):
        self.level = contract['level']
        self.denom = contract['denomination']
        self.risk = contract['risk']
        self.declarer = declarer
        self.made = made
        self.vul = vulnerable  # 'None','NS','EW','All'

    def declarer_side(self):
        return 'NS' if self.declarer in ('N','S') else 'EW'

    def is_vulnerable(self):
        # self.vul is one of 'None','NS','EW','All'
        return (self.vul == 'All') or (self.vul == self.declarer_side())

    def pbn_score(self) -> str:
        """
        Returns the PBN 'Score' tag string,
        i.e. always from NS's perspective: "NS <number>"
        (negative if NS lost).
        """
        side, pts = self.score()
        # if EW won, NS lost ⇒ negative
        ns_pts = pts if side == 'NS' else -pts
        return f"NS {ns_pts}"

    def score(self):
        """Compute (side, points). Positive points to winners."""
        # PASS‐OUT
        if self.level == 0:
            return (None, 0)

        vul = self.is_vulnerable()
        tricks_needed = 6 + self.level
        over_under = self.made - tricks_needed

        # made the contract
        if over_under >= 0:
            trick_pts = 0
            # base trick score
            if self.denom == 'NT':
                trick_pts = 40 + 30 * (self.level - 1)
            else:
                trick_pts = self.TRICK_SCORE[self.denom] * self.level

            # doubled/redoubled
            mult = 1
            if self.risk == 'X':
                trick_pts *= 2
                mult = 2
            elif self.risk == 'XX':
                trick_pts *= 4
                mult = 4

            total = trick_pts

            # insult bonus for making a doubled contract
            if mult > 1:
                total += 50 * mult  # 50 for a double, 100 for redouble

            # game/slam bonus
            if trick_pts >= 100:
                total += 500 if vul else 300
            else:
                total += 50  # part‐score bonus

            # slam bonuses
            if self.level == 6:
                total += 750 if vul else 500
            elif self.level == 7:
                total += 1500 if vul else 1000

            # overtricks
            if self.risk == '':
                # undoubled: same per‐trick score as suit
                ovpt = self.TRICK_SCORE[self.denom] if self.denom != 'NT' else 30
                total += ovpt * over_under
            else:
                # doubled/redoubled overtricks
                if vul:
                    ov_val = 200
                else:
                    ov_val = 100
                if self.risk == 'XX':
                    ov_val *= 2
                total += ov_val * over_under

            return (self.declarer_side(), total)

        # went down
        vul = self.is_vulnerable()
        down = -over_under
        penalty = 0
        if self.risk == '':
            # undoubled
            penalty = 100 * down if vul else 50 * down
        else:
            # doubled or redoubled
            # step penalties
            if not vul:
                # first undertrick 100, next two 200, then 300+
                steps = [100, 200, 200]
            else:
                # vulnerable: all undertricks 200 then 300
                steps = [200, 300, 300]
            for i in range(down):
                penalty += steps[i] if i < len(steps) else 300
            if self.risk == 'XX':
                penalty *= 2

        # defenders get the points
        defenders = 'EW' if self.declarer_side() == 'NS' else 'NS'
        return (defenders, penalty)

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

        # Double: can follow any number of Passes, as long as the
        # last non-Pass call was a bid by an opponent
        if call == 'X':
            # find last non-Pass call
            for prev in reversed(self.calls):
                if prev['call'] != 'Pass':
                    last = prev
                    break
            else:
                return False   # no bid to double

            # must be a level+denom bid (not a Double or Redouble)
            if len(last['call']) < 2 or not last['call'][0].isdigit():
                return False

            # must be your opponent
            return last['player'] != player

        # Redouble: same idea, but the last non-Pass must have been an X by opponent
        if call == 'XX':
            for prev in reversed(self.calls):
                if prev['call'] != 'Pass':
                    last = prev
                    break
            else:
                return False   # no double to redouble

            if last['call'] != 'X':
                return False

            return last['player'] != player

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
        """True if auction has ended: pass‑out or three consecutive Passes after last real bid."""
        # 1) Pass‑out: dealer + 3 others all Pass
        if self.last_bid_idx is None and len(self.calls) >= 4:
            if all(c['call'] == 'Pass' for c in self.calls[:4]):
                return True

        # 2) Normal close: need at least 3 consecutive Pass calls after the last bid
        if self.last_bid_idx is not None:
            # extract calls _after_ the last real bid
            after = [c['call'] for c in self.calls[self.last_bid_idx+1:]]
            # check that the last three are all Pass
            if len(after) >= 3 and all(call == 'Pass' for call in after[-3:]):
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
        Returns the seat ('N','E','S','W') of the first player in the
        declaring partnership who bid the final contract's denomination.
        """
        if not self.is_finished():
            raise RuntimeError("Auction not finished yet")

        ctr = self.contract()
        # pass‑out
        if ctr['level'] == 0:
            return None

        # determine which side won the contract
        last = self.calls[self.last_bid_idx]
        winning_side = {'N','S'} if last['player'] in ('N','S') else {'E','W'}

        suit = ctr['denomination']  # e.g. 'S', 'H', 'NT', etc.

        # find the first bid of that suit by the winning side
        for c in self.calls:
            bid = c['call']
            if bid in ('Pass','X','XX'):
                continue
            # extract this bid's denomination (everything after the level digit)
            this_suit = bid[1:]
            if this_suit == suit and c['player'] in winning_side:
                return c['player']

        return None

class Trick:
    RANKS = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']
    SEATS = ['N','E','S','W']
    """Manages one trick of four cards, enforcing turn order and follow‐suit."""
    def __init__(self, trump: str=None, leader: str=None):
        self.trump = trump            # e.g. 'S' or None
        self.leader = leader          # e.g. 'N','E','S','W'
        self.cards = []               # list of {'player','card'} dicts

    def next_player(self) -> str:
        """Who should play next in this trick?"""
        idx = self.SEATS.index(self.leader)
        # offset by how many cards have already been played
        return self.SEATS[(idx + len(self.cards)) % 4]

    def add_card(self, player: str, card: str, hands: dict) -> bool:
        # 1) correct turn
        expected = self.next_player()
        if player != expected:
            raise ValueError(f"It’s {expected}’s turn, not {player}")

        # 2) verify card in hand
        if card not in hands[player]:
            raise ValueError(f"Player {player} does not have {card}")

        # 3) follow suit if possible
        suit = card[0]
        if self.cards:
            lead_suit = self.cards[0]['card'][0]
            # if you have any lead‐suit cards, you must follow
            if any(c[0] == lead_suit for c in hands[player]) and suit != lead_suit:
                raise ValueError(f"Must follow {lead_suit} suit")

        # 4) play the card
        hands[player].remove(card)
        self.cards.append({'player': player, 'card': card})
        return len(self.cards) == 4

    def winner(self) -> str:
        """Return who won the completed trick."""
        lead_suit = self.cards[0]['card'][0]

        def score(entry):
            s, r = entry['card'][0], entry['card'][1]
            rank_value = self.RANKS.index(r)
            # trump outranks everything
            if self.trump and s == self.trump:
                return (2, rank_value)
            # next highest is following the lead suit
            if s == lead_suit:
                return (1, rank_value)
            # else, you’re out of suit and not trump
            return (0, rank_value)

        winner_entry = max(self.cards, key=score)
        return winner_entry['player']

# bridge class that should work well with parsed pbn format
# actions are mostly in the format of parsed pbn format, but one caveat is
# auction and play input formats are different.
# You need to first convert the parsed pbn format's auction and play params into 'live' auction and play
# because this class will parse each action one by one and determine if its legal or not
class Bridge():
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
        self.currentTrick = None

        # auction state
        self.auction = None

        # info required for pbn format
        self.dealers = []
        self.vulnerables = []
        self.deals = []
        self.auctions = []
        self.contracts = []
        self.declarers = []
        self.tricks = []
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
        if action['value'] not in VALID_AUCTION_ACTIONS:
            return
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
            # go to play phase
            self.currentPhase = 'Play'
            decl = self.declarers[-1]
            decl_idx = self.seats.index(decl)
            # leader is left of declarer
            self.leader = self.seats[(decl_idx + 1) % 4]
            trump = self.contracts[-1]['denomination']
            self.currentTrick = Trick(trump=trump, leader=self.leader)
            self.tricks.append(self.currentTrick)
            self.results.append(0)
        return

    def handleDealAction(self, action):
        for card in action['cards']:
            self.hands[card['seat']].append(card['suit'] + card['rank'])
        self.deals.append(action['cards'])
    
    def handleDealerAction(self, action):
        self.dealer = action['value']
        self.dealers.append(action['value'])

    def handlePlayAction(self, action):
        if action['value'] == '*':
            return
        player, card = action['player'], action['value']

        # attempt to add the card (will enforce turn + follow‐suit)
        trick_done = self.currentTrick.add_card(player, card, self.hands)

        if trick_done:
            # determine who wins, and make them the new leader
            winner = self.currentTrick.winner()
            self.leader = winner
            teams = ['NS', 'EW']
            declarer = self.declarers[-1][0]
            if (winner in teams[0] and declarer in teams[0]) or (winner in teams[1] and declarer in teams[1]):
                self.results[-1] += 1

            # start the next trick, with the same trump but new leader
            trump = self.contracts[-1]['denomination']
            self.currentTrick = Trick(trump=trump, leader=self.leader)
            if len(self.tricks) == 13:
                ctr = self.contracts[-1]
                decl = self.declarers[-1]
                made = self.results[-1]
                vul = self.vulnerable

                sc = ScoreCalculator(ctr, decl, made, vul)
                self.scores.append(sc.pbn_score())
            else:
                self.tricks.append(self.currentTrick)

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

b = Bridge()
