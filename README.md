# uniswapv3_backtest









# #### Data we need:
# user input:
# - investment amount, trading pair -> amt0, amt1
# - start time and end time
# - time period that you assume fixed swap price, swap volumes or liquidity positions
# - upper and lower price
# - pool_fee_rate

# data from api:
# - cprice of each time period (tick, 1.0001 ** i)
# - L_pool at each time period at specific pool_fee_rate (liquidity?, or simply total X tokens + Y tokens in USD)
# - Swap volume at each time period at specific pool_fee_rate (volumeUSD?)
# - Gas cost to mint at each time period

# --------------------------------------------------------------------------------------------------------------
# #### Fees
# The liquidity amount is calculated from the following numbers that describe a position: 
# - amount of token 0 (amt0), amount of token 1 (amt1), 
# - price (as x token 1's per token 0) at the upper limit of the position (upper), 
# - price at the lower limit of the position (lower) 
# - and the current swap price (cprice). 

# Then liquidity (L_you?) for a position is calculated as follows:

# Case 1: cprice <= lower
# - liquidity = amt0 * (sqrt(upper) * sqrt(lower)) / (sqrt(upper) - sqrt(lower))

# Case 2: lower < cprice <= upper
# - liquidity is the min of the following two calculations:
# - amt0 * (sqrt(upper) * sqrt(cprice)) / (sqrt(upper) - sqrt(cprice))
# - amt1 / (sqrt(cprice) - sqrt(lower))

# Case 3: upper < cprice
# - liquidity = amt1 / (sqrt(upper) - sqrt(lower))

# Resources
# - liquidity can use this code: https://github.com/JNP777/UNI_V3-Liquitidy-amounts-calcs/blob/main/UNI_v3_funcs.py

# Fee is calculated by:
# - Fee income = (L_you/L_pool) * swap volume under fixed time period * pool_fee_rate/100
# - L_you also should be for that specific ticks only, not the whole amount you provided for. Its not linear, its calculated from the 3 cases above
# - Does Case1 and Case3's fee be 0 regardless?


# reference: https://uniswapv3.flipsidecrypto.com/
# - check my numbers with the reference from the website

# ----------------------------------------------------------------------------------------
# #### Impermanent Loss (is this v2 or v3)
# - IL (in %) = (2 sqrt(p) / (p+1) ) - 1
# - where p = r_t1/r_t2
# - and r_t is a price in b at time 1
# - Net $ loss = total asset value in dollars at stake time * IL (in%)

# reference: https://chainbulletin.com/impermanent-loss-explained-with-examples-math/#:~:text=Impermanent%20loss%20is%20the%20difference,is%20equal%20to%20200%20DAI

# --------------------------------------------------------------------------------------------------------------
# #### Other cost

# Gas_costs_mint = 500000 gwei * gas_price at that time (??? double check actual cost)

# ### PNL/APR
# -PNL = Acumulated Fees_accrued (dolar value at generation) - IL - Gas_costs_mint

# -APR = PNL/Initial_capital*(age of the position / year time)

# --------------------------------------------------------------------------------------------------------------






# https://playcode.io/780618/
# import axios from 'axios';

# // Constants ---------------------------------------------------------------
# const x96 = Math.pow(2, 96);
# const x128 = Math.pow(2, 128);
# const exampleNFTid = '28500';
# const graphqlEndpoint =
#   'https://api.thegraph.com/subgraphs/name/benesjan/uniswap-v3-subgraph';
# // Constants End -----------------------------------------------------------

# // Main function -----------------------------------------------------------
# async function getPosition(id) {
#   console.time('Uni Position Query');

#   // The call to the subgraph
#   let positionRes = await axios.post(graphqlEndpoint, {
#     query: positionQuery.replace('%1', id),
#   });

#   // Setting up some variables to keep things shorter & clearer
#   let position = positionRes.data.data.position;
#   let positionLiquidity = position.liquidity;
#   let pool = position.pool;
#   let decimalDifference =
#     parseInt(position.token1.decimals, 10) -
#     parseInt(position.token0.decimals, 10);
#   let [symbol_0, symbol_1] = [position.token0.symbol, position.token1.symbol];

#   // Prices (not decimal adjusted)
#   let priceCurrent = sqrtPriceToPrice(pool.sqrtPrice);
#   let priceUpper = parseFloat(position.tickUpper.price0);
#   let priceLower = parseFloat(position.tickLower.price0);

#   // Square roots of the prices (not decimal adjusted)
#   let priceCurrentSqrt = parseFloat(pool.sqrtPrice) / Math.pow(2, 96);
#   let priceUpperSqrt = Math.sqrt(parseFloat(position.tickUpper.price0));
#   let priceLowerSqrt = Math.sqrt(parseFloat(position.tickLower.price0));

#   // Prices (decimal adjusted)
#   let priceCurrentAdjusted = sqrtPriceToPriceAdjusted(
#     pool.sqrtPrice,
#     decimalDifference
#   );
#   let priceUpperAdjusted =
#     parseFloat(position.tickUpper.price0) / Math.pow(10, decimalDifference);
#   let priceLowerAdjusted =
#     parseFloat(position.tickLower.price0) / Math.pow(10, decimalDifference);

