import random

DENOMS = ['C', 'D', 'H', 'S', 'NT']
BIDS = [f"{level}{denom}" for level in range(1, 8) for denom in DENOMS]
VALID_AUCTION_ACTIONS = set(['Pass', 'X', 'XX'] + BIDS)

class ScoreCalculator:
    TRICK_SCORE = {'C': 20, 'D': 20, 'H': 30, 'S': 30, 'NT': None}

    def __init__(self, contract, declarer, made, vulnerable):
        self.level = contract['level']
        self.denom = contract['denomination']
        self.risk = contract['risk']
        self.declarer = declarer
        self.made = made
        self.vul = vulnerable

    def declarer_side(self):
        return 'NS' if self.declarer in ('N','S') else 'EW'

    def is_vulnerable(self):
        return (self.vul == 'All') or (self.vul == self.declarer_side())

    def pbn_score(self) -> str:
        side, pts = self.score()
        ns_pts = pts if side == 'NS' else -pts
        return f"NS {ns_pts}"

    def score(self):
        if self.level == 0:
            return (None, 0)

        vul = self.is_vulnerable()
        tricks_needed = 6 + self.level
        over_under = self.made - tricks_needed

        if over_under >= 0:
            trick_pts = 0
            if self.denom == 'NT':
                trick_pts = 40 + 30 * (self.level - 1)
            else:
                trick_pts = self.TRICK_SCORE[self.denom] * self.level

            mult = 1
            if self.risk == 'X':
                trick_pts *= 2
                mult = 2
            elif self.risk == 'XX':
                trick_pts *= 4
                mult = 4

            total = trick_pts

            if mult > 1:
                total += 50 * mult

            if trick_pts >= 100:
                total += 500 if vul else 300
            else:
                total += 50

            if self.level == 6:
                total += 750 if vul else 500
            elif self.level == 7:
                total += 1500 if vul else 1000

            if self.risk == '':
                ovpt = self.TRICK_SCORE[self.denom] if self.denom != 'NT' else 30
                total += ovpt * over_under
            else:
                ov_val = 200 if vul else 100
                if self.risk == 'XX':
                    ov_val *= 2
                total += ov_val * over_under

            return (self.declarer_side(), total)

        vul = self.is_vulnerable()
        down = -over_under
        penalty = 0
        if self.risk == '':
            penalty = 100 * down if vul else 50 * down
        else:
            steps = [100, 200, 200] if not vul else [200, 300, 300]
            for i in range(down):
                penalty += steps[i] if i < len(steps) else 300
            if self.risk == 'XX':
                penalty *= 2

        defenders = 'EW' if self.declarer_side() == 'NS' else 'NS'
        return (defenders, penalty)

class Auction:
    DENOMINATIONS = ['C', 'D', 'H', 'S', 'NT']
    LEVELS = list(range(1, 8))

    def __init__(self):
        self.calls = []
        self.last_bid_idx = None

    @classmethod
    def _bid_value(cls, bid_str: str) -> int:
        level = int(bid_str[0])
        denom = bid_str[1:]
        denom_index = cls.DENOMINATIONS.index(denom)
        return (level - 1) * len(cls.DENOMINATIONS) + denom_index

    def is_valid_call(self, player: str, call: str) -> bool:
        if call == 'Pass':
            return True

        if call == 'X':
            for prev in reversed(self.calls):
                if prev['call'] != 'Pass':
                    last = prev
                    break
            else:
                return False

            if len(last['call']) < 2 or not last['call'][0].isdigit():
                return False

            return last['player'] != player

        if call == 'XX':
            for prev in reversed(self.calls):
                if prev['call'] != 'Pass':
                    last = prev
                    break
            else:
                return False

            if last['call'] != 'X':
                return False

            return last['player'] != player

        if len(call) < 2 or not call[0].isdigit():
            return False
        level = int(call[0])
        denom = call[1:]
        if level not in self.LEVELS or denom not in self.DENOMINATIONS:
            return False
        if self.last_bid_idx is not None:
            last = self.calls[self.last_bid_idx]['call']
            if self._bid_value(call) <= self._bid_value(last):
                return False
        return True

    def add_call(self, player: str, call: str) -> bool:
        if not self.is_valid_call(player, call):
            raise ValueError(f"Illegal call {call!r} by {player}")

        self.calls.append({'player': player, 'call': call})
        idx = len(self.calls) - 1
        if call not in ('Pass', 'X', 'XX'):
            self.last_bid_idx = idx

        return self.is_finished()

    def is_finished(self) -> bool:
        if self.last_bid_idx is None and len(self.calls) >= 4:
            if all(c['call'] == 'Pass' for c in self.calls[:4]):
                return True

        if self.last_bid_idx is not None:
            after = [c['call'] for c in self.calls[self.last_bid_idx+1:]]
            if len(after) >= 3 and all(call == 'Pass' for call in after[-3:]):
                return True

        return False

    def contract(self) -> dict:
        if not self.is_finished():
            raise RuntimeError("Auction not finished yet")

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
        if not self.is_finished():
            raise RuntimeError("Auction not finished yet")

        ctr = self.contract()
        if ctr['level'] == 0:
            return None

        last = self.calls[self.last_bid_idx]
        winning_side = {'N','S'} if last['player'] in ('N','S') else {'E','W'}
        suit = ctr['denomination']

        for c in self.calls:
            bid = c['call']
            if bid in ('Pass','X','XX'):
                continue
            this_suit = bid[1:]
            if this_suit == suit and c['player'] in winning_side:
                return c['player']

        return None

