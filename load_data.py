
import requests
import json
import pandas as pd
import math
import numpy as np


# function to use requests.post to make an API call to the subgraph url
def run_query(q):

    # endpoint where you are making the request
    request = requests.post('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'
                            '',json={'query': q})
    if request.status_code == 200:
        return request
    else:
        raise Exception('Query failed. return code is {}.      {}'.format(request.status_code, query))
        
        


def get_token_id(symbol):
    
    # default should be first:10, in case there are more than 1 coins with the same symbol
    query_ = """ 
    {{
      tokens(first:1, where:{{symbol: "{}"}}) {{
        id
        symbol
        name
      }}
    }}""".format(symbol)
    
    # run query
    query_result_ = run_query(query_)
    json_data_ = json.loads(query_result_.text)
    
    print(' ')
    print('get_token_id: {}'.format(symbol))
    print(json_data_)
    
    # make sure only return 1 object
    if len(json_data_['data']['tokens']) == 1:
        token_id_ = json_data_['data']['tokens'][0]['id']
        return token_id_
        
    else:
        print(json_data_['data'])
        raise Exception('Returned number of token_ids != 1')

        



def get_pool_id(token0_id, token1_id, feeTier):
    query_ = """
    {{
      pools(first: 10, 
        where:{{token0: "{}",
        token1: "{}",
        feeTier:"{}" }}) 
      {{
        id
        token0{{symbol}}
        token1{{symbol}}
        feeTier
      }}
    }}""".format(token0_id, token1_id, feeTier)
    
    
    # run query
    query_result_ = run_query(query_)
    json_data_ = json.loads(query_result_.text)
    
    print('\n get_pool_id for feeTier: {}'.format(feeTier))
    print(json_data_)
    
    # make sure there is only 1 pool that matches exactly
    if len(json_data_['data']['pools']) == 1:
        pool_id_ = json_data_['data']['pools'][0]['id']
        return pool_id_
    else:
        print(json_data_['data'])
        raise Exception('Returned number of token_ids != 1')

        
    return json_data_





def get_poolHourDatas(pool_id, num_datapoints=3000):
    # input: pool_id
    # num_datapoints (must be multiple of max_request_)
    
    max_request_ = 1000
    quotient_ = math.floor(num_datapoints/max_request_)
            
    query_base_ = '''
    {{
      poolHourDatas(first:{},
      skip: {},
        where:{{ pool: "{}" }},
      orderBy:periodStartUnix,
      orderDirection: desc) 
      {{
        periodStartUnix
        pool{{
            token0{{
                symbol
            }}
            token1{{
                symbol
            }}
        }}
        liquidity
        sqrtPrice
        token0Price
        token1Price
        tick
        feeGrowthGlobal0X128
        feeGrowthGlobal1X128
        tvlUSD
        volumeToken0
        volumeToken1
        volumeUSD
        feesUSD
        txCount
        open
        high
        low
        close
      }}
    }}'''
    
    poolDayDatas_array_ = []
    
    # query loop
    for i in range(quotient_):
        q_first_ = max_request_
        q_next_ = i*max_request_
        query_ = query_base_.format(q_first_, q_next_, pool_id)
        query_result_ = run_query(query_)
        json_data_ = json.loads(query_result_.text)
        try:
            poolDayDatas_array_ += json_data_['data']['poolHourDatas']
        except Exception:
            pass
    
    print(' ')
    print('\n Queried poolHourDatas, total of {} datapoints'.format(str(len(poolDayDatas_array_))))

    
    # array to dataframe
    df_ = pd.json_normalize(poolDayDatas_array_)
    
    return df_





def get_swaps(pool_id, time_start='1627369200', time_end='1623772800', num_datapoints=6000):
    # input: pool_id
    # num_datapoints (must be multiple of max_request_)
    
    max_request_ = 1000
    quotient_ = math.floor(num_datapoints/max_request_)
#     remainder_ = num_datapoints%max_request_
           
    query_base_ = '''
    {{
      swaps(first:{}, skip: {},
            where:{{ pool: "{}",
            timestamp_lt: "{}",
            timestamp_gt: "{}"}},
          orderBy:timestamp,
          orderDirection: desc){{
        transaction {{
          blockNumber
          timestamp
          gasUsed
          gasPrice
        }}
        id
        timestamp
        tick
        amount0
        amount1
        amountUSD
        sqrtPriceX96
      }}
    }}'''
    
    swap_arrays_ = []
    
    # query loop
    for i in range(quotient_):
        q_first_ = max_request_
        q_next_ = i*max_request_
        query_ = query_base_.format(q_first_, q_next_, pool_id, time_start, time_end)
        query_result_ = run_query(query_)
        json_data_ = json.loads(query_result_.text)
        
        try:
            swap_arrays_ += json_data_['data']['swaps']
            
        except Exception:
            pass
        
    print('Queried Swaps, total of {} datapoints'.format(str(len(swap_arrays_))))
    print(' ')
    df_ = pd.json_normalize(swap_arrays_)
    
    # next time start, if at the edge, then we keep looping and skipping
    if len(swap_arrays_) != 0:
        # last element of timestamp, add 1 so next iterations still includes it
        next_time_start_ = str( int(df_['timestamp'][df_.index[-1]]) + 1 ) 
    else:
        next_time_start_ = time_start
            
            
    return df_, next_time_start_


