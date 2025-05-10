async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying NFT contract with account:", deployer.address);

  const NFT = await ethers.getContractFactory("UserAchievementNFT");
  const nft = await NFT.deploy(); // fără argument

  await nft.waitForDeployment();

  console.log("✅ NFT Contract deployed at:", await nft.getAddress());
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