#   // Prices (decimal adjusted and reversed)
#   let priceCurrentAdjustedReversed = 1 / priceCurrentAdjusted;
#   let priceLowerAdjustedReversed = 1 / priceUpperAdjusted;
#   let priceUpperAdjustedReversed = 1 / priceLowerAdjusted;

#   // The amount calculations using positionLiquidity & current, upper and lower priceSqrt
#   let amount_0, amount_1;
#   if (priceCurrent <= priceLower) {
#     amount_0 = positionLiquidity * (1 / priceLowerSqrt - 1 / priceUpperSqrt);
#     amount_1 = 0;
#   } else if (priceCurrent < priceUpper) {
#     amount_0 = positionLiquidity * (1 / priceCurrentSqrt - 1 / priceUpperSqrt);
#     amount_1 = positionLiquidity * (priceCurrentSqrt - priceLowerSqrt);
#   } else {
#     amount_1 = positionLiquidity * (priceUpperSqrt - priceLowerSqrt);
#     amount_0 = 0;
#   }

#   // Decimal adjustment for the amounts
#   let amount_0_Adjusted = amount_0 / Math.pow(10, position.token0.decimals);
#   let amount_1_Adjusted = amount_1 / Math.pow(10, position.token1.decimals);

#   // UNCOLLECTED FEES --------------------------------------------------------------------------------------
#   // Check out the relevant formulas below which are from Uniswap Whitepaper Section 6.3 and 6.4
#   // 𝑓𝑟 =𝑓𝑔−𝑓𝑏(𝑖𝑙)−𝑓𝑎(𝑖𝑢)
#   // 𝑓𝑢 =𝑙·(𝑓𝑟(𝑡1)−𝑓𝑟(𝑡0))

#   // These will be used for both tokens' fee amounts
#   let tickCurrent = parseFloat(position.pool.tick);
#   let tickLower = parseFloat(position.tickLower.tickIdx);
#   let tickUpper = parseFloat(position.tickUpper.tickIdx);

#   // Global fee growth per liquidity '𝑓𝑔' for both token 0 and token 1
#   let feeGrowthGlobal_0 = parseFloat(position.pool.feeGrowthGlobal0X128) / x128;
#   let feeGrowthGlobal_1 = parseFloat(position.pool.feeGrowthGlobal1X128) / x128;

#   // Fee growth outside '𝑓𝑜' of our lower tick for both token 0 and token 1
#   let tickLowerFeeGrowthOutside_0 =
#     parseFloat(position.tickLower.feeGrowthOutside0X128) / x128;
#   let tickLowerFeeGrowthOutside_1 =
#     parseFloat(position.tickLower.feeGrowthOutside1X128) / x128;

#   // Fee growth outside '𝑓𝑜' of our upper tick for both token 0 and token 1
#   let tickUpperFeeGrowthOutside_0 =
#     parseFloat(position.tickUpper.feeGrowthOutside0X128) / x128;
#   let tickUpperFeeGrowthOutside_1 =
#     parseFloat(position.tickUpper.feeGrowthOutside1X128) / x128;
  

#   // These are '𝑓𝑏(𝑖𝑙)' and '𝑓𝑎(𝑖𝑢)' from the formula
#   // for both token 0 and token 1
#   let tickLowerFeeGrowthBelow_0;
#   let tickLowerFeeGrowthBelow_1;
#   let tickUpperFeeGrowthAbove_0;
#   let tickUpperFeeGrowthAbove_1;

#   // These are the calculations for '𝑓𝑎(𝑖)' from the formula
#   // for both token 0 and token 1
#   if (tickCurrent >= tickUpper) {
#     tickUpperFeeGrowthAbove_0 = feeGrowthGlobal_0 - tickUpperFeeGrowthOutside_0;
#     tickUpperFeeGrowthAbove_1 = feeGrowthGlobal_1 - tickUpperFeeGrowthOutside_1;
#   } else {
#     tickUpperFeeGrowthAbove_0 = tickUpperFeeGrowthOutside_0;
#     tickUpperFeeGrowthAbove_1 = tickUpperFeeGrowthOutside_1;
#   }

#   // These are the calculations for '𝑓b(𝑖)' from the formula
#   // for both token 0 and token 1
#   if (tickCurrent >= tickLower) {
#     tickLowerFeeGrowthBelow_0 = tickLowerFeeGrowthOutside_0;
#     tickLowerFeeGrowthBelow_1 = tickLowerFeeGrowthOutside_1;
#   } else {
#     tickLowerFeeGrowthBelow_0 = feeGrowthGlobal_0 - tickLowerFeeGrowthOutside_0;
#     tickLowerFeeGrowthBelow_1 = feeGrowthGlobal_1 - tickLowerFeeGrowthOutside_1;
#   }

