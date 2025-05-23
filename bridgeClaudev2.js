const DENOMS = ['C', 'D', 'H', 'S', 'NT'];
const BIDS = [];
for (let level = 1; level <= 7; level++) {
    for (const denom of DENOMS) {
        BIDS.push(`${level}${denom}`);
    }
}
const VALID_AUCTION_ACTIONS = new Set(['Pass', 'X', 'XX', ...BIDS]);

class ScoreCalculator {
    static TRICK_SCORE = { 'C': 20, 'D': 20, 'H': 30, 'S': 30, 'NT': null };

    constructor(contract, declarer, made, vulnerable) {
        if (typeof contract !== 'object' || contract === null) {
            throw new Error("Contract must be an object");
        }
        if (!Number.isInteger(made) || made < 0 || made > 13) {
            throw new Error("Made tricks must be an integer between 0 and 13");
        }
        
        this.level = contract.level || 0;
        this.denom = contract.denomination;
        this.risk = contract.risk || '';
        this.declarer = declarer;
        this.made = made;
        this.vul = vulnerable;

        // Validate inputs
        if (this.level < 0 || this.level > 7) {
            throw new Error("Contract level must be between 0 and 7");
        }
        if (this.denom && !['C', 'D', 'H', 'S', 'NT'].includes(this.denom)) {
            throw new Error("Invalid denomination");
        }
        if (!['', 'X', 'XX'].includes(this.risk)) {
            throw new Error("Invalid risk level");
        }
        if (this.declarer && !['N', 'E', 'S', 'W'].includes(this.declarer)) {
            throw new Error("Invalid declarer");
        }
    }

    declarerSide() {
        if (!this.declarer) {
            return null;
        }
        return ['N', 'S'].includes(this.declarer) ? 'NS' : 'EW';
    }

    isVulnerable() {
        if (!this.vul || !this.declarerSide()) {
            return false;
        }
        return (this.vul === 'All') || (this.vul === this.declarerSide());
    }

    pbnScore() {
        const [side, pts] = this.score();
        if (side === null) {
            return "NS 0";
        }
        const nsPts = side === 'NS' ? pts : -pts;
        return `NS ${nsPts}`;
    }

    score() {
        if (this.level === 0 || !this.declarer) {
            return [null, 0];
        }

        const vul = this.isVulnerable();
        const tricksNeeded = 6 + this.level;
        const overUnder = this.made - tricksNeeded;

        if (overUnder >= 0) {
            // Made the contract
            let trickPts = 0;
            if (this.denom === 'NT') {
                trickPts = 40 + 30 * (this.level - 1);
            } else {
                trickPts = ScoreCalculator.TRICK_SCORE[this.denom] * this.level;
            }

            let mult = 1;
            if (this.risk === 'X') {
                trickPts *= 2;
                mult = 2;
            } else if (this.risk === 'XX') {
                trickPts *= 4;
                mult = 4;
            }

            let total = trickPts;

            // Double/redouble bonus
            if (mult > 1) {
                total += 50 * mult;
            }

            // Game/part-game bonus
            if (trickPts >= 100) {
                total += vul ? 500 : 300;
            } else {
                total += 50;
            }

            // Slam bonuses
            if (this.level === 6) {  // Small slam
                total += vul ? 750 : 500;
            } else if (this.level === 7) {  // Grand slam
                total += vul ? 1500 : 1000;
            }

            // Overtricks
            if (overUnder > 0) {
                if (this.risk === '') {
                    const ovpt = this.denom !== 'NT' ? ScoreCalculator.TRICK_SCORE[this.denom] : 30;
                    total += ovpt * overUnder;
                } else {
                    let ovVal = vul ? 200 : 100;
                    if (this.risk === 'XX') {
                        ovVal *= 2;
                    }
                    total += ovVal * overUnder;
                }
            }

            return [this.declarerSide(), total];
        } else {
            // Failed the contract
            const down = -overUnder;
            let penalty = 0;
            
            if (this.risk === '') {
                penalty = (vul ? 100 : 50) * down;
            } else {
                // Doubled penalties
                const steps = vul ? [200, 300, 300] : [100, 200, 200];
                
                for (let i = 0; i < down; i++) {
                    if (i < steps.length) {
                        penalty += steps[i];
                    } else {
                        penalty += 300;
                    }
                }
                
                if (this.risk === 'XX') {
                    penalty *= 2;
                }
            }

            const defenders = this.declarerSide() === 'NS' ? 'EW' : 'NS';
            return [defenders, penalty];
        }
    }
}

