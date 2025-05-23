// helpful link to view pbn: https://www.philallen.co.uk/PBNViewerVersion1_1c.html
const fs = require('fs');
const path = require('path');
// const { Bridge } = require('./bridge');
const { Bridge } = require('./bridgeClaudev2');

const seats = ['N', 'E', 'S', 'W'];
const games = [];

const TARGET = new Set(['Vulnerable', 'Dealer', 'Deal', 'Declarer', 'Contract', 'Result', 'Score', 'Auction', 'Play']);

// all denominations in order
const DENOMS = ['C', 'D', 'H', 'S', 'NT'];

// generate 1C–7NT
const BIDS = [];
for (let level = 1; level <= 7; level++) {
    for (const denom of DENOMS) {
        BIDS.push(`${level}${denom}`);
    }
}

const VALID_AUCTION_ACTIONS = new Set([
    'Pass', 'X', 'XX',  // pass, double, redouble
    ...BIDS             // all valid level+denom bids
]);

// Load in games from parsed pbn file
const inputDir = 'parsed-games';

try {
    const files = fs.readdirSync(inputDir);
    
    for (const filename of files) {
        // Uncomment to filter specific file
        // if (filename !== 'parsed-Esoito01.jsonl') {
        //     continue;
        // }

        if (!filename.endsWith('.jsonl')) {
            continue;
        }

        const filepath = path.join(inputDir, filename);
        const fileGames = [];
        
        try {
            const fileContent = fs.readFileSync(filepath, 'utf8');
            const lines = fileContent.split('\n');
            let currentGame = null;

            for (const line of lines) {
                const trimmedLine = line.trim();
                if (!trimmedLine) {
                    continue;
                }

                try {
                    const obj = JSON.parse(trimmedLine);

                    if (obj.type === 'game') {
                        if (currentGame) {
                            fileGames.push(currentGame);
                        }
                        currentGame = {};
                    } else if (obj.type === 'tag' && currentGame !== null) {
                        const name = obj.name;
                        if (TARGET.has(name)) {
                            currentGame[name] = obj;
                        }
                    }
                } catch (parseError) {
                    console.warn(`Error parsing line in ${filename}:`, parseError.message);
                }
            }

            if (currentGame) {
                fileGames.push(currentGame);
            }
        } catch (fileError) {
            console.error(`Error reading file ${filename}:`, fileError.message);
            continue;
        }
        
        games.push([filename, fileGames]);
    }
} catch (dirError) {
    console.error(`Error reading directory ${inputDir}:`, dirError.message);
    process.exit(1);
}

console.log(`total files loaded: ${games.length}`);

const declarers = [];
const actualDeclarers = [];
const contracts = [];
const actualContracts = [];
const results = [];
const actualResults = [];
const scores = [];
const actualScores = [];

for (const [fileName, fileGames] of games) {
    console.log('filename: ', fileName);
    
    for (let gameIndex = 0; gameIndex < fileGames.length; gameIndex++) {
        const game = fileGames[gameIndex];
        console.log('game', gameIndex);
        
        if (!game.Auction) {
            continue;
        }
        
        const auctionActions = [];
        const auctionTokens = game.Auction.tokens;
        let seatIndex = seats.indexOf(game.Auction.value);
        
        for (const token of auctionTokens) {
            if (!VALID_AUCTION_ACTIONS.has(token)) {
                continue;
            }
            auctionActions.push({
                name: 'Auction',
                player: seats[seatIndex],
                value: token
            });
            seatIndex = (seatIndex + 1) % seats.length;
        }
        
        const actions = [game.Vulnerable, game.Dealer, game.Deal, ...auctionActions];
        const b = new Bridge(actions);

        if (!game.Play) {
            continue;
        }
        
        const playTokens = game.Play.tokens;
        seatIndex = seats.indexOf(game.Play.value);
        let plays = [];
        let tricks = 0;
        
        for (const token of playTokens) {
            const playAction = {
                name: 'Play',
                player: seats[seatIndex],
                value: token
            };
            plays.push(playAction);
            seatIndex = (seatIndex + 1) % seats.length;
            
            if (plays.length === 4) {
                let count = 4;
                while (count) {
                    let i = 0;
                    for (let index = 0; index < plays.length; index++) {
                        const item = plays[index];
                        if (item.player === b.tricks[b.tricks.length - 1].nextPlayer()) {
                            i = index;
                            break;
                        }
                    }
                    b.simulate(plays[i]);
                    count--;
                }
                tricks++;
                plays = [];
            }
        }
        
        if (tricks === 13) {
            results.push(b.results[0]);
            actualResults.push(parseInt(game.Result.value));
            scores.push(b.scores[0]);
            actualScores.push(game.Score.value);
            
            if (b.scores[0] !== game.Score.value) {
                console.log(`mismatch in score for file ${fileName} at game ${gameIndex}`, b.scores[0], game.Score.value);
            }
            if (b.results[0] !== parseInt(game.Result.value)) {
                console.log(`mismatch in result for file ${fileName} at game ${gameIndex}`, b.results[0], parseInt(game.Result.value));
            }
        }

        if (b.declarers[0] !== game.Declarer.value) {
            console.log(`declarers mismatch at game ${gameIndex} in file ${fileName}`);
        }
        declarers.push(b.declarers[0]);
        actualDeclarers.push(game.Declarer.value);
        
        const contract = `${b.contracts[0].level}${b.contracts[0].denomination}${b.contracts[0].risk}`;
        contracts.push(contract);
        actualContracts.push(game.Contract.value);
        
        if (contract !== game.Contract.value) {
            console.log(`contract mismatch at game ${gameIndex} in file ${fileName}`);
        }
    }
}

// Validation loops
for (let i = 0; i < declarers.length; i++) {
    if (declarers[i] !== actualDeclarers[i]) {
        console.log('declarers mismatch at ', i);
    }
}

for (let i = 0; i < contracts.length; i++) {
    if (contracts[i] !== actualContracts[i]) {
        console.log('contracts mismatch at ', i);
    }
}

for (let i = 0; i < results.length; i++) {
    if (results[i] !== actualResults[i]) {
        console.log('results mismatch at ', i);
    }
}

for (let i = 0; i < scores.length; i++) {
    if (scores[i] !== actualScores[i]) {
        console.log('scores mismatch at ', i);
    }
}

console.log(scores.length);
console.log(results.length);
console.log(declarers.length);
console.log(contracts.length);