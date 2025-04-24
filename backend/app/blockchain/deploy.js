const hre = require("hardhat");

async function main() {
  const TradeSimulator = await hre.ethers.getContractFactory("TradeSimulator");
  const contract = await TradeSimulator.deploy();

  await contract.deployed();
  console.log(`✅ Contract deployed at: ${contract.address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