class Auction {
    static DENOMINATIONS = ['C', 'D', 'H', 'S', 'NT'];
    static LEVELS = [1, 2, 3, 4, 5, 6, 7];
    static VALID_PLAYERS = ['N', 'E', 'S', 'W'];

    constructor(dealer = 'N') {
        if (!Auction.VALID_PLAYERS.includes(dealer)) {
            throw new Error("Invalid dealer");
        }
        this.calls = [];
        this.lastBidIdx = null;
        this.dealer = dealer;
    }

    currentPlayer() {
        if (this.calls.length === 0) {
            return this.dealer;
        }
        
        const dealerIdx = Auction.VALID_PLAYERS.indexOf(this.dealer);
        const callCount = this.calls.length;
        const currentIdx = (dealerIdx + callCount) % 4;
        return Auction.VALID_PLAYERS[currentIdx];
    }

    static _bidValue(bidStr) {
        if (!bidStr || bidStr.length < 2) {
            return -1;
        }
        try {
            const level = parseInt(bidStr[0]);
            const denom = bidStr.slice(1);
            if (!Auction.LEVELS.includes(level) || !Auction.DENOMINATIONS.includes(denom)) {
                return -1;
            }
            const denomIndex = Auction.DENOMINATIONS.indexOf(denom);
            return (level - 1) * Auction.DENOMINATIONS.length + denomIndex;
        } catch (error) {
            return -1;
        }
    }

    isValidCall(player, call) {
        // Validate player
        if (!Auction.VALID_PLAYERS.includes(player)) {
            return false;
        }
            
        // Check if it's this player's turn
        if (player !== this.currentPlayer()) {
            return false;
        }
            
        // Validate call format
        if (typeof call !== 'string') {
            return false;
        }

        if (call === 'Pass') {
            return true;
        }

        if (call === 'X') {
            // Find the last non-pass call
            let lastNonPass = null;
            for (let i = this.calls.length - 1; i >= 0; i--) {
                if (this.calls[i].call !== 'Pass') {
                    lastNonPass = this.calls[i];
                    break;
                }
            }
            
            if (!lastNonPass) {
                return false;
            }

            // Must be a bid (not X or XX)
            if (['X', 'XX'].includes(lastNonPass.call)) {
                return false;
            }
                
            // Can't double your own side's bid
            const doublerSide = new Set(['N', 'S'].includes(player) ? ['N', 'S'] : ['E', 'W']);
            const bidderSide = new Set(['N', 'S'].includes(lastNonPass.player) ? ['N', 'S'] : ['E', 'W']);
            
            return ![...doublerSide].some(x => bidderSide.has(x));
        }

        if (call === 'XX') {
            // Find the last non-pass call
            let lastNonPass = null;
            for (let i = this.calls.length - 1; i >= 0; i--) {
                if (this.calls[i].call !== 'Pass') {
                    lastNonPass = this.calls[i];
                    break;
                }
            }
            
            if (!lastNonPass || lastNonPass.call !== 'X') {
                return false;
            }

            // Can redouble your own side's doubled bid
            const redoublerSide = new Set(['N', 'S'].includes(player) ? ['N', 'S'] : ['E', 'W']);
            const doublerSide = new Set(['N', 'S'].includes(lastNonPass.player) ? ['N', 'S'] : ['E', 'W']);
            
            return ![...redoublerSide].some(x => doublerSide.has(x));
        }

        // Validate bid format and level
        const bidValue = Auction._bidValue(call);
        if (bidValue === -1) {
            return false;
        }
            
        // Must be higher than last bid
        if (this.lastBidIdx !== null) {
            const lastBid = this.calls[this.lastBidIdx].call;
            const lastValue = Auction._bidValue(lastBid);
            if (bidValue <= lastValue) {
                return false;
            }
        }
                
        return true;
    }

