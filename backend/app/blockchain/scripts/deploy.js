const hre = require("hardhat");

async function main() {
    const NFT = await hre.ethers.getContractFactory("UserAchievementNFT");
    const nft = await NFT.deploy();
    await nft.waitForDeployment();

    console.log(` NFT Contract deployed at: ${await nft.getAddress()}`);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
