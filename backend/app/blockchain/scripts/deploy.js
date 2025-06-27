const hre = require("hardhat");

async function main() {
    const [deployer] = await hre.ethers.getSigners();
    const NFT = await hre.ethers.getContractFactory("UserAchievementNFT");
    const nft = await NFT.deploy(deployer.address); //adresa ownerului
    await nft.waitForDeployment();

    console.log(` NFT Contract deployed at: ${await nft.getAddress()}`);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});