    addCall(player, call) {
        if (!this.isValidCall(player, call)) {
            throw new Error(`Illegal call ${call} by ${player}`);
        }

        this.calls.push({ player, call });
        
        // Update last bid index if this is a bid
        if (!['Pass', 'X', 'XX'].includes(call)) {
            this.lastBidIdx = this.calls.length - 1;
        }

        return this.isFinished();
    }

    isFinished() {
        // Need at least 4 calls to finish
        if (this.calls.length < 4) {
            return false;
        }
            
        // All pass out (4 passes in a row from the start)
        if (this.lastBidIdx === null) {
            // Check if we have exactly 4 passes or more
            if (this.calls.length >= 4 && this.calls.slice(0, 4).every(c => c.call === 'Pass')) {
                return true;
            }
            return false;
        }

        // Three passes after the last bid
        const callsAfterBid = this.calls.slice(this.lastBidIdx + 1);
        if (callsAfterBid.length >= 3) {
            return callsAfterBid.slice(-3).every(c => c.call === 'Pass');
        }

        return false;
    }

    contract() {
        if (!this.isFinished()) {
            throw new Error("Auction not finished yet");
        }

        // All pass - no contract
        if (this.lastBidIdx === null) {
            return { level: 0, denomination: 'Pass', risk: '' };
        }

        const lastBid = this.calls[this.lastBidIdx];
        const level = parseInt(lastBid.call[0]);
        const denom = lastBid.call.slice(1);
        
        // Check for doubles/redoubles after the last bid
        const callsAfter = this.calls.slice(this.lastBidIdx + 1);
        let risk = '';
        for (const call of callsAfter) {
            if (call.call === 'X') {
                risk = 'X';
            } else if (call.call === 'XX') {
                risk = 'XX';
            }
        }

        return { level, denomination: denom, risk };
    }

    declarer() {
        if (!this.isFinished()) {
            throw new Error("Auction not finished yet");
        }

        const contract = this.contract();
        if (contract.level === 0) {
            return null;
        }

        // Find the winning side
        const lastBid = this.calls[this.lastBidIdx];
        const winningSide = new Set(['N', 'S'].includes(lastBid.player) ? ['N', 'S'] : ['E', 'W']);
        const trumpSuit = contract.denomination;

        // Find the first player from the winning side to bid this trump suit
        for (const call of this.calls) {
            if (['Pass', 'X', 'XX'].includes(call.call)) {
                continue;
            }
                
            const bidSuit = call.call.slice(1);
            if (bidSuit === trumpSuit && winningSide.has(call.player)) {
                return call.player;
            }
        }

        return null;
    }
}

class Trick {
    static RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A'];
    static SEATS = ['N', 'E', 'S', 'W'];

    constructor(trump = null, leader = null) {
        if (leader && !Trick.SEATS.includes(leader)) {
            throw new Error("Invalid leader");
        }
        if (trump && !['C', 'D', 'H', 'S'].includes(trump)) {
            throw new Error("Invalid trump suit");
        }
            
        this.trump = trump;
        this.leader = leader;
        this.cards = [];
    }

    nextPlayer() {
        if (!this.leader) {
            throw new Error("No leader set for trick");
        }
        const idx = Trick.SEATS.indexOf(this.leader);
        return Trick.SEATS[(idx + this.cards.length) % 4];
    }

    addCard(player, card, hands) {
        // Validate inputs
        if (!Trick.SEATS.includes(player)) {
            throw new Error(`Invalid player: ${player}`);
        }
        if (typeof card !== 'string' || card.length !== 2) {
            throw new Error(`Invalid card format: ${card}`);
        }
        if (!['C', 'D', 'H', 'S'].includes(card[0]) || !Trick.RANKS.includes(card[1])) {
            throw new Error(`Invalid card: ${card}`);
        }
        if (!(player in hands)) {
            throw new Error(`No hand found for player ${player}`);
        }
        if (!Array.isArray(hands[player])) {
            throw new Error(`Invalid hand format for player ${player}`);
        }

        const expected = this.nextPlayer();
        if (player !== expected) {
            throw new Error(`It's ${expected}'s turn, not ${player}`);
        }

        if (!hands[player].includes(card)) {
            throw new Error(`Player ${player} does not have ${card}`);
        }

        // Check suit following
        const suit = card[0];
        if (this.cards.length > 0) {
            const leadSuit = this.cards[0].card[0];
            const playerHasLeadSuit = hands[player].some(c => c[0] === leadSuit);
            if (playerHasLeadSuit && suit !== leadSuit) {
                throw new Error(`Must follow ${leadSuit} suit`);
            }
        }

        const cardIndex = hands[player].indexOf(card);
        hands[player].splice(cardIndex, 1);
        this.cards.push({ player, card });
        return this.cards.length === 4;
    }