class Trick:
    RANKS = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']
    SEATS = ['N','E','S','W']

    def __init__(self, trump: str=None, leader: str=None):
        self.trump = trump
        self.leader = leader
        self.cards = []

    def next_player(self) -> str:
        idx = self.SEATS.index(self.leader)
        return self.SEATS[(idx + len(self.cards)) % 4]

    def add_card(self, player: str, card: str, hands: dict) -> bool:
        expected = self.next_player()
        if player != expected:
            raise ValueError(f"It's {expected}'s turn, not {player}")

        if card not in hands[player]:
            raise ValueError(f"Player {player} does not have {card}")

        suit = card[0]
        if self.cards:
            lead_suit = self.cards[0]['card'][0]
            if any(c[0] == lead_suit for c in hands[player]) and suit != lead_suit:
                raise ValueError(f"Must follow {lead_suit} suit")

        hands[player].remove(card)
        self.cards.append({'player': player, 'card': card})
        return len(self.cards) == 4

    def winner(self) -> str:
        lead_suit = self.cards[0]['card'][0]

        def score(entry):
            s, r = entry['card'][0], entry['card'][1]
            rank_value = self.RANKS.index(r)
            if self.trump and s == self.trump:
                return (2, rank_value)
            if s == lead_suit:
                return (1, rank_value)
            return (0, rank_value)

        winner_entry = max(self.cards, key=score)
        return winner_entry['player']

class Bridge():
    suits = ['C','D','H','S']
    ranks = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']
    seats = ['N','E','S','W']

    def __init__(self, actions=None):
        self.cards = [s + r for s in self.suits for r in self.ranks]
        self.actions = actions or []
        self.hands = {'N': [], 'E': [], 'S': [], 'W': []}
        self.dealer = None
        self.gameIndex = 0
        self.currentPhase = None
        self.vulnerable = None
        self.currentTrick = None
        self.auction = None
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

    def handleAuctionAction(self, action):
        if self.currentPhase != 'Auction':
            self.currentPhase = 'Auction'
            self.auction = Auction()
        if action['value'] not in VALID_AUCTION_ACTIONS:
            return
        finished = self.auction.add_call(action['player'], action['value'])
        if finished:
            self.auctions.append([c['call'] for c in self.auction.calls])
            ctr = self.auction.contract()
            self.contracts.append(ctr)
            self.declarers.append(self.auction.declarer())
            self.currentPhase = 'Play'
            decl = self.declarers[-1]
            decl_idx = self.seats.index(decl)
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

        trick_done = self.currentTrick.add_card(player, card, self.hands)

        if trick_done:
            winner = self.currentTrick.winner()
            self.leader = winner
            teams = ['NS', 'EW']
            declarer = self.declarers[-1][0]
            if (winner in teams[0] and declarer in teams[0]) or (winner in teams[1] and declarer in teams[1]):
                self.results[-1] += 1

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