# get_swap can only request 6000 datapoints at the time. this is to loop get_swap to get more data
def get_swaps_loop(pool_id, time_start='1627369200', time_end='1623772800'): # ,  num_datapoints= 150000
    
    print('time_start: {}, time_end: {}'.format(time_start, time_end))
    
    max_num_query = 6000
#     num_iterations = math.floor(num_datapoints/max_num_query) + 3 # add 3 just in case
    
    next_time_start_ = time_start
    count = 0 # counting number of times that data returns is less than maximum, meaning reaching the end
#     for i in range(num_iterations):
    first_time = True
    while(count<10):
        print('next_time_start_: {}'.format(next_time_start_))
        df_, next_time_start_ = get_swaps(pool_id, next_time_start_, time_end, num_datapoints=max_num_query)
        
        if first_time == True:
            df_all_ = df_
            first_time = False
        else:
            df_all_ = df_all_.append(df_)
            
        if df_.shape[0] < 6000:
            count += 1
    
    # drop duplicates, reset index
    df_all_ = df_all_.drop_duplicates(subset=['id'])
    df_all_ = df_all_.reset_index(drop=True)
    print('Total swaps data = {}'.format(df_all_.shape[0]))
    
    return df_all_




def merge_poolHourData_swaps_all(df_poolHourDatas, df_swaps_all):
    
    # Match timestamp with hour period, and assign to df_swaps_all['periodStartUnix']
    def compute_periodStartUnix(row_):
        return row_['timestamp'] - (row_['timestamp'] % 3600)
    def compute_periodEndUnix(row_):
        return row_['periodStartUnix'] + 3600

    df_swaps_all['timestamp'] = df_swaps_all['timestamp'].astype(int)    
    df_swaps_all['periodStartUnix'] = df_swaps_all.apply(lambda row: compute_periodStartUnix(row), axis=1)                       
    df_swaps_all['periodEndUnix'] = df_swaps_all.apply(lambda row: compute_periodEndUnix(row), axis=1)                       

    df_swaps_all['periodStartUnix'] = df_swaps_all['periodStartUnix'].astype(int)        
    df_swaps_all['periodEndUnix'] = df_swaps_all['periodEndUnix'].astype(int)
    
    # Create swaps_txCount to compare with txCount in poolHourDatas to check integrity
    df_swaps_all['swaps_txCount'] = 1

    df_swaps_all['amount0'] = df_swaps_all['amount0'].astype(float)
    df_swaps_all['amount1'] = df_swaps_all['amount1'].astype(float)

    df_swaps_all['amount0_p'] = df_swaps_all['amount0'].apply(lambda x: x if x >= 0 else 0)
    df_swaps_all['amount0_n'] = df_swaps_all['amount0'].apply(lambda x: x if x < 0 else 0)
    df_swaps_all['amount1_p'] = df_swaps_all['amount1'].apply(lambda x: x if x >= 0 else 0)
    df_swaps_all['amount1_n'] = df_swaps_all['amount1'].apply(lambda x: x if x < 0 else 0)
    
    
    # Groupby->Sum based on periodStartUnix, specify columns to sum at GROUPBY_COLS
    GROUPBY_COLS = ['periodStartUnix','amount0', 'amount1', 
                    'amount0_p', 'amount0_n', 'amount1_p', 'amount1_n',
                    'amountUSD', 'swaps_txCount']
    df_swaps_to_merge = df_swaps_all[GROUPBY_COLS]
    df_swaps_to_merge = df_swaps_to_merge.astype({'periodStartUnix': 'int',
                                                 'amount0':'float','amount1':'float', 
                                                  'amount0_p':'float','amount0_n':'float',
                                                  'amount1_p':'float', 'amount1_n':'float',
                                                  'amountUSD':'float', 'swaps_txCount':'int'})

    df_swaps_to_merge = df_swaps_to_merge.groupby(by=['periodStartUnix']).sum()

    # Merge df_swaps_all (groupby) with df_poolHourDatas
    df_poolHourDatas['periodStartUnix'] = df_poolHourDatas['periodStartUnix'].astype(int)
    df_merged = df_poolHourDatas.merge(df_swaps_to_merge, how='left', on='periodStartUnix')
    df_merged['txCount'] = df_merged['txCount'].astype(int)
    
    return df_merged




def get_data(token0, token1, feeTier):
    
    # Indicate Tokens and FeeTier
    token0_id = get_token_id(token0)
    token1_id = get_token_id(token1)
    pool_id = get_pool_id(token0_id, token1_id, feeTier)

    # Get poolHourDatas
    df_poolHourDatas = get_poolHourDatas(pool_id, num_datapoints=10000)

    # Get Swap Datas within the poolHourDatas timeframe
    time_start = df_poolHourDatas['periodStartUnix'][0]
    time_end = df_poolHourDatas['periodStartUnix'][df_poolHourDatas.index[-1]]
    
    # Get Swaps data
    df_swaps_all = get_swaps_loop(pool_id, time_start, time_end) # ,  num_datapoints= 150000
    
    # Saving settings
    SETTINGS = '{}-{}-{}-timestamp-{}-{}.csv'.format(token0, token1, feeTier, time_start, time_end)
    df_swaps_all.to_csv('../data/df_swaps_all_'+SETTINGS)
    df_poolHourDatas.to_csv('../data/df_poolHourDatas_'+SETTINGS)
    
    # Merge data
    df_merged = merge_poolHourData_swaps_all(df_poolHourDatas, df_swaps_all)
    
    df_merged.to_csv('../data/df_merged_tmp_'+SETTINGS)
    
    return df_merged
















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
