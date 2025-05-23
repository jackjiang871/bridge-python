import random

DENOMS = ['C', 'D', 'H', 'S', 'NT']
BIDS = [f"{level}{denom}" for level in range(1, 8) for denom in DENOMS]
VALID_AUCTION_ACTIONS = set(['Pass', 'X', 'XX'] + BIDS)

class ScoreCalculator:
    TRICK_SCORE = {'C': 20, 'D': 20, 'H': 30, 'S': 30, 'NT': None}

    def __init__(self, contract, declarer, made, vulnerable):
        if not isinstance(contract, dict):
            raise ValueError("Contract must be a dictionary")
        if not isinstance(made, int) or made < 0 or made > 13:
            raise ValueError("Made tricks must be an integer between 0 and 13")
        
        self.level = contract.get('level', 0)
        self.denom = contract.get('denomination')
        self.risk = contract.get('risk', '')
        self.declarer = declarer
        self.made = made
        self.vul = vulnerable

        # Validate inputs
        if self.level < 0 or self.level > 7:
            raise ValueError("Contract level must be between 0 and 7")
        if self.denom and self.denom not in ['C', 'D', 'H', 'S', 'NT']:
            raise ValueError("Invalid denomination")
        if self.risk not in ['', 'X', 'XX']:
            raise ValueError("Invalid risk level")
        if self.declarer and self.declarer not in ['N', 'E', 'S', 'W']:
            raise ValueError("Invalid declarer")

    def declarer_side(self):
        if not self.declarer:
            return None
        return 'NS' if self.declarer in ('N','S') else 'EW'

    def is_vulnerable(self):
        if not self.vul or not self.declarer_side():
            return False
        return (self.vul == 'All') or (self.vul == self.declarer_side())

    def pbn_score(self) -> str:
        side, pts = self.score()
        if side is None:
            return "NS 0"
        ns_pts = pts if side == 'NS' else -pts
        return f"NS {ns_pts}"

    def score(self):
        if self.level == 0 or not self.declarer:
            return (None, 0)

        vul = self.is_vulnerable()
        tricks_needed = 6 + self.level
        over_under = self.made - tricks_needed

        if over_under >= 0:
            # Made the contract
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

            # Double/redouble bonus
            if mult > 1:
                total += 50 * mult

            # Game/part-game bonus
            if trick_pts >= 100:
                total += 500 if vul else 300
            else:
                total += 50

            # Slam bonuses
            if self.level == 6:  # Small slam
                total += 750 if vul else 500
            elif self.level == 7:  # Grand slam
                total += 1500 if vul else 1000

            # Overtricks
            if over_under > 0:
                if self.risk == '':
                    ovpt = self.TRICK_SCORE[self.denom] if self.denom != 'NT' else 30
                    total += ovpt * over_under
                else:
                    ov_val = 200 if vul else 100
                    if self.risk == 'XX':
                        ov_val *= 2
                    total += ov_val * over_under

            return (self.declarer_side(), total)
        else:
            # Failed the contract
            down = -over_under
            penalty = 0
            
            if self.risk == '':
                penalty = (100 if vul else 50) * down
            else:
                # Doubled penalties
                if vul:
                    steps = [200, 300, 300]
                else:
                    steps = [100, 200, 200]
                
                for i in range(down):
                    if i < len(steps):
                        penalty += steps[i]
                    else:
                        penalty += 300
                
                if self.risk == 'XX':
                    penalty *= 2

            defenders = 'EW' if self.declarer_side() == 'NS' else 'NS'
            return (defenders, penalty)

