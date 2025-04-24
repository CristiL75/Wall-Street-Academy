const hre = require("hardhat");

async function main() {
  const TradeSimulator = await hre.ethers.getContractFactory("TradeSimulator");
  const contract = await TradeSimulator.deploy();

  console.log(`✅ Contract deployed at: ${contract.target}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
