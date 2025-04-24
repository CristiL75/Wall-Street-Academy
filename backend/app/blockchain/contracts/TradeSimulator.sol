// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract TradeSimulator {
    struct Trade {
        string symbol;
        uint256 amount;
        bool isBuy;
        uint256 timestamp;
    }

    mapping(address => Trade[]) public userTrades;

    function registerTrade(address user, string memory symbol, uint256 amount, bool isBuy) public {
        userTrades[user].push(Trade(symbol, amount, isBuy, block.timestamp));
    }

    function getUserTrades(address user) public view returns (Trade[] memory) {
        return userTrades[user];
    }
}