class Auction:
    DENOMINATIONS = ['C', 'D', 'H', 'S', 'NT']
    LEVELS = list(range(1, 8))
    VALID_PLAYERS = ['N', 'E', 'S', 'W']

    def __init__(self, dealer='N'):
        if dealer not in self.VALID_PLAYERS:
            raise ValueError("Invalid dealer")
        self.calls = []
        self.last_bid_idx = None
        self.dealer = dealer

    def current_player(self):
        """Get the current player to call"""
        if not self.calls:
            return self.dealer
        
        dealer_idx = self.VALID_PLAYERS.index(self.dealer)
        call_count = len(self.calls)
        current_idx = (dealer_idx + call_count) % 4
        return self.VALID_PLAYERS[current_idx]

    @classmethod
    def _bid_value(cls, bid_str: str) -> int:
        if not bid_str or len(bid_str) < 2:
            return -1
        try:
            level = int(bid_str[0])
            denom = bid_str[1:]
            if level not in cls.LEVELS or denom not in cls.DENOMINATIONS:
                return -1
            denom_index = cls.DENOMINATIONS.index(denom)
            return (level - 1) * len(cls.DENOMINATIONS) + denom_index
        except (ValueError, IndexError):
            return -1

    def is_valid_call(self, player: str, call: str) -> bool:
        # Validate player
        if player not in self.VALID_PLAYERS:
            return False
            
        # Check if it's this player's turn
        if player != self.current_player():
            return False
            
        # Validate call format
        if not isinstance(call, str):
            return False

        if call == 'Pass':
            return True

        if call == 'X':
            # Find the last non-pass call
            last_non_pass = None
            for prev in reversed(self.calls):
                if prev['call'] != 'Pass':
                    last_non_pass = prev
                    break
            
            if not last_non_pass:
                return False

            # Must be a bid (not X or XX)
            if last_non_pass['call'] in ('X', 'XX'):
                return False
                
            # Can't double your own side's bid
            doubler_side = {'N', 'S'} if player in ('N', 'S') else {'E', 'W'}
            bidder_side = {'N', 'S'} if last_non_pass['player'] in ('N', 'S') else {'E', 'W'}
            
            return doubler_side != bidder_side

        if call == 'XX':
            # Find the last non-pass call
            last_non_pass = None
            for prev in reversed(self.calls):
                if prev['call'] != 'Pass':
                    last_non_pass = prev
                    break
            
            if not last_non_pass or last_non_pass['call'] != 'X':
                return False

            # Can redouble your own side's doubled bid
            redoubler_side = {'N', 'S'} if player in ('N', 'S') else {'E', 'W'}
            doubler_side = {'N', 'S'} if last_non_pass['player'] in ('N', 'S') else {'E', 'W'}
            
            return redoubler_side != doubler_side

        # Validate bid format and level
        bid_value = self._bid_value(call)
        if bid_value == -1:
            return False
            
        # Must be higher than last bid
        if self.last_bid_idx is not None:
            last_bid = self.calls[self.last_bid_idx]['call']
            last_value = self._bid_value(last_bid)
            if bid_value <= last_value:
                return False
                
        return True

    def add_call(self, player: str, call: str) -> bool:
        if not self.is_valid_call(player, call):
            raise ValueError(f"Illegal call {call!r} by {player}")

        self.calls.append({'player': player, 'call': call})
        
        # Update last bid index if this is a bid
        if call not in ('Pass', 'X', 'XX'):
            self.last_bid_idx = len(self.calls) - 1

        return self.is_finished()

    def is_finished(self) -> bool:
        # Need at least 4 calls
        if len(self.calls) < 4:
            return False
            
        # All pass out (4 passes in a row from the start)
        if self.last_bid_idx is None:
            return all(c['call'] == 'Pass' for c in self.calls[:4])

        # Three passes after the last bid
        calls_after_bid = self.calls[self.last_bid_idx + 1:]
        if len(calls_after_bid) >= 3:
            return all(c['call'] == 'Pass' for c in calls_after_bid[-3:])

        return False

    def contract(self) -> dict:
        if not self.is_finished():
            raise RuntimeError("Auction not finished yet")

        # All pass - no contract
        if self.last_bid_idx is None:
            return {'level': 0, 'denomination': None, 'risk': ''}

        last_bid = self.calls[self.last_bid_idx]
        level = int(last_bid['call'][0])
        denom = last_bid['call'][1:]
        
        # Check for doubles/redoubles after the last bid
        calls_after = self.calls[self.last_bid_idx + 1:]
        risk = ''
        for call in calls_after:
            if call['call'] == 'X':
                risk = 'X'
            elif call['call'] == 'XX':
                risk = 'XX'

        return {'level': level, 'denomination': denom, 'risk': risk}

    def declarer(self) -> str:
        if not self.is_finished():
            raise RuntimeError("Auction not finished yet")

        contract = self.contract()
        if contract['level'] == 0:
            return None

        # Find the winning side
        last_bid = self.calls[self.last_bid_idx]
        winning_side = {'N', 'S'} if last_bid['player'] in ('N', 'S') else {'E', 'W'}
        trump_suit = contract['denomination']

        # Find the first player from the winning side to bid this trump suit
        for call in self.calls:
            if call['call'] in ('Pass', 'X', 'XX'):
                continue
                
            bid_suit = call['call'][1:]
            if bid_suit == trump_suit and call['player'] in winning_side:
                return call['player']

        return None

