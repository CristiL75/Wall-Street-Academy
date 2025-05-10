// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract UserAchievementNFT is ERC721URIStorage, Ownable {
    uint256 public nextTokenId;

    constructor(address initialOwner) ERC721("WallStreetAchievements", "WSA") Ownable(initialOwner) {}

    function mintNFT(address to, string memory tokenURI) public onlyOwner {
        uint256 tokenId = nextTokenId;
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, tokenURI);
        nextTokenId++;
    }
}