    winner() {
        if (this.cards.length !== 4) {
            throw new Error("Trick not complete");
        }
            
        const leadSuit = this.cards[0].card[0];

        const cardScore = (entry) => {
            const suit = entry.card[0];
            const rank = entry.card[1];
            let rankValue;
            try {
                rankValue = Trick.RANKS.indexOf(rank);
            } catch (error) {
                rankValue = 0;
            }
                
            if (this.trump && suit === this.trump) {
                return [2, rankValue];  // Trump cards
            } else if (suit === leadSuit) {
                return [1, rankValue];  // Lead suit
            } else {
                return [0, rankValue];  // Other suits
            }
        };

        let winnerEntry = this.cards[0];
        let bestScore = cardScore(winnerEntry);
        
        for (let i = 1; i < this.cards.length; i++) {
            const score = cardScore(this.cards[i]);
            if (score[0] > bestScore[0] || (score[0] === bestScore[0] && score[1] > bestScore[1])) {
                winnerEntry = this.cards[i];
                bestScore = score;
            }
        }
        
        return winnerEntry.player;
    }
}

class Bridge {
    static SUITS = ['C', 'D', 'H', 'S'];
    static RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A'];
    static SEATS = ['N', 'E', 'S', 'W'];
    static VALID_VULNERABILITY = ['None', 'NS', 'EW', 'All'];

    constructor(actions = null) {
        this.cards = [];
        for (const s of Bridge.SUITS) {
            for (const r of Bridge.RANKS) {
                this.cards.push(s + r);
            }
        }
        
        this.actions = actions || [];
        this.hands = { 'N': [], 'E': [], 'S': [], 'W': [] };
        this.dealer = null;
        this.gameIndex = 0;
        this.currentPhase = 'Setup';
        this.vulnerable = null;
        this.currentTrick = null;
        this.auction = null;
        
        // Game history
        this.dealers = [];
        this.vulnerables = [];
        this.deals = [];
        this.auctions = [];
        this.contracts = [];
        this.declarers = [];
        this.tricks = [];
        this.results = [];
        this.scores = [];

        // Initialize with default actions if none provided
        if (this.actions.length === 0) {
            this.actions = [
                { name: 'Vulnerable', value: 'None' },
                { name: 'Dealer', value: Bridge.SEATS[Math.floor(Math.random() * Bridge.SEATS.length)] },
                this.generateDeal()
            ];
        }
            
        // Process initial actions
        for (const action of this.actions) {
            this.simulate(action);
        }
    }

    generateDeal() {
        // Shuffle cards using Fisher-Yates algorithm
        const shuffledCards = [...this.cards];
        for (let i = shuffledCards.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffledCards[i], shuffledCards[j]] = [shuffledCards[j], shuffledCards[i]];
        }
        
        const dealtCards = [];
        
        // Deal 13 cards to each player
        const dealOrder = ['N', 'W', 'S', 'E'];  // Standard dealing order
        for (let i = 0; i < dealOrder.length; i++) {
            const seat = dealOrder[i];
            const startIdx = i * 13;
            const endIdx = startIdx + 13;
            for (let j = startIdx; j < endIdx; j++) {
                const card = shuffledCards[j];
                dealtCards.push({
                    seat: seat,
                    suit: card[0],
                    rank: card[1]
                });
            }
        }
                