class Trick:
    RANKS = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']
    SEATS = ['N','E','S','W']

    def __init__(self, trump: str = None, leader: str = None):
        if leader and leader not in self.SEATS:
            raise ValueError("Invalid leader")
        if trump and trump not in ['C', 'D', 'H', 'S']:
            raise ValueError("Invalid trump suit")
            
        self.trump = trump
        self.leader = leader
        self.cards = []

    def next_player(self) -> str:
        if not self.leader:
            raise RuntimeError("No leader set for trick")
        idx = self.SEATS.index(self.leader)
        return self.SEATS[(idx + len(self.cards)) % 4]

    def add_card(self, player: str, card: str, hands: dict) -> bool:
        # Validate inputs
        if player not in self.SEATS:
            raise ValueError(f"Invalid player: {player}")
        if not isinstance(card, str) or len(card) != 2:
            raise ValueError(f"Invalid card format: {card}")
        if card[0] not in ['C', 'D', 'H', 'S'] or card[1] not in self.RANKS:
            raise ValueError(f"Invalid card: {card}")
        if player not in hands:
            raise ValueError(f"No hand found for player {player}")
        if not isinstance(hands[player], list):
            raise ValueError(f"Invalid hand format for player {player}")

        expected = self.next_player()
        if player != expected:
            raise ValueError(f"It's {expected}'s turn, not {player}")

        if card not in hands[player]:
            raise ValueError(f"Player {player} does not have {card}")

        # Check suit following
        suit = card[0]
        if self.cards:
            lead_suit = self.cards[0]['card'][0]
            player_has_lead_suit = any(c[0] == lead_suit for c in hands[player])
            if player_has_lead_suit and suit != lead_suit:
                raise ValueError(f"Must follow {lead_suit} suit")

        hands[player].remove(card)
        self.cards.append({'player': player, 'card': card})
        return len(self.cards) == 4

    def winner(self) -> str:
        if len(self.cards) != 4:
            raise RuntimeError("Trick not complete")
            
        lead_suit = self.cards[0]['card'][0]

        def card_score(entry):
            suit, rank = entry['card'][0], entry['card'][1]
            try:
                rank_value = self.RANKS.index(rank)
            except ValueError:
                rank_value = 0
                
            if self.trump and suit == self.trump:
                return (2, rank_value)  # Trump cards
            elif suit == lead_suit:
                return (1, rank_value)  # Lead suit
            else:
                return (0, rank_value)  # Other suits

        winner_entry = max(self.cards, key=card_score)
        return winner_entry['player']