#   // Calculations for '𝑓𝑟(𝑡1)' part of the '𝑓𝑢 =𝑙·(𝑓𝑟(𝑡1)−𝑓𝑟(𝑡0))' formula
#   // for both token 0 and token 1
#   let fr_t1_0 =
#     feeGrowthGlobal_0 - tickLowerFeeGrowthBelow_0 - tickUpperFeeGrowthAbove_0;
#   let fr_t1_1 =
#     feeGrowthGlobal_1 - tickLowerFeeGrowthBelow_1 - tickUpperFeeGrowthAbove_1;

#   // '𝑓𝑟(𝑡0)' part of the '𝑓𝑢 =𝑙·(𝑓𝑟(𝑡1)−𝑓𝑟(𝑡0))' formula
#   // for both token 0 and token 1
#   let feeGrowthInsideLast_0 =
#     parseFloat(position.feeGrowthInside0LastX128) / x128;
#   let feeGrowthInsideLast_1 =
#     parseFloat(position.feeGrowthInside1LastX128) / x128;

#   // The final calculations for the '𝑓𝑢 =𝑙·(𝑓𝑟(𝑡1)−𝑓𝑟(𝑡0))' uncollected fees formula
#   // for both token 0 and token 1 since we now know everything that is needed to compute it
#   let uncollectedFees_0 = positionLiquidity * (fr_t1_0 - feeGrowthInsideLast_0);
#   let uncollectedFees_1 = positionLiquidity * (fr_t1_1 - feeGrowthInsideLast_1);

#   // Decimal adjustment to get final results
#   let uncollectedFeesAdjusted_0 =
#     uncollectedFees_0 / Math.pow(10, position.token0.decimals);
#   let uncollectedFeesAdjusted_1 =
#     uncollectedFees_1 / Math.pow(10, position.token1.decimals);
#   // UNCOLLECTED FEES END ----------------------------------------------------------------------------------

#   // Logs of the the results
#   console.table([
#     ['Pair', `${symbol_0}/${symbol_1}`],
#     ['Upper Price', priceUpperAdjusted.toPrecision(5)],
#     ['Current Price', priceCurrentAdjusted.toPrecision(5)],
#     ['Lower Price', priceLowerAdjusted.toPrecision(5)],
#     [`Current Amount ${symbol_0}`, amount_0_Adjusted.toPrecision(5)],
#     [`Current Amount ${symbol_1}`, amount_1_Adjusted.toPrecision(5)],
#     [`Uncollected Fee Amount ${symbol_0}`, uncollectedFeesAdjusted_0.toPrecision(5)],
#     [`Uncollected Fee Amount ${symbol_1}`, uncollectedFeesAdjusted_1.toPrecision(5)],
#     [`Decimals ${symbol_0}`, position.token0.decimals],
#     [`Decimals ${symbol_1}`, position.token1.decimals],
#     ['------------------', '------------------'],
#     ['Upper Price Reversed', priceUpperAdjustedReversed.toPrecision(5)],
#     ['Current Price Reversed', priceCurrentAdjustedReversed.toPrecision(5)],
#     ['Lower Price Reversed', priceLowerAdjustedReversed.toPrecision(5)],
#   ]);
#   console.timeEnd('Uni Position Query');
# }
# // Main Function End --------------------------------------------------------

# // Helper Functions ---------------------------------------------------------
# function sqrtPriceToPriceAdjusted(sqrtPriceX96Prop, decimalDifference) {
#   let sqrtPrice = parseFloat(sqrtPriceX96Prop) / x96;
#   let divideBy = Math.pow(10, decimalDifference);
#   let price = Math.pow(sqrtPrice, 2) / divideBy;

#   return price;
# }

# function sqrtPriceToPrice(sqrtPriceX96Prop) {
#   let sqrtPrice = parseFloat(sqrtPriceX96Prop) / x96;
#   let price = Math.pow(sqrtPrice, 2);
#   return price;
# }
# // Helper Functions End ----------------------------------------------------

# // Subgraph query for the position
# const positionQuery = `
#     query tokenPosition {
#         position(id: "%1"){
#             id
#             token0{
#                 symbol
#                 derivedETH
#                 id
#                 decimals
#             }
#             token1{
#                 symbol
#                 derivedETH
#                 id
#                 decimals
#             }
#             pool{
#                 id
#                 liquidity
#                 sqrtPrice
#                 tick
#                 feeGrowthGlobal0X128
#                 feeGrowthGlobal1X128
#             }
#             liquidity
#             depositedToken0
#             depositedToken1
#             feeGrowthInside0LastX128
#             feeGrowthInside1LastX128
#             tickLower {
#                 tickIdx
#                 price0
#                 price1
#                 feeGrowthOutside0X128
#                 feeGrowthOutside1X128
#             }
#             tickUpper {
#                 tickIdx
#                 price0
#                 price1
#                 feeGrowthOutside0X128
#                 feeGrowthOutside1X128
#             }
#             withdrawnToken0
#             withdrawnToken1
#             collectedFeesToken0
#             collectedFeesToken1
#             transaction{
#                 timestamp
#                 blockNumber
#             }
#         }
#     }
# `;

# getPosition(exampleNFTid);