        return { name: 'Deal', cards: dealtCards };
    }

    validateAction(action) {
        if (typeof action !== 'object' || action === null) {
            throw new Error("Action must be an object");
        }
        if (!('name' in action)) {
            throw new Error("Action must have a 'name' field");
        }
        if (!['Auction', 'Deal', 'Dealer', 'Play', 'Vulnerable'].includes(action.name)) {
            throw new Error(`Invalid action name: ${action.name}`);
        }
    }

    simulate(action) {
        try {
            this.validateAction(action);
            
            if (action.name === 'Auction') {
                this.handleAuctionAction(action);
            } else if (action.name === 'Deal') {
                this.handleDealAction(action);
            } else if (action.name === 'Dealer') {
                this.handleDealerAction(action);
            } else if (action.name === 'Play') {
                this.handlePlayAction(action);
            } else if (action.name === 'Vulnerable') {
                this.handleVulnerableAction(action);
            }
                
        } catch (error) {
            console.error(`Error during simulation of ${JSON.stringify(action)}: ${error.message}`);
        }
    }

    handleAuctionAction(action) {
        if (!('player' in action) || !('value' in action)) {
            throw new Error("Auction action must have 'player' and 'value' fields");
        }
            
        if (!['Setup', 'Auction'].includes(this.currentPhase)) {
            throw new Error(`Cannot auction in phase: ${this.currentPhase}`);
        }
            
        if (this.currentPhase === 'Setup') {
            if (!this.dealer) {
                throw new Error("Dealer must be set before auction");
            }
            this.currentPhase = 'Auction';
            this.auction = new Auction(this.dealer);
        }

        const player = action.player;
        const call = action.value;
        
        if (!Bridge.SEATS.includes(player)) {
            throw new Error(`Invalid player: ${player}`);
        }
        if (!VALID_AUCTION_ACTIONS.has(call)) {
            throw new Error(`Invalid auction call: ${call}`);
        }

        const finished = this.auction.addCall(player, call);
        
        if (finished) {
            // Store auction results
            this.auctions.push(this.auction.calls.map(c => c.call));
            const contract = this.auction.contract();
            this.contracts.push(contract);
            const declarer = this.auction.declarer();
            this.declarers.push(declarer);
            
            // Start play phase if there's a contract
            if (contract.level > 0 && declarer) {
                this.currentPhase = 'Play';
                const declIdx = Bridge.SEATS.indexOf(declarer);
                this.leader = Bridge.SEATS[(declIdx + 1) % 4];  // Left of declarer leads
                const trump = contract.denomination !== 'NT' ? contract.denomination : null;
                this.currentTrick = new Trick(trump, this.leader);
                this.tricks = [this.currentTrick];
                this.results.push(0);  // Tricks made by declaring side
            } else {
                // All pass - game over
                this.currentPhase = 'Finished';
                this.scores.push("NS 0");
            }
        }
    }

    handleDealAction(action) {
        if (!('cards' in action)) {
            throw new Error("Deal action must have 'cards' field");
        }
            
        if (this.currentPhase !== 'Setup') {
            throw new Error("Can only deal in setup phase");
        }

        const cards = action.cards;
        if (!Array.isArray(cards) || cards.length !== 52) {
            throw new Error("Deal must contain exactly 52 cards");
        }

        // Clear existing hands
        for (const seat of Bridge.SEATS) {
            this.hands[seat] = [];
        }

        // Distribute cards
        const seatCounts = { 'N': 0, 'E': 0, 'S': 0, 'W': 0 };
        const usedCards = new Set();
        
        for (const cardInfo of cards) {
            if (typeof cardInfo !== 'object' || cardInfo === null) {
                throw new Error("Each card must be an object");
            }
            if (!('seat' in cardInfo) || !('suit' in cardInfo) || !('rank' in cardInfo)) {
                throw new Error("Card must have 'seat', 'suit', and 'rank' fields");
            }
                
            const seat = cardInfo.seat;
            const suit = cardInfo.suit;
            const rank = cardInfo.rank;
            
            if (!Bridge.SEATS.includes(seat)) {
                throw new Error(`Invalid seat: ${seat}`);
            }
            if (!Bridge.SUITS.includes(suit)) {
                throw new Error(`Invalid suit: ${suit}`);
            }
            if (!Bridge.RANKS.includes(rank)) {
                throw new Error(`Invalid rank: ${rank}`);
            }
                
            const card = suit + rank;
            if (usedCards.has(card)) {
                throw new Error(`Duplicate card: ${card}`);
            }
            usedCards.add(card);
                
            this.hands[seat].push(card);
            seatCounts[seat] += 1;
        }

        // Verify each player has exactly 13 cards
        for (const [seat, count] of Object.entries(seatCounts)) {
            if (count !== 13) {
                throw new Error(`Player ${seat} has ${count} cards, should have 13`);
            }
        }

        this.deals.push(cards);
    }

    handleDealerAction(action) {
        if (!('value' in action)) {
            throw new Error("Dealer action must have 'value' field");
        }
            
        const dealer = action.value;
        if (!Bridge.SEATS.includes(dealer)) {
            throw new Error(`Invalid dealer: ${dealer}`);
        }
            
        this.dealer = dealer;
        this.dealers.push(dealer);
    }

    handlePlayAction(action) {
        if (this.currentPhase !== 'Play') {
            throw new Error("Can only play cards in play phase");
        }
            
        if (!('player' in action) || !('value' in action)) {
            throw new Error("Play action must have 'player' and 'value' fields");
        }

        if (action.value === '*') {  // Skip/dummy action
            return;
        }

        const player = action.player;
        const card = action.value;
        
        if (!Bridge.SEATS.includes(player)) {
            throw new Error(`Invalid player: ${player}`);
        }

        const trickDone = this.currentTrick.addCard(player, card, this.hands);

        if (trickDone) {
            const winner = this.currentTrick.winner();
            this.leader = winner;
            
            // Update tricks won by declaring side
            const declaringSide = new Set(['N', 'S'].includes(this.declarers[this.declarers.length - 1]) ? ['N', 'S'] : ['E', 'W']);
            if (declaringSide.has(winner)) {
                this.results[this.results.length - 1] += 1;
            }

            // Check if this was the last trick
            const completedTricks = this.tricks.filter(t => t.cards.length === 4).length;
            if (completedTricks === 13) {
                // Calculate final score
                const contract = this.contracts[this.contracts.length - 1];
                const declarer = this.declarers[this.declarers.length - 1];
                const made = this.results[this.results.length - 1];
                
                if (contract.level > 0) {
                    const sc = new ScoreCalculator(contract, declarer, made, this.vulnerable);
                    this.scores.push(sc.pbnScore());
                } else {
                    this.scores.push("NS 0");
                }
                    
                this.currentPhase = 'Finished';
            } else {
                // Start next trick
                const trump = this.contracts[this.contracts.length - 1].denomination !== 'NT' 
                    ? this.contracts[this.contracts.length - 1].denomination 
                    : null;
                this.currentTrick = new Trick(trump, this.leader);
                this.tricks.push(this.currentTrick);
            }
        }
    }

    handleVulnerableAction(action) {
        if (!('value' in action)) {
            throw new Error("Vulnerable action must have 'value' field");
        }
            
        const vuln = action.value;
        if (!Bridge.VALID_VULNERABILITY.includes(vuln)) {
            throw new Error(`Invalid vulnerability: ${vuln}`);
        }
            
        this.vulnerable = vuln;
        this.vulnerables.push(vuln);
    }

    getState() {
        const sortedHands = {};
        for (const [k, v] of Object.entries(this.hands)) {
            sortedHands[k] = [...v].sort();
        }
        
        return {
            phase: this.currentPhase,
            dealer: this.dealer,
            vulnerable: this.vulnerable,
            hands: sortedHands,
            auctionCalls: this.auction ? this.auction.calls.map(c => c.call) : [],
            currentPlayer: this.auction && this.currentPhase === 'Auction' ? this.auction.currentPlayer() : null,
            contract: this.contracts.length > 0 ? this.contracts[this.contracts.length - 1] : null,
            declarer: this.declarers.length > 0 ? this.declarers[this.declarers.length - 1] : null,
            tricksMade: this.results.length > 0 ? this.results[this.results.length - 1] : null,
            scores: this.scores
        };
    }
}

// Export for use in other modules (if using modules)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        DENOMS,
        BIDS,
        VALID_AUCTION_ACTIONS,
        ScoreCalculator,
        Auction,
        Trick,
        Bridge
    };
}

// For browser usage
if (typeof window !== 'undefined') {
    window.BridgeGame = {
        DENOMS,
        BIDS,
        VALID_AUCTION_ACTIONS,
        ScoreCalculator,
        Auction,
        Trick,
        Bridge
    };
}