class Bridge:
    SUITS = ['C', 'D', 'H', 'S']
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    SEATS = ['N', 'E', 'S', 'W']
    VALID_VULNERABILITY = ['None', 'NS', 'EW', 'All']

    def __init__(self, actions=None):
        self.cards = [s + r for s in self.SUITS for r in self.RANKS]
        self.actions = actions or []
        self.hands = {'N': [], 'E': [], 'S': [], 'W': []}
        self.dealer = None
        self.game_index = 0
        self.current_phase = 'Setup'
        self.vulnerable = None
        self.current_trick = None
        self.auction = None
        
        # Game history
        self.dealers = []
        self.vulnerables = []
        self.deals = []
        self.auctions = []
        self.contracts = []
        self.declarers = []
        self.tricks = []
        self.results = []
        self.scores = []

        # Initialize with default actions if none provided
        if not self.actions:
            self.actions = [
                {'name': 'Vulnerable', 'value': 'None'},
                {'name': 'Dealer', 'value': random.choice(self.SEATS)},
                self.generate_deal()
            ]
            
        # Process initial actions
        for action in self.actions:
            self.simulate(action)

    def generate_deal(self):
        """Generate a random deal"""
        shuffled_cards = random.sample(self.cards, k=len(self.cards))
        dealt_cards = []
        
        # Deal 13 cards to each player
        for i, seat in enumerate(['N', 'W', 'S', 'E']):  # Standard dealing order
            start_idx = i * 13
            end_idx = start_idx + 13
            for card in shuffled_cards[start_idx:end_idx]:
                dealt_cards.append({
                    'seat': seat, 
                    'suit': card[0], 
                    'rank': card[1]
                })
                
        return {'name': 'Deal', 'cards': dealt_cards}

    def validate_action(self, action):
        """Validate action format and content"""
        if not isinstance(action, dict):
            raise ValueError("Action must be a dictionary")
        if 'name' not in action:
            raise ValueError("Action must have a 'name' field")
        if action['name'] not in ['Auction', 'Deal', 'Dealer', 'Play', 'Vulnerable']:
            raise ValueError(f"Invalid action name: {action['name']}")

    def simulate(self, action):
        """Simulate a single action with error handling"""
        try:
            self.validate_action(action)
            
            if action['name'] == 'Auction':
                self.handle_auction_action(action)
            elif action['name'] == 'Deal':
                self.handle_deal_action(action)
            elif action['name'] == 'Dealer':
                self.handle_dealer_action(action)
            elif action['name'] == 'Play':
                self.handle_play_action(action)
            elif action['name'] == 'Vulnerable':
                self.handle_vulnerable_action(action)
                
        except Exception as e:
            print(f'Error during simulation of {action}: {e}')
            raise

    def handle_auction_action(self, action):
        """Handle auction calls"""
        if 'player' not in action or 'value' not in action:
            raise ValueError("Auction action must have 'player' and 'value' fields")
            
        if self.current_phase not in ['Setup', 'Auction']:
            raise ValueError(f"Cannot auction in phase: {self.current_phase}")
            
        if self.current_phase == 'Setup':
            if not self.dealer:
                raise ValueError("Dealer must be set before auction")
            self.current_phase = 'Auction'
            self.auction = Auction(self.dealer)

        player = action['player']
        call = action['value']
        
        if player not in self.SEATS:
            raise ValueError(f"Invalid player: {player}")
        if call not in VALID_AUCTION_ACTIONS:
            raise ValueError(f"Invalid auction call: {call}")

        finished = self.auction.add_call(player, call)
        
        if finished:
            # Store auction results
            self.auctions.append([c['call'] for c in self.auction.calls])
            contract = self.auction.contract()
            self.contracts.append(contract)
            declarer = self.auction.declarer()
            self.declarers.append(declarer)
            
            # Start play phase if there's a contract
            if contract['level'] > 0:
                self.current_phase = 'Play'
                decl_idx = self.SEATS.index(declarer)
                self.leader = self.SEATS[(decl_idx + 1) % 4]  # Left of declarer leads
                trump = contract['denomination'] if contract['denomination'] != 'NT' else None
                self.current_trick = Trick(trump=trump, leader=self.leader)
                self.tricks = [self.current_trick]
                self.results.append(0)  # Tricks made by declaring side
            else:
                # All pass - game over
                self.current_phase = 'Finished'
                self.scores.append("NS 0")

    def handle_deal_action(self, action):
        """Handle deal cards"""
        if 'cards' not in action:
            raise ValueError("Deal action must have 'cards' field")
            
        if self.current_phase != 'Setup':
            raise ValueError("Can only deal in setup phase")

        cards = action['cards']
        if not isinstance(cards, list) or len(cards) != 52:
            raise ValueError("Deal must contain exactly 52 cards")

        # Clear existing hands
        for seat in self.SEATS:
            self.hands[seat] = []

        # Distribute cards
        seat_counts = {'N': 0, 'E': 0, 'S': 0, 'W': 0}
        for card_info in cards:
            if not isinstance(card_info, dict):
                raise ValueError("Each card must be a dictionary")
            if 'seat' not in card_info or 'suit' not in card_info or 'rank' not in card_info:
                raise ValueError("Card must have 'seat', 'suit', and 'rank' fields")
                
            seat = card_info['seat']
            suit = card_info['suit']
            rank = card_info['rank']
            
            if seat not in self.SEATS:
                raise ValueError(f"Invalid seat: {seat}")
            if suit not in self.SUITS:
                raise ValueError(f"Invalid suit: {suit}")
            if rank not in self.RANKS:
                raise ValueError(f"Invalid rank: {rank}")
                
            card = suit + rank
            if card in [c for hand in self.hands.values() for c in hand]:
                raise ValueError(f"Duplicate card: {card}")
                
            self.hands[seat].append(card)
            seat_counts[seat] += 1

        # Verify each player has exactly 13 cards
        for seat, count in seat_counts.items():
            if count != 13:
                raise ValueError(f"Player {seat} has {count} cards, should have 13")

        self.deals.append(cards)

    def handle_dealer_action(self, action):
        """Handle dealer selection"""
        if 'value' not in action:
            raise ValueError("Dealer action must have 'value' field")
            
        dealer = action['value']
        if dealer not in self.SEATS:
            raise ValueError(f"Invalid dealer: {dealer}")
            
        self.dealer = dealer
        self.dealers.append(dealer)

    def handle_play_action(self, action):
        """Handle card play"""
        if self.current_phase != 'Play':
            raise ValueError("Can only play cards in play phase")
            
        if 'player' not in action or 'value' not in action:
            raise ValueError("Play action must have 'player' and 'value' fields")

        if action['value'] == '*':  # Skip/dummy action
            return

        player = action['player']
        card = action['value']
        
        if player not in self.SEATS:
            raise ValueError(f"Invalid player: {player}")

        trick_done = self.current_trick.add_card(player, card, self.hands)

        if trick_done:
            winner = self.current_trick.winner()
            self.leader = winner
            
            # Update tricks won by declaring side
            declaring_side = {'N', 'S'} if self.declarers[-1] in ('N', 'S') else {'E', 'W'}
            if winner in declaring_side:
                self.results[-1] += 1

            # Check if this was the last trick
            if len([t for t in self.tricks if len(t.cards) == 4]) == 13:
                # Calculate final score
                contract = self.contracts[-1]
                declarer = self.declarers[-1]
                made = self.results[-1]
                
                if contract['level'] > 0:
                    sc = ScoreCalculator(contract, declarer, made, self.vulnerable)
                    self.scores.append(sc.pbn_score())
                else:
                    self.scores.append("NS 0")
                    
                self.current_phase = 'Finished'
            else:
                # Start next trick
                trump = self.contracts[-1]['denomination'] if self.contracts[-1]['denomination'] != 'NT' else None
                self.current_trick = Trick(trump=trump, leader=self.leader)
                self.tricks.append(self.current_trick)

    def handle_vulnerable_action(self, action):
        """Handle vulnerability setting"""
        if 'value' not in action:
            raise ValueError("Vulnerable action must have 'value' field")
            
        vuln = action['value']
        if vuln not in self.VALID_VULNERABILITY:
            raise ValueError(f"Invalid vulnerability: {vuln}")
            
        self.vulnerable = vuln
        self.vulnerables.append(vuln)

    def get_state(self):
        """Get current game state for debugging"""
        return {
            'phase': self.current_phase,
            'dealer': self.dealer,
            'vulnerable': self.vulnerable,
            'hands': {k: sorted(v) for k, v in self.hands.items()},
            'auction_calls': [c['call'] for c in self.auction.calls] if self.auction else [],
            'current_player': self.auction.current_player() if self.auction and self.current_phase == 'Auction' else None,
            'contract': self.contracts[-1] if self.contracts else None,
            'declarer': self.declarers[-1] if self.declarers else None,
            'tricks_made': self.results[-1] if self.results else None,
            'scores': self.scores
